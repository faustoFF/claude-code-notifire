#!/usr/bin/env bash
# Idempotently wires the PermissionRequest and Stop hooks into the user-level
# Claude Code settings (~/.claude/settings.json), pointing at this repo's notify.py.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CCNOTIFY_NOTIFY_PATH="${REPO_DIR}/notify.py"
export CCNOTIFY_SETTINGS="${CCNOTIFY_SETTINGS:-${HOME}/.claude/settings.json}"

python3 - <<'PY'
import json
import os

settings_path = os.environ["CCNOTIFY_SETTINGS"]
notify = os.environ["CCNOTIFY_NOTIFY_PATH"]

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
try:
    with open(settings_path, encoding="utf-8") as fh:
        data = json.load(fh)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}

hooks = data.setdefault("hooks", {})


def handler():
    return {"type": "command", "command": "python3", "args": [notify], "async": True}


def ensure(event, matcher):
    groups = hooks.setdefault(event, [])
    for group in groups:
        for hook in group.get("hooks", []):
            if hook.get("command") == "python3" and notify in (hook.get("args") or []):
                return False
    group = {"hooks": [handler()]}
    if matcher:
        group = {"matcher": matcher, **group}
    groups.append(group)
    return True


added_permission = ensure("PermissionRequest", "*")
added_stop = ensure("Stop", None)

with open(settings_path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

print(f"settings:          {settings_path}")
print(f"notify.py:         {notify}")
print(f"PermissionRequest: {'added' if added_permission else 'already present'}")
print(f"Stop:              {'added' if added_stop else 'already present'}")
PY

echo "Done. Restart Claude Code sessions (or run /hooks) to pick up the changes."
