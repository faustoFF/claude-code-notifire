"""Turns a tool call into a one-line "what is requested" summary."""

from __future__ import annotations


def _short_path(path):
    """Returns the last two path segments for compact display."""
    if not path:
        return path
    segments = path.rstrip("/").split("/")
    return "/".join(segments[-2:]) if len(segments) >= 2 else path


def _clip(text):
    """Clips the text to 24 chars for compact display."""
    if len(text) > 24:
        text = text[:23].rstrip() + "…"
    return text


def _first_text(value):
    """Returns the first non-empty string found in the value, walking dicts and lists."""
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        for item in value:
            found = _first_text(item)
            if found:
                return found
    return None


def _fragment(tool_name, ti):
    """Returns the tool-specific input fragment as a single collapsed line."""
    if tool_name == "Bash":
        return " ".join((ti.get("command") or "").split())

    if tool_name in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Read"):
        return _short_path(ti.get("file_path") or ti.get("notebook_path") or "")

    if tool_name in ("Glob", "Grep"):
        return ti.get("pattern") or ""

    return " ".join((_first_text(ti) or "").split())


def summarize(tool_name, tool_input):
    """Returns a single human-readable line describing the requested tool call.

    When the input carries a ``description`` (shown as the notification body)
    the fragment is clipped short; otherwise it is passed in full and the
    engine decides how much fits.
    """
    ti = tool_input or {}

    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        return f"{parts[1]}/{'__'.join(parts[2:])}" if len(parts) >= 3 else tool_name

    fragment = _fragment(tool_name, ti)
    if fragment and ti.get("description"):
        fragment = _clip(fragment)
    return f"{tool_name}: {fragment}" if fragment else (tool_name or "tool")
