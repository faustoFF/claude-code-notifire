"""Turns a tool call into a one-line "what is requested" summary."""

from __future__ import annotations

import json


def _short_path(path):
    """Returns the last two path segments for compact display."""
    if not path:
        return path
    segments = path.rstrip("/").split("/")
    return "/".join(segments[-2:]) if len(segments) >= 2 else path


def summarize(tool_name, tool_input):
    """Returns a single human-readable line describing the requested tool call."""
    ti = tool_input or {}

    if tool_name == "Bash":
        command = (ti.get("command") or "").strip()
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

    if ti:
        compact = json.dumps(ti, ensure_ascii=False)
        if len(compact) > 120:
            compact = compact[:117] + "…"
        return f"{tool_name}: {compact}"

    return tool_name or "tool"
