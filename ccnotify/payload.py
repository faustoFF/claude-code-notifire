"""Normalized notification payload shared by all engines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


SEPARATOR = "─" * 10


class NotifyType(str, Enum):
    PERMISSION = "permission"
    FINISHED = "finished"


@dataclass
class Payload:
    """Engine-agnostic notification data.

    ``summary`` is the one-line "what is requested" (permission only);
    ``body`` is the accompanying assistant text / final message.
    """

    type: NotifyType
    emoji: str
    accent: str
    directory: str
    session: str
    summary: str
    body: str
    session_id: str = ""

    @property
    def title(self) -> str:
        """Returns the toast title: ``<emoji> <directory> — <session>``."""
        head = f"{self.emoji} {self.directory}".strip()
        return f"{head} — {self.session}" if self.session else head

    def display_lines(self):
        """Returns the plain content lines (summary and/or body).

        No decoration: each engine adds its own separators and spacing, since a
        Windows toast has a tight line budget while Telegram does not.
        """
        return [line for line in (self.summary, self.body) if line]
