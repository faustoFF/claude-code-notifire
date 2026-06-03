"""Telegram engine: sends the notification through the Bot API.

Credentials come from the ``telegram`` config block (``bot_token`` /
``chat_id``) or the ``TELEGRAM_BOT_TOKEN`` / ``TELEGRAM_CHAT_ID`` environment
variables. Uses only the standard library.
"""

from __future__ import annotations

import html
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from ccnotify.engines.base import NotificationEngine
from ccnotify.payload import Payload

_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramEngine(NotificationEngine):
    def __init__(self, config):
        super().__init__(config)
        opts = (config or {}).get("telegram", {})
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN") or opts.get("bot_token")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID") or opts.get("chat_id")
        self.timeout = float(opts.get("timeout", 10))

    def send(self, payload: Payload) -> None:
        if not self.token or not self.chat_id:
            print("[ccnotify] telegram: bot_token/chat_id not configured", file=sys.stderr)
            return

        title = f"<b>{html.escape(payload.title)}</b>"
        body = "\n".join(html.escape(line) for line in payload.display_lines())
        text = f"{title}\n\n{body}" if body else title
        data = urllib.parse.urlencode({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }).encode("utf-8")

        request = urllib.request.Request(_API.format(token=self.token), data=data, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout):
                pass
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")[:200]
            print(f"[ccnotify] telegram: HTTP {error.code} {body}", file=sys.stderr)
        except Exception as error:
            print(f"[ccnotify] telegram: {error}", file=sys.stderr)
