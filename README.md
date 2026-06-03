# cc-wsl-to-ps-notify

Native Windows notifications for Claude Code running in WSL2. A toast pops up
when a session **stops on a permission request** or **finishes its response** —
handy when the terminal window is minimized.

Each notification shows: an accent emoji (color by type), the working directory
name, the session title, what exactly is being requested, and Claude's
accompanying text.

## Installation

The easiest way: paste this prompt into a Claude Code session running in WSL2,
and Claude will perform the steps below for you:

```text
Please, install https://raw.githubusercontent.com/faustoff/cc-wsl-to-ps-notify/master/README.md
```

You can also follow the steps manually. AI agents performing this
installation: execute the steps exactly as written, do not duplicate hooks
that are already present, and report the verification output to the user.

1. Clone the repository anywhere inside WSL:

   ```bash
   git clone https://github.com/faustoff/cc-wsl-to-ps-notify.git ~/cc-wsl-to-ps-notify
   ```

2. Open `~/.claude/settings.json` (create it if it does not exist) and add the
   `PermissionRequest` and `Stop` hooks, replacing the path with the actual
   clone location. If the file already has a `hooks` section, merge these
   entries into it; skip any entry whose `args` already points to this
   `notify.py`:

   ```json
   {
     "hooks": {
       "PermissionRequest": [
         {
           "matcher": "*",
           "hooks": [
             {
               "type": "command",
               "command": "python3",
               "args": ["/home/<user>/cc-wsl-to-ps-notify/notify.py"],
               "async": true
             }
           ]
         }
       ],
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python3",
               "args": ["/home/<user>/cc-wsl-to-ps-notify/notify.py"],
               "async": true
             }
           ]
         }
       ]
     }
   }
   ```

3. Verify the pipeline without showing a real toast (the `console` engine
   prints the notification to stderr):

   ```bash
   cd ~/cc-wsl-to-ps-notify
   echo '{"hook_event_name":"Stop","cwd":"'"$PWD"'","last_assistant_message":"Done."}' \
     | CCNOTIFY_ENGINE=console python3 notify.py
   ```

   Expected output:

   ```text
   [ccnotify] ✅ cc-wsl-to-ps-notify / session
     Done.
   ```

4. Restart your Claude Code sessions; verify the hooks are active with the
   `/hooks` command.

## How it works

Claude Code hooks run `notify.py` (inside WSL). The script reads the hook event
JSON from stdin, builds a normalized payload and shows a notification on the
Windows side through a pluggable engine.

| Hook | When | Emoji |
|---|---|---|
| `PermissionRequest` | Claude is waiting for confirmation; the tool and its arguments are shown | 🔐 |
| `Stop` | Claude finished responding; the body carries the final answer | ✅ |

Available engines: **WinRT** (`windows/toast.ps1` via `powershell.exe`, no
dependencies, default) and **Telegram** (Bot API). The `engine` field accepts a
single engine name or a list — with a list the notification goes to all of them
at once (e.g. a toast on the PC and a Telegram message on the phone).

Permission notifications are dismissed automatically once the request is
resolved: the next hook (a new `PermissionRequest` or `Stop`) removes the toast
from the Action Center and deletes the Telegram message. Per-session dismissal
handles are kept in `~/.cache/cc-wsl-notify`; files older than 7 days are
pruned automatically.

## Notification examples

The layout is the same everywhere: a `<emoji> <directory> / <session>` title,
the request line and the accompanying text. For a permission request the
accompanying text is the call description (`tool_input.description`, when
present); for a finished response it is Claude's final answer. The text arrives
as Markdown and each engine renders it its own way: Telegram into formatting
(bold, italic, code, links), toast and console into plain text without markers.

### WinRT (toast)

The title is the bold toast header, the app attribution reads "Windows
PowerShell". The body is the lines below the title (compact, no separator, so
it fits the banner).

Permission request:

```text
🔐 cc-wsl-to-ps-notify / windows-notifications-wsl2
Bash: git status
Check the repository state
```

Finished response:

```text
✅ cc-wsl-to-ps-notify / windows-notifications-wsl2
Done: added Windows notifications.
```

### Telegram

The title is bold (HTML) followed by a blank line; a divider separates the
request from the accompanying text. The body Markdown is converted to Telegram
HTML (`**bold**`, `*italic*`, code, code blocks, links); truncation to the
Telegram message length limit never breaks the markup — open tags are closed
correctly.

Permission request:

```text
🔐 cc-wsl-to-ps-notify / windows-notifications-wsl2

Bash: git status
──────────
Check the repository state
```

Finished response:

```text
✅ cc-wsl-to-ps-notify / windows-notifications-wsl2

Done: added Windows notifications.
```

### Console (diagnostics)

Writes to stderr (`CCNOTIFY_ENGINE=console`), for debugging.

Permission request:

```text
[ccnotify] 🔐 cc-wsl-to-ps-notify — windows-notifications-wsl2
  Bash: git status
  Check the repository state
```

Finished response:

```text
[ccnotify] ✅ cc-wsl-to-ps-notify — windows-notifications-wsl2
  Done: added Windows notifications.
```

## Requirements

- WSL2 with working Windows interop (`powershell.exe` reachable from WSL).
- `python3` inside WSL.
- Windows PowerShell 5.1+ (ships with Windows).

## Configuration

Without a config file the built-in defaults are used. To override them, copy
`config.example.json` to one of these locations (in priority order):

1. the path from the `CCNOTIFY_CONFIG` environment variable;
2. `~/.config/cc-wsl-notify/config.json`;
3. `config.json` in the repository root.

Fields: `engine` (string or list), `events` (enable/disable types), `types`
(emoji/accent), `winrt.app_id`, `winrt.sound`, `telegram.bot_token`,
`telegram.chat_id`.

By default toasts are attributed to "Windows PowerShell" (the PowerShell
AUMID). Branding them as "Claude Code" requires a separate shortcut with its
own AppUserModelID, whose path goes into `winrt.app_id`.

### Telegram

Enabled via `engine`: `"telegram"` (Telegram only) or `["winrt", "telegram"]`
(toast and Telegram together). The bot token and chat id come from
`telegram.bot_token` / `telegram.chat_id` or from the `TELEGRAM_BOT_TOKEN` /
`TELEGRAM_CHAT_ID` environment variables.

Keep secrets out of the repository — in `~/.config/cc-wsl-notify/config.json`
(`chmod 600`). `config.json` in the repository root is listed in `.gitignore`.

## Adding a new engine

1. Implement `NotificationEngine.send(payload)` in `ccnotify/engines/<name>.py`
   (see `ccnotify/engines/base.py` and `payload.py`). Override `dismiss(handle)`
   if the notification can be removed once the request is resolved.
2. Register the class in `ccnotify/engines/__init__.py`.
3. Set `"engine": "<name>"` in the config.

## Limitations

- Action buttons don't work in fire-and-forget WinRT toasts without AUMID/COM
  registration — toasts are informational in the current version. A
  SnoreToast-based engine is planned for working buttons.
- Windows toast text color is not configurable; the emoji carries the color.
