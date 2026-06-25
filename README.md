# claude-code-notifire

![A Windows toast and a Telegram message sent by claude-code-notifire](docs/banner.png)

Notifications for Claude Code: a notification arrives when a session **stops
on a permission request** or **finishes its response** — handy when the
terminal window is minimized or you are away from the machine.

Notifications are delivered through pluggable engines, used alone or together:

- **WinRT** — a native Windows toast, for Claude Code running in WSL2;
- **Telegram** — a Bot API message, works wherever Claude Code runs (WSL is
  not required).

Each notification shows: an accent emoji (color by type), the working directory
name, the session title, what exactly is being requested, and Claude's
accompanying text.

## Requirements

- `python3` on the machine where Claude Code runs.

Per engine:

- **WinRT**: WSL2 with working Windows interop (`powershell.exe` reachable
  from WSL) and Windows PowerShell 5.1+ (ships with Windows).
- **Telegram**: a bot token (from [@BotFather](https://t.me/BotFather)) and a
  chat id. No WSL or Windows required.

## Installation

> [!TIP]
> **The easiest way — let Claude install it for you.** Paste this prompt into
> a Claude Code session, and Claude will perform all the steps below:
>
> ```text
> Please, install https://raw.githubusercontent.com/faustoff/claude-code-notifire/master/README.md
> ```

You can also follow the steps manually. AI agents performing this
installation: first ask the user which engines to enable — `winrt` (Windows
toast, requires WSL2), `telegram` (requires a bot token and chat id; ask for
them), or both — then execute the steps exactly as written, do not duplicate
hooks that are already present, and report the verification output to the
user.

1. Clone the repository on the machine where Claude Code runs (for the WinRT
   engine that means inside WSL):

   ```bash
   git clone https://github.com/faustoff/claude-code-notifire.git ~/claude-code-notifire
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
               "args": ["/home/<user>/claude-code-notifire/notify.py"],
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
               "args": ["/home/<user>/claude-code-notifire/notify.py"],
               "async": true
             }
           ]
         }
       ]
     }
   }
   ```

3. Pick the engines. The default is `winrt` (Windows toast) — no extra
   configuration needed, skip this step. For Telegram (alone or together with
   the toast) create `~/.config/claude-code-notifire/config.json`:

   ```json
   {
     "engine": ["winrt", "telegram"],
     "telegram": {
       "bot_token": "<token from @BotFather>",
       "chat_id": "<your chat id>"
     }
   }
   ```

   For Telegram only — without WSL and Windows at all — set
   `"engine": "telegram"`. Restrict access to the file: `chmod 600`.

4. Verify the pipeline without sending a real notification (the `console`
   engine prints it to stderr):

   ```bash
   cd ~/claude-code-notifire
   echo '{"hook_event_name":"Stop","cwd":"'"$PWD"'","last_assistant_message":"Done."}' \
     | NOTIFIRE_ENGINE=console python3 notify.py
   ```

   Expected output:

   ```text
   [notifire] ✅ claude-code-notifire / session
     Done.
   ```

5. Restart your Claude Code sessions; verify the hooks are active with the
   `/hooks` command.

## Configuration

Without a config file the built-in defaults are used. To override them, copy
`config.example.json` to one of these locations (in priority order):

1. the path from the `NOTIFIRE_CONFIG` environment variable;
2. `~/.config/claude-code-notifire/config.json`;
3. `config.json` in the repository root.

Fields: `engine` (string or list), `events` (enable/disable types), `types`
(emoji/accent), `winrt.app_id`, `winrt.sound`, `telegram.bot_token`,
`telegram.chat_id`.

`winrt.sound` accepts three values: `true` (default — the standard Windows
notification sound, which respects the system sound scheme), `false` (silent),
or a Windows path to a `.wav` file (e.g.
`"C:\\Windows\\Media\\Windows Notify.wav"`). With a path the toast is silent and
the file is played directly, so the sound is heard even when the Windows sound
scheme is set to "No Sounds" — useful for a sound dedicated to Claude Code only.

A ready-made bell sound is bundled at `sounds/bell.wav`; copy it to a location
on the Windows filesystem and set `winrt.sound` to that path.

By default toasts are attributed to "Windows PowerShell" (the PowerShell
AUMID). Branding them as "Claude Code" requires a separate shortcut with its
own AppUserModelID, whose path goes into `winrt.app_id`.

### Telegram

Enabled via `engine`: `"telegram"` (Telegram only) or `["winrt", "telegram"]`
(toast and Telegram together). The bot token and chat id come from
`telegram.bot_token` / `telegram.chat_id` or from the `TELEGRAM_BOT_TOKEN` /
`TELEGRAM_CHAT_ID` environment variables.

Keep secrets out of the repository — in `~/.config/claude-code-notifire/config.json`
(`chmod 600`). `config.json` in the repository root is listed in `.gitignore`.

## How it works

Claude Code hooks run `notify.py`. The script reads the hook event JSON from
stdin, builds a normalized payload and delivers it through the configured
engines.

| Hook | When | Emoji |
|---|---|---|
| `PermissionRequest` | Claude is waiting for confirmation; the tool and its arguments are shown | 🔐 |
| `Stop` | Claude finished responding; the body carries the final answer | ✅ |

Available engines: **WinRT** (`windows/toast.ps1` via `powershell.exe`, no
dependencies, default; requires WSL2) and **Telegram** (Bot API, standard
library only; works on any machine). The `engine` field accepts a single
engine name or a list — with a list the notification goes to all of them at
once (e.g. a toast on the PC and a Telegram message on the phone).

Permission notifications are dismissed automatically once the request is
resolved: the next hook (a new `PermissionRequest` or `Stop`) removes the toast
from the Action Center and deletes the Telegram message. Per-session dismissal
handles are kept in `~/.cache/claude-code-notifire`; files older than 7 days are
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
🔐 my-app / fix-login-bug
Bash: npm test
Run the test suite
```

Finished response:

```text
✅ my-app / fix-login-bug
Done: the login bug is fixed.
```

### Telegram

The title is bold (HTML) followed by a blank line; a divider separates the
request from the accompanying text. The body Markdown is converted to Telegram
HTML (`**bold**`, `*italic*`, code, code blocks, links); truncation to the
Telegram message length limit never breaks the markup — open tags are closed
correctly.

Permission request:

```text
🔐 my-app / fix-login-bug

Bash: npm test
──────────
Run the test suite
```

Finished response:

```text
✅ my-app / fix-login-bug

Done: the login bug is fixed.
```

### Console (diagnostics)

Writes to stderr (`NOTIFIRE_ENGINE=console`), for debugging.

Permission request:

```text
[notifire] 🔐 my-app — fix-login-bug
  Bash: npm test
  Run the test suite
```

Finished response:

```text
[notifire] ✅ my-app — fix-login-bug
  Done: the login bug is fixed.
```

## Adding a new engine

1. Implement `NotificationEngine.send(payload)` in `notifire/engines/<name>.py`
   (see `notifire/engines/base.py` and `payload.py`). Override `dismiss(handle)`
   if the notification can be removed once the request is resolved.
2. Register the class in `notifire/engines/__init__.py`.
3. Set `"engine": "<name>"` in the config.

## Limitations

- Action buttons don't work in fire-and-forget WinRT toasts without AUMID/COM
  registration — toasts are informational in the current version. A
  SnoreToast-based engine is planned for working buttons.
- Windows toast text color is not configurable; the emoji carries the color.
