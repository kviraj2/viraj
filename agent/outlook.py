import json
import urllib.request
from datetime import datetime, timedelta, timezone

import msal

from .config import DATA_DIR, MS_CLIENT_ID, MS_TENANT_ID

TOKEN_CACHE_PATH = DATA_DIR / "ms_token_cache.json"
SCOPES = ["Calendars.Read", "Mail.Read"]
GRAPH = "https://graph.microsoft.com/v1.0"


def _get_token() -> str:
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text())

    app = msal.PublicClientApplication(
        MS_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{MS_TENANT_ID}",
        token_cache=cache,
        # personal Microsoft accounts need the consumers endpoint
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            TOKEN_CACHE_PATH.write_text(cache.serialize())
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "error" in flow:
        raise RuntimeError(f"Device flow error: {flow.get('error_description', flow)}")
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
            start = datetime.fromisoformat(start_str[:19])
        except ValueError:
            start = None
        events.append({
            "subject": e.get("subject", "(no subject)"),
            "start": start,
            "location": e.get("location", {}).get("displayName", ""),
            "is_online": e.get("isOnlineMeeting", False),
        })
    return events


def get_recent_emails(hours: int = 24, max_results: int = 10) -> list[dict]:
    if not MS_CLIENT_ID:
        return []

    token = _get_token()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    data = _graph(
        f"/me/mailFolders/inbox/messages"
        f"?$filter=receivedDateTime ge {since} and isRead eq false"
        f"&$orderby=receivedDateTime desc"
        f"&$top={max_results}"
        f"&$select=subject,from,receivedDateTime,bodyPreview,isRead",
        token,
    )

    emails = []
    for m in data.get("value", []):
        received_str = m.get("receivedDateTime", "")
        try:
            received = datetime.fromisoformat(received_str[:19])
        except ValueError:
            received = None
        emails.append({
            "subject": m.get("subject", "(no subject)"),
            "from": m.get("from", {}).get("emailAddress", {}).get("name", "?"),
            "from_email": m.get("from", {}).get("emailAddress", {}).get("address", ""),
            "received": received,
            "preview": m.get("bodyPreview", "")[:200],
        })
    return emails


def auth():
    """Trigger device-code auth flow and cache the token."""
    _get_token()
