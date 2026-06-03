#!/usr/bin/env python3
"""Entry point for Claude Code hooks.

Reads the hook event JSON from stdin, builds a normalized :class:`Payload` and
hands it to the configured notification engine. Dispatch is driven by
``hook_event_name`` (``PermissionRequest`` and ``Stop``). Writes nothing to
stdout so it is never interpreted as a hook decision; diagnostics go to stderr.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ccnotify import permission, state, transcript  # noqa: E402
from ccnotify.config import load_config  # noqa: E402
from ccnotify.engines import get_engine  # noqa: E402
from ccnotify.payload import NotifyType, Payload  # noqa: E402


def _clip(text, limit):
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _short_id(session_id):
    return session_id[:8] if session_id else "session"


def _style(config, key):
    style = config["types"].get(key, {})
    return style.get("emoji", ""), style.get("accent", "")


def build_payload(event, config):
    """Returns a :class:`Payload` for the event, or ``None`` to send nothing."""
    hook = event.get("hook_event_name")
    cwd = event.get("cwd") or os.getcwd()
    directory = os.path.basename(cwd.rstrip("/")) or cwd
    transcript_path = event.get("transcript_path")
    session_id = event.get("session_id") or ""
    session = (
        (transcript.read_session_title(transcript_path) if transcript_path else None)
        or _short_id(session_id)
    )
    limit = int(config.get("max_body_chars", 220))

    if hook == "PermissionRequest":
        if not config["events"].get("permission", True):
            return None
        emoji, accent = _style(config, "permission")
        tool_input = event.get("tool_input") or {}
        summary = permission.summarize(event.get("tool_name", ""), tool_input)
        description = tool_input.get("description") or ""
        return Payload(NotifyType.PERMISSION, emoji, accent, directory, session,
                       _clip(summary, limit), description, session_id, limit=limit)

    if hook == "Stop":
        if not config["events"].get("finished", True):
            return None
        if event.get("background_tasks"):
            return None
        emoji, accent = _style(config, "finished")
        body = event.get("last_assistant_message")
        if not body and transcript_path:
            body = transcript.read_last_assistant_text(transcript_path)
        return Payload(NotifyType.FINISHED, emoji, accent, directory, session,
                       "", body or "", session_id, limit=limit)

    return None


def _resolve_engines(config):
    engines = os.environ.get("CCNOTIFY_ENGINE") or config.get("engine", "winrt")
    return [engines] if isinstance(engines, str) else engines


def _dismiss_pending(session_id, config):
    """Removes the notification(s) recorded for the session (resolved request)."""
    for name, handle in state.load(session_id).items():
        try:
            get_engine(name, config).dismiss(handle)
        except Exception as error:
            print(f"[ccnotify] engine {name!r} dismiss error: {error}", file=sys.stderr)


def _send(payload, engines, config):
    """Sends the payload via each engine. Returns ``{engine: handle}``."""
    handles = {}
    for name in engines:
        try:  # never break the hook, and isolate engines from each other
            handle = get_engine(name, config).send(payload)
            if handle is not None:
                handles[name] = handle
        except Exception as error:
            print(f"[ccnotify] engine {name!r} error: {error}", file=sys.stderr)
    return handles


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0

    config = load_config()
    hook = event.get("hook_event_name")
    session_id = event.get("session_id") or ""
    engines = _resolve_engines(config)

    state.prune()  # runs on every hook, so cleanup never depends on a clean Stop

    if hook == "PermissionRequest":
        _dismiss_pending(session_id, config)  # the previous request is now resolved
        payload = build_payload(event, config)
        handles = _send(payload, engines, config) if payload is not None else {}
        state.save(session_id, handles)
        return 0

    if hook == "Stop":
        _dismiss_pending(session_id, config)  # the turn's last request is resolved
        state.clear(session_id)
        payload = build_payload(event, config)
        if payload is not None:
            _send(payload, engines, config)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
