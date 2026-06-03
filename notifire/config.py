"""Configuration loading with built-in defaults.

The tool works with no config file at all: :func:`load_config` falls back to
:data:`DEFAULTS`. A user config may be placed at ``$NOTIFIRE_CONFIG``,
``~/.config/claude-code-notifire/config.json`` or ``<repo>/config.json``.
"""

from __future__ import annotations

import json
import os

DEFAULT_APP_ID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"

DEFAULTS = {
    "engine": "winrt",
    "events": {"permission": True, "finished": True},
    "types": {
        "permission": {"emoji": "🔐", "accent": "amber"},
        "finished": {"emoji": "✅", "accent": "green"},
    },
    "winrt": {"app_id": DEFAULT_APP_ID, "sound": True},
}

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _candidate_paths():
    env = os.environ.get("NOTIFIRE_CONFIG")
    if env:
        yield env
    yield os.path.expanduser("~/.config/claude-code-notifire/config.json")
    yield os.path.join(_REPO_ROOT, "config.json")


def _merge(base, override):
    """Returns ``base`` deep-merged with ``override`` (two levels of dicts)."""
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = {**result[key], **value}
        else:
            result[key] = value
    return result


def load_config():
    """Returns the effective config dict (defaults merged with the first file found)."""
    for path in _candidate_paths():
        try:
            with open(path, encoding="utf-8") as fh:
                return _merge(DEFAULTS, json.load(fh))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return dict(DEFAULTS)
