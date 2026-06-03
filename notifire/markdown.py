"""Renders the Markdown subset Claude emits as plain text or Telegram HTML.

Supported: ``**bold**``/``__bold__``, ``*italic*``/``_italic_``, ``inline
code``, fenced code blocks, ``[links](url)``, ``#`` headers (rendered bold)
and list bullets (``-``/``*``/``+`` becomes ``•``). Unpaired markers stay
literal, so the HTML output is always well-formed; truncation closes any open
tag. Known limitation: no nesting — inside ``**a `b` c**`` the code wins and
the ``**`` stay literal.
"""

from __future__ import annotations

import html
import re

_HEADER = re.compile(r"#{1,6}\s+(.*)")
_BULLET = re.compile(r"(\s*)[-*+]\s+(.*)")
_INLINE = (
    ("code", re.compile(r"`([^`\n]+)`")),
    ("link", re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")),
    ("bold", re.compile(r"\*\*(.+?)\*\*")),
    ("bold", re.compile(r"__(.+?)__")),
    ("italic", re.compile(r"\*([^*\n]+)\*")),
    ("italic", re.compile(r"_([^_\n]+)_")),
)
_TAGS = {"bold": "b", "italic": "i", "code": "code", "pre": "pre"}


def _intraword(line, pos, match):
    """Returns ``True`` for an underscore marker inside a word (``snake_case``)."""
    if not match.group(0).startswith("_"):
        return False
    before = line[pos - 1] if pos else ""
    after = line[match.end()] if match.end() < len(line) else ""
    return before.isalnum() or after.isalnum()


def _scan_inline(line):
    """Splits one line into ``(kind, text, url)`` segments, literals merged."""
    segments = []
    literal = []

    def flush():
        if literal:
            segments.append(("text", "".join(literal), None))
            del literal[:]

    pos = 0
    while pos < len(line):
        for kind, pattern in _INLINE:
            match = pattern.match(line, pos)
            if match and not _intraword(line, pos, match):
                flush()
                url = match.group(2) if kind == "link" else None
                segments.append((kind, match.group(1), url))
                pos = match.end()
                break
        else:
            literal.append(line[pos])
            pos += 1
    flush()
    return segments


def _segments(text):
    """Parses Markdown into a flat list of ``(kind, text, url)`` segments."""
    segments = []
    lines = (text or "").split("\n")
    i = 0
    while i < len(lines):
        if i:
            segments.append(("linebreak", "\n", None))
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1  # past the closing fence
            segments.append(("pre", "\n".join(block), None))
            continue
        header = _HEADER.match(stripped)
        bullet = _BULLET.match(line)
        if header:
            for kind, value, url in _scan_inline(header.group(1)):
                kind = "bold" if kind in ("text", "italic") else kind
                segments.append((kind, value, url))
        elif bullet:
            segments.append(("text", bullet.group(1) + "• ", None))
            segments.extend(_scan_inline(bullet.group(2)))
        else:
            segments.extend(_scan_inline(line))
        i += 1
    return segments


def _trim(segments, limit):
    """Trims segments to ``limit`` visible chars, appending ``…`` when cut."""
    if limit <= 0:
        return segments
    if sum(len(text) for kind, text, _ in segments if kind != "linebreak") <= limit:
        return segments
    out, used, budget = [], 0, limit - 1  # one char reserved for the ellipsis
    for kind, text, url in segments:
        if kind == "linebreak":
            out.append((kind, text, url))
            continue
        room = budget - used
        if room <= 0:
            break
        if len(text) > room:
            cut = text[:room].rstrip()
            if cut:
                out.append((kind, cut, url))
            break
        out.append((kind, text, url))
        used += len(text)
    while out and out[-1][0] == "linebreak":
        out.pop()
    if not out:
        return [("text", "…", None)]
    kind, text, url = out[-1]
    out[-1] = (kind, text + "…", url)
    return out


def to_plain(text, limit=0):
    """Returns the text with Markdown markers removed, clipped to ``limit``."""
    return "".join(value for _, value, _ in _trim(_segments(text), limit))


def to_telegram_html(text, limit=0):
    """Returns the text as well-formed Telegram HTML, clipped to ``limit``.

    The visible-character budget is counted before escaping, and tags are only
    ever emitted as open/close pairs, so truncation cannot leave a tag open.
    """
    parts = []
    for kind, value, url in _trim(_segments(text), limit):
        escaped = html.escape(value)
        if kind == "link":
            parts.append(f'<a href="{html.escape(url, quote=True)}">{escaped}</a>')
        elif kind in _TAGS:
            tag = _TAGS[kind]
            parts.append(f"<{tag}>{escaped}</{tag}>")
        else:
            parts.append(escaped)
    return "".join(parts)
