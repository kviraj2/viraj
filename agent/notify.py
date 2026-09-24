import urllib.request

from .config import NTFY_SERVER, NTFY_TOPIC


def send_notification(message: str) -> bool:
    if not NTFY_TOPIC:
        print(f"[Notification — NTFY_TOPIC not set in .env]: {message}")
        return False
    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=message.encode(),
        method="POST",
        headers={"Title": "Viraj Agent"},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status == 200
