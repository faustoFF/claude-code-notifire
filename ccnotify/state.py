"""Per-session store of pending dismissal handles, keyed by ``session_id``.

Holds ``{engine_name: handle}`` for the permission notification currently shown,
so a later hook (next ``PermissionRequest`` or ``Stop``) can dismiss it.
"""

from __future__ import annotations

import json
import os

_DIR = os.path.expanduser(os.environ.get("CCNOTIFY_STATE_DIR") or "~/.cache/cc-wsl-notify")


def _path(session_id):
    safe = "".join(c for c in (session_id or "") if c.isalnum() or c in "-_") or "default"
    return os.path.join(_DIR, f"{safe}.json")


def load(session_id):
    """Returns the stored ``{engine: handle}`` for the session, or ``{}``."""
    try:
        with open(_path(session_id), encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(session_id, handles):
    """Persists ``{engine: handle}`` for the session (overwrites)."""
    os.makedirs(_DIR, exist_ok=True)
    with open(_path(session_id), "w", encoding="utf-8") as fh:
        json.dump(handles, fh)


def clear(session_id):
    """Removes the session's stored handles, if any."""
    try:
        os.remove(_path(session_id))
    except OSError:
        pass
