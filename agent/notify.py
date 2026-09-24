import urllib.request
from urllib.error import URLError
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
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except URLError as e:
        print(f"[Notify failed]: {e}")
        return False
