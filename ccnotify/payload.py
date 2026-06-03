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

    @property
    def title(self) -> str:
        """Returns the toast title: ``<emoji> <directory> — <session>``."""
        head = f"{self.emoji} {self.directory}".strip()
        return f"{head} — {self.session}" if self.session else head

    def display_lines(self):
        """Returns the text lines shown below the title.

        When a summary precedes the accompanying text, a divider is glued to
        the text (same block) so it can never render on its own — it is shown
        only together with the text that follows it.
        """
        lines = []
        if self.summary:
            lines.append(self.summary)
        if self.body:
            lines.append(f"{SEPARATOR}\n{self.body}" if lines else self.body)
        return lines
