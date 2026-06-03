"""Notification engine interface."""

from __future__ import annotations

import abc

from ccnotify.payload import Payload


class NotificationEngine(abc.ABC):
    """A notification backend. Implement :meth:`send` and register it."""

    def __init__(self, config):
        self.config = config or {}

    @abc.abstractmethod
    def send(self, payload: Payload) -> None:
        """Shows the notification described by ``payload``."""
