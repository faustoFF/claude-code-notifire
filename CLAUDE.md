# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

The repository is published on GitHub: all code, comments, docs, and commit messages are English-only.

## What this is

A notification hook for Claude Code: `notify.py` is wired into the user's `~/.claude/settings.json` as a `PermissionRequest` and `Stop` hook. It reads the hook event JSON from stdin and delivers a notification through one or more pluggable engines (Windows toast via WSL, Telegram, console). Pure Python 3 standard library — no dependencies, no build step, no test suite.

## Commands

Smoke-test the full pipeline without sending a real notification (console engine prints to stderr):

```bash
echo '{"hook_event_name":"Stop","cwd":"'"$PWD"'","last_assistant_message":"Done."}' \
  | NOTIFIRE_ENGINE=console python3 notify.py
```

Simulate a permission request:

```bash
echo '{"hook_event_name":"PermissionRequest","cwd":"'"$PWD"'","session_id":"test1234","tool_name":"Bash","tool_input":{"command":"npm test","description":"Run the test suite"}}' \
  | NOTIFIRE_ENGINE=console python3 notify.py
```

Useful env overrides: `NOTIFIRE_ENGINE` (engine override), `NOTIFIRE_CONFIG` (config path), `NOTIFIRE_STATE_DIR` (state dir, default `~/.cache/claude-code-notifire`).

## Architecture

Flow: hook event JSON on stdin → `notify.py` (`main`/`build_payload`) → normalized `Payload` → each configured engine's `send()`.

- `notify.py` — entry point and dispatch by `hook_event_name`. Must never write to stdout (stdout would be interpreted as a hook decision); all diagnostics go to stderr. Engine errors are caught and isolated so the hook never breaks the session.
- `notifire/payload.py` — `Payload`, the engine-agnostic notification: `title` (`<emoji> <directory> / <session>`), `summary` (one-line "what is requested", permission only), `body` (raw Markdown; each engine renders and truncates it its own way).
- `notifire/engines/` — `base.py` defines `NotificationEngine` (`send(payload) -> handle | None`, optional `dismiss(handle)`); `__init__.py` holds the `_REGISTRY` name→class map. Engines: `winrt` (default), `telegram`, `console` (diagnostics). To add an engine: implement it, register in `_REGISTRY` — config key `engine` (string or list) selects it.
- `notifire/state.py` — per-session `{engine: handle}` store in `~/.cache/claude-code-notifire`, powering auto-dismissal: the next `PermissionRequest` or `Stop` for a session removes the previous permission notification (toast from Action Center, Telegram message deleted). Pruned on every hook run.
- `notifire/config.py` — `DEFAULTS` deep-merged (two levels) with the first config file found: `$NOTIFIRE_CONFIG` → `~/.config/claude-code-notifire/config.json` → `<repo>/config.json` (gitignored, may hold secrets).
- `notifire/markdown.py` — renders the Markdown subset Claude emits as plain text (`to_plain`) or Telegram HTML (`to_telegram_html`); truncation always closes open tags so the HTML stays well-formed.
- `notifire/permission.py` — `summarize(tool_name, tool_input)` builds the one-line request summary (`Bash: npm test`).
- `notifire/transcript.py` — reads the session JSONL transcript for the session title (`ai-title`) and the last assistant message fallback.
- `windows/toast.ps1` / `windows/dismiss.ps1` — run by the WinRT engine through `powershell.exe`; data is passed via a temp JSON file (path translated with `wslpath -w`) to avoid quoting issues.

## Conventions

- The README's Installation section doubles as an executable runbook for AI agents — when changing hook setup, config locations, or the verification command, update it in lockstep.
- Engines must stay dependency-free (standard library only); the WinRT engine may shell out to `powershell.exe`.
