"""Normalized notification payload shared by all engines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ccnotify.markdown import to_plain


SEPARATOR = "─" * 10


class NotifyType(str, Enum):
    PERMISSION = "permission"
    FINISHED = "finished"


@dataclass
class Payload:
    """Engine-agnostic notification data.

    ``summary`` is the one-line "what is requested" (permission only);
    ``body`` is the accompanying assistant text / final message — raw
    Markdown, rendered by each engine. ``limit`` caps the visible body
    length (``0`` — no cap).
    """

    type: NotifyType
    emoji: str
    accent: str
    directory: str
    session: str
    summary: str
    body: str
    session_id: str = ""
    limit: int = 0

    @property
    def title(self) -> str:
        """Returns the toast title: ``<emoji> <directory> / <session>``."""
        head = f"{self.emoji} {self.directory}".strip()
        return f"{head} / {self.session}" if self.session else head

    def display_lines(self):
        """Returns the plain content lines (summary and/or body).

        The body is rendered without Markdown markers and clipped to
        ``limit``. No decoration: each engine adds its own separators and
        spacing, since a Windows toast has a tight line budget while Telegram
        does not.
        """
        return [line for line in (self.summary, to_plain(self.body, self.limit)) if line]
