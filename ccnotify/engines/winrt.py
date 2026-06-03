"""WinRT engine: shows a native Windows toast via PowerShell.

Serializes the payload to a temp JSON file, translates WSL paths to Windows
paths with ``wslpath -w`` and runs ``windows/toast.ps1`` through
``powershell.exe``. Passing data via a file avoids all quoting/escaping issues.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

from ccnotify.config import DEFAULT_APP_ID
from ccnotify.engines.base import NotificationEngine
from ccnotify.payload import Payload

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TOAST_PS1 = os.path.join(_REPO_ROOT, "windows", "toast.ps1")


def _wslpath_w(path):
    """Returns the Windows form of a WSL path via ``wslpath -w``."""
    result = subprocess.run(
        ["wslpath", "-w", path], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


class WinRtEngine(NotificationEngine):
    def __init__(self, config):
        super().__init__(config)
        opts = (config or {}).get("winrt", {})
        self.app_id = opts.get("app_id") or DEFAULT_APP_ID
        self.sound = bool(opts.get("sound", True))

    def send(self, payload: Payload) -> None:
        data = {
            "appId": self.app_id,
            "sound": self.sound,
            "title": payload.title,
            "lines": payload.display_lines(),
        }
        fd, tmp = tempfile.mkstemp(prefix="ccnotify-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
            result = subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", _wslpath_w(_TOAST_PS1),
                    "-PayloadPath", _wslpath_w(tmp),
                ],
                capture_output=True, text=True, timeout=20, check=False,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout).strip().splitlines()
                print(f"[ccnotify] toast.ps1 failed: {err[0] if err else result.returncode}",
                      file=sys.stderr)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
