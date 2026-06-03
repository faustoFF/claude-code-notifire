"""Diagnostic engine: prints the payload to stderr instead of showing a toast."""

from __future__ import annotations

import sys

from notifire.engines.base import NotificationEngine
from notifire.payload import Payload


class ConsoleEngine(NotificationEngine):
    def send(self, payload: Payload) -> None:
        print(f"[notifire] {payload.title}", file=sys.stderr)
        for line in payload.display_lines():
            for physical in line.split("\n"):
                print(f"  {physical}", file=sys.stderr)
