"""WinRT engine: shows and removes native Windows toasts via PowerShell.

Serializes a payload to a temp JSON file, translates WSL paths to Windows paths
with ``wslpath -w`` and runs ``windows/toast.ps1`` (show) or
``windows/dismiss.ps1`` (remove) through ``powershell.exe``. Passing data via a
file avoids all quoting/escaping issues.

Permission toasts are shown with a per-session ``Tag``/``Group`` so they can be
removed from the Action Center once the request is resolved.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile

from notifire.config import DEFAULT_APP_ID
from notifire.engines.base import NotificationEngine
from notifire.payload import NotifyType, Payload

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TOAST_PS1 = os.path.join(_REPO_ROOT, "windows", "toast.ps1")
_DISMISS_PS1 = os.path.join(_REPO_ROOT, "windows", "dismiss.ps1")
_GROUP = "notifire"
_MAX_LINE = 1000  # safety cap: oversized toast XML fails to show at all


def _cap(line):
    return line if len(line) <= _MAX_LINE else line[: _MAX_LINE - 1].rstrip() + "…"


def _wslpath_w(path):
    """Returns the Windows form of a WSL path via ``wslpath -w``."""
    result = subprocess.run(
        ["wslpath", "-w", path], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _tag(session_id):
    """Returns a short, stable toast tag derived from the session id."""
    return hashlib.sha1((session_id or "default").encode()).hexdigest()[:16]


class WinRtEngine(NotificationEngine):
    def __init__(self, config):
        super().__init__(config)
        opts = (config or {}).get("winrt", {})
        self.app_id = opts.get("app_id") or DEFAULT_APP_ID
        self.sound = bool(opts.get("sound", True))

    def send(self, payload: Payload):
        data = {
            "appId": self.app_id,
            "sound": self.sound,
            "title": payload.title,
            "lines": [_cap(line) for line in payload.display_lines()],
        }
        handle = None
        if payload.type == NotifyType.PERMISSION:
            tag = _tag(payload.session_id)
            data["tag"], data["group"] = tag, _GROUP
            handle = {"tag": tag, "group": _GROUP, "app_id": self.app_id}
        self._run(_TOAST_PS1, data, "toast.ps1")
        return handle

    def dismiss(self, handle):
        if not handle or "tag" not in handle:
            return
        data = {
            "tag": handle["tag"],
            "group": handle.get("group", _GROUP),
            "appId": handle.get("app_id", self.app_id),
        }
        self._run(_DISMISS_PS1, data, "dismiss.ps1")

    def _run(self, script, data, label):
        """Runs a PowerShell script, passing ``data`` as a temp JSON file."""
        fd, tmp = tempfile.mkstemp(prefix="notifire-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
            result = subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", _wslpath_w(script),
                    "-PayloadPath", _wslpath_w(tmp),
                ],
                capture_output=True, text=True, timeout=20, check=False,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout).strip().splitlines()
                print(f"[notifire] {label} failed: {err[0] if err else result.returncode}",
                      file=sys.stderr)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
