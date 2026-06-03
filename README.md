# cc-wsl-to-ps-notify

Нативные Windows-уведомления для Claude Code, запущенного в WSL2. Тост всплывает,
когда сессия **остановилась на запросе разрешения** или **завершила ответ** — удобно,
если окно терминала свёрнуто.

В уведомлении: акцентное эмодзи (цвет — по типу), имя рабочей директории, заголовок
сессии, что именно запрашивается, и сопровождающий текст Claude.

## Как это работает

Хуки Claude Code запускают `notify.py` (в WSL). Скрипт читает JSON события из stdin,
собирает данные и через подключаемый движок показывает тост на стороне Windows.

| Хук | Когда | Эмодзи |
|---|---|---|
| `PermissionRequest` | Claude ждёт подтверждения; видно инструмент и аргументы | 🔐 |
| `Stop` | Claude закончил отвечать; в теле — итоговый ответ | ✅ |

Доступные движки: **WinRT** (`windows/toast.ps1` через `powershell.exe`, без зависимостей,
по умолчанию) и **Telegram** (отправка через Bot API). Поле `engine` принимает имя одного
движка или список — тогда уведомление уходит во все сразу (например, тост на ПК и
сообщение в Telegram на телефон).

## Требования

- WSL2 с работающим Windows-interop (`powershell.exe` доступен из WSL).
- `python3` в WSL.
- Windows PowerShell 5.1+ (есть в Windows по умолчанию).

## Установка

```bash
./install.sh
```

Скрипт идемпотентно добавляет хуки `PermissionRequest` и `Stop` в
`~/.claude/settings.json` с абсолютным путём к `notify.py` (существующие хуки не
трогает). После установки перезапустите сессии Claude Code; проверить — командой
`/hooks`.

## Конфигурация

Без файла конфигурации используются значения по умолчанию. Чтобы переопределить —
скопируйте `config.example.json` в одно из мест (в порядке приоритета):

1. путь из переменной `CCNOTIFY_CONFIG`;
2. `~/.config/cc-wsl-notify/config.json`;
3. `config.json` в корне репозитория.

Поля: `engine` (строка или список), `events` (включение типов), `types` (эмодзи/акцент),
`max_body_chars`, `winrt.app_id`, `winrt.sound`, `telegram.bot_token`, `telegram.chat_id`.

По умолчанию тосты подписаны «Windows PowerShell» (AUMID PowerShell). Брендирование
под «Claude Code» — это отдельный ярлык со своим AppUserModelID, путь к которому
прописывается в `winrt.app_id`.

### Telegram

Включается через `engine`: `"telegram"` (только Telegram) или `["winrt", "telegram"]`
(тост и Telegram вместе). Токен бота и chat_id берутся из `telegram.bot_token` /
`telegram.chat_id` либо из переменных окружения `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.

Секреты держите вне репозитория — в `~/.config/cc-wsl-notify/config.json` (`chmod 600`).
В корне репозитория `config.json` добавлен в `.gitignore`.

## Добавление нового движка

1. Реализуйте `NotificationEngine.send(payload)` в `ccnotify/engines/<name>.py`
   (см. `ccnotify/engines/base.py` и `payload.py`).
2. Зарегистрируйте класс в `ccnotify/engines/__init__.py`.
3. Укажите `"engine": "<name>"` в конфиге.

## Ограничения

- Кнопки действий в WinRT fire-and-forget не работают без регистрации AUMID/COM —
  в текущей версии тосты информационные. Для рабочих кнопок планируется движок на
  SnoreToast.
- Цвет текста тоста Windows не настраивается; цвет несёт эмодзи.

## Проверка

Сухой прогон без реального тоста (движок `console` пишет payload в stderr):

```bash
echo '{"hook_event_name":"Stop","cwd":"'"$PWD"'","last_assistant_message":"Готово."}' \
  | CCNOTIFY_ENGINE=console python3 notify.py
```

Реальный тост — тот же вызов без `CCNOTIFY_ENGINE=console`.
