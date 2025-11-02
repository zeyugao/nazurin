# Telegram Forwarder (Userbot)

Forward Telegram messages between channels/chats using your personal account via Telethon.

## Requirements
- Python 3.10 or newer
- `Telethon` and `PyYAML`

Recommended virtual environment setup:
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Prepare credentials
1. 前往 <https://my.telegram.org> → `API development tools` → 建立應用程式，取得 `api_id` 與 `api_hash`。
2. 使用 Telethon 產生 `session_string`（只需做一次）：
   ```bash
   python - <<'PY'
   from telethon.sync import TelegramClient
   from telethon.sessions import StringSession

   api_id = 123456  # 改成你的 api_id
   api_hash = "0123456789abcdef0123456789abcdef"  # 改成你的 api_hash

   with TelegramClient(StringSession(), api_id, api_hash) as client:
       print("Session string:", client.session.save())
   PY
   ```
   跟著指示登入（會發送簡訊/Telegram 密碼），最後將輸出的 session string 貼到設定檔。
   若不想使用 string session，也可以在設定檔填 `session_file`，程式會使用本機檔案保存。

> 使用 userbot 代表你將以個人帳號操作，請留意安全性與 Telegram 使用條款。

## Configuration
1. Copy `config.example.yaml` to `config.yaml`.
2. 填入 `api_id`、`api_hash`、`session_string`（或 `session_file`）。
3. 在 `watch_list` 中新增轉發規則，例如：
   ```yaml
   watch_list:
     - sources:
         - "https://t.me/SugarPic/71831"
         - "@AnotherChannel"
       forward_to:
         - "@MyForwardChannel"
         - 123456789
       include_service_messages: false
     - source: -1002222333344
       forward_to:
         - 987654321
   ```
   - `sources`：要監控的頻道/群組/聊天，可用數字 ID、`@username` 或 `t.me/...` 連結。支援 `https://t.me/c/<internal_id>/...`。
   - `forward_to`：轉發目的地列表，格式相同。
   - `include_service_messages`：設為 `true` 時連服務訊息（加入群組、置頂等）也會轉發。
   - 仍支援單一 `source` 欄位作為簡寫。

## Run
```bash
python forwarder.py --config config.yaml
```

- `--config` 可省略（預設讀取 `config.yaml`）。
- 確認帳號已加入/訂閱欲監控的頻道，否則看不到貼文。
- 若目的地也是你管理的頻道，請確保帳號有發文權限，避免轉發失敗。
