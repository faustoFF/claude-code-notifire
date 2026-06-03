"""Turns a tool call into a one-line "what is requested" summary."""

from __future__ import annotations


def _short_path(path):
    """Returns the last two path segments for compact display."""
    if not path:
        return path
    segments = path.rstrip("/").split("/")
    return "/".join(segments[-2:]) if len(segments) >= 2 else path


def _clip(text):
    """Collapses whitespace and clips the text to 24 chars for compact display."""
    text = " ".join((text or "").split())
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


def summarize(tool_name, tool_input):
    """Returns a single human-readable line describing the requested tool call."""
    ti = tool_input or {}

    if tool_name == "Bash":
        command = _clip(ti.get("command") or "")
        return f"Bash: {command}" if command else "Bash"

    if tool_name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        return f"{tool_name}: {_short_path(path)}" if path else tool_name

    if tool_name == "Read":
        path = ti.get("file_path") or ""
        return f"Read: {_short_path(path)}" if path else "Read"

    if tool_name in ("Glob", "Grep"):
        pattern = ti.get("pattern") or ""
        return f"{tool_name}: {pattern}" if pattern else tool_name

    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        return f"{parts[1]}/{'__'.join(parts[2:])}" if len(parts) >= 3 else tool_name

    text = _first_text(ti)
    if text:
        return f"{tool_name}: {_clip(text)}"

    return tool_name or "tool"
