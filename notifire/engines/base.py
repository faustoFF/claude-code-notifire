"""Notification engine interface."""

from __future__ import annotations

import abc

from notifire.payload import Payload


class NotificationEngine(abc.ABC):
    """A notification backend. Implement :meth:`send` and register it."""

    def __init__(self, config):
        self.config = config or {}

    @abc.abstractmethod
    def send(self, payload: Payload):
        """Shows the notification. Returns a JSON-serializable dismissal handle
        for transient notifications (so they can be removed later), or ``None``."""

    def dismiss(self, handle) -> None:
        """Removes a previously shown notification by its handle. No-op by default."""
