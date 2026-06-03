"""Engine registry. Add a backend by implementing :class:`NotificationEngine`
and registering it in ``_REGISTRY``; select it via ``"engine"`` in the config.
"""

from __future__ import annotations

from ccnotify.engines.console import ConsoleEngine
from ccnotify.engines.telegram import TelegramEngine
from ccnotify.engines.winrt import WinRtEngine

_REGISTRY = {
    "winrt": WinRtEngine,
    "telegram": TelegramEngine,
    "console": ConsoleEngine,
}


def get_engine(name, config):
    """Returns an engine instance for ``name``. Raises ``ValueError`` if unknown."""
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"unknown notification engine: {name!r}")
    return cls(config)
