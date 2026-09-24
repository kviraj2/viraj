import json
import urllib.request
from urllib.error import URLError

from .bot import _respond
from .config import DATA_DIR, TELEGRAM_TOKEN

API_BASE = "https://api.telegram.org/bot"
CHAT_ID_FILE = DATA_DIR / "telegram_chat_id"
OFFSET_FILE = DATA_DIR / "telegram_offset"


def _api(method: str, **params) -> dict:
    url = f"{API_BASE}{TELEGRAM_TOKEN}/{method}"
    data = json.dumps(params).encode() if params else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def send_message(chat_id: int, text: str):
    _api("sendMessage", chat_id=chat_id, text=text[:4096])


def _get_offset() -> int:
    return int(OFFSET_FILE.read_text().strip()) if OFFSET_FILE.exists() else 0


def _set_offset(offset: int):
    OFFSET_FILE.write_text(str(offset))


def _get_chat_id() -> int | None:
    return int(CHAT_ID_FILE.read_text().strip()) if CHAT_ID_FILE.exists() else None


def bot_tick():
    if not TELEGRAM_TOKEN:
        return

    offset = _get_offset()
    try:
        result = _api("getUpdates", offset=offset, timeout=0)
    except URLError:
        return

    for update in result.get("result", []):
        update_id = update["update_id"]
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            _set_offset(update_id + 1)
            continue

        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()

        # Auto-save the first chat that messages the bot (that's you)
        saved_id = _get_chat_id()
        if saved_id is None:
            CHAT_ID_FILE.write_text(str(chat_id))
            saved_id = chat_id

        # Ignore anyone who isn't the owner
        if chat_id != saved_id:
            _set_offset(update_id + 1)
            continue

        if text:
            try:
                response = _respond(text)
                send_message(chat_id, response)
            except Exception as e:
                send_message(chat_id, f"Error: {e}")

        _set_offset(update_id + 1)
