import json
import urllib.request
from datetime import datetime, timedelta, timezone

import msal

from .config import DATA_DIR, MS_CLIENT_ID, MS_TENANT_ID

TOKEN_CACHE_PATH = DATA_DIR / "ms_token_cache.json"
SCOPES = ["Calendars.Read"]
GRAPH = "https://graph.microsoft.com/v1.0"


def _get_token() -> str:
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text())

    app = msal.PublicClientApplication(
        MS_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{MS_TENANT_ID}",
        token_cache=cache,
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            TOKEN_CACHE_PATH.write_text(cache.serialize())
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=SCOPES)
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Auth failed: {result.get('error_description', result)}")

    TOKEN_CACHE_PATH.write_text(cache.serialize())
    return result["access_token"]


def _graph(path: str, token: str) -> dict:
    req = urllib.request.Request(
        f"{GRAPH}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_upcoming_events(days: int = 7) -> list[dict]:
    if not MS_CLIENT_ID:
        return []

    token = _get_token()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    data = _graph(
        f"/me/calendarview"
        f"?startDateTime={now.isoformat()}"
        f"&endDateTime={end.isoformat()}"
        f"&$orderby=start/dateTime"
        f"&$top=25",
        token,
    )

    events = []
    for e in data.get("value", []):
        start_str = e["start"]["dateTime"]
        try:
            start = datetime.fromisoformat(start_str.rstrip("0").rstrip(".") or start_str)
        except ValueError:
            start = None
        events.append({
            "subject": e.get("subject", "(no subject)"),
            "start": start,
            "location": e.get("location", {}).get("displayName", ""),
            "is_online": e.get("isOnlineMeeting", False),
        })
    return events


def auth():
    """Trigger device-code auth flow and cache the token."""
    _get_token()
