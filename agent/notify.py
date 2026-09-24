import urllib.request
from .config import NTFY_TOPIC


def send_notification(message: str, title: str = "bestie") -> bool:
    if not NTFY_TOPIC:
        print(f"[Notify — NTFY_TOPIC not set]: {message}")
        return False
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode(),
        headers={"Title": title},
    )
    urllib.request.urlopen(req, timeout=10)
    return True
