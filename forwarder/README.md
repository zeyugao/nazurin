# Telegram Forwarder Bot

Simple Telegram bot script that monitors specified chats and forwards new messages to configured destinations.

## Requirements
- Python 3.10 or newer
- `aiogram` version 3+

Recommended virtual environment setup:
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
1. Copy `config.example.json` to `config.json`.
2. Replace `bot_token` with your bot token from @BotFather.
3. Add entries under `watch_list`, for example:
   ```json
   {
     "source": "https://t.me/SugarPic/71831",
     "forward_to": ["@MyForwardChannel", 123456789],
     "include_service_messages": false
   }
   ```
   - `source`: chat to monitor. Accepts numeric IDs (e.g. `-1001234567890`), `@username`, or a `t.me` message URL such as `https://t.me/SugarPic/71831`. Links of the form `https://t.me/c/<internal_id>/...` are also supported and will be converted automatically.
   - `forward_to`: list of destination chats, each as numeric ID, `@username`, or `t.me/...` link.
   - `include_service_messages`: set to `true` to forward service messages such as members joining a group.
4. Optional `polling.drop_pending_updates` controls whether pending updates are skipped on startup (default `true`).

> 要監控頻道貼文，請把機器人加入該頻道並提升為管理員，Telegram 才會把新貼文推送給機器人。

## Run
```bash
python forwarder.py --config config.json
```

If the configuration file is named `config.json` in the project root, the `--config` option can be omitted. The script uses long polling, so ensure the runtime environment can reach the Telegram API.
