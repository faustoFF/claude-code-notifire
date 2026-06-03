"""Readers for the Claude Code session transcript (JSONL)."""

from __future__ import annotations

import json


def _iter_entries(path):
    """Yields parsed JSON objects from a JSONL transcript, skipping bad lines."""
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def read_session_title(path):
    """Returns the latest session title (``ai-title`` entry), or ``None``."""
    title = None
    for entry in _iter_entries(path):
        if entry.get("type") == "ai-title" and entry.get("aiTitle"):
            title = entry["aiTitle"]
    return title


def read_last_assistant_text(path):
    """Returns the text of the last assistant message, or ``None``.

    Concatenates ``text`` content blocks of the final ``role == "assistant"``
    entry, ignoring ``thinking`` and tool-use blocks.
    """
    text = None
    for entry in _iter_entries(path):
        message = entry.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        parts = [
            block.get("text", "")
            for block in (message.get("content") or [])
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        joined = "".join(parts).strip()
        if joined:
            text = joined
    return text
