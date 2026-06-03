"""Telegram engine: sends and deletes notifications through the Bot API.

Credentials come from the ``telegram`` config block (``bot_token`` /
``chat_id``) or the ``TELEGRAM_BOT_TOKEN`` / ``TELEGRAM_CHAT_ID`` environment
variables. Uses only the standard library.
"""

from __future__ import annotations

import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from ccnotify.engines.base import NotificationEngine
from ccnotify.markdown import to_telegram_html
from ccnotify.payload import SEPARATOR, Payload

_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramEngine(NotificationEngine):
    def __init__(self, config):
        super().__init__(config)
        opts = (config or {}).get("telegram", {})
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN") or opts.get("bot_token")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID") or opts.get("chat_id")
        self.timeout = float(opts.get("timeout", 10))

    def send(self, payload: Payload):
        if not self.token or not self.chat_id:
            print("[ccnotify] telegram: bot_token/chat_id not configured", file=sys.stderr)
            return None

        sections = []
        if payload.summary:
            sections.append(html.escape(payload.summary))
        body_html = to_telegram_html(payload.body, payload.limit)
        if body_html:
            if sections:  # divider between "what is requested" and the text
                sections.append(SEPARATOR)
            sections.append(body_html)
        title = f"<b>{html.escape(payload.title)}</b>"
        body = "\n".join(sections)
        text = f"{title}\n\n{body}" if body else title

        result = self._call("sendMessage", {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        })
        message_id = (result or {}).get("result", {}).get("message_id")
        return {"message_id": message_id} if message_id is not None else None

    def dismiss(self, handle):
        message_id = (handle or {}).get("message_id")
        if message_id is None or not self.token or not self.chat_id:
            return
        self._call("deleteMessage", {"chat_id": self.chat_id, "message_id": message_id})

    def _call(self, method, params):
        """POSTs to a Bot API method. Returns the parsed JSON, or ``None`` on error."""
        url = _API.format(token=self.token, method=method)
        data = urllib.parse.urlencode(params).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:200]
            print(f"[ccnotify] telegram {method}: HTTP {error.code} {detail}", file=sys.stderr)
        except Exception as error:
            print(f"[ccnotify] telegram {method}: {error}", file=sys.stderr)
        return None
