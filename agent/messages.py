import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

CHAT_DB = Path.home() / "Library/Messages/chat.db"
APPLE_EPOCH = datetime(2001, 1, 1)


def _conn():
    conn = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _from_apple_ns(ns: int) -> datetime:
    return APPLE_EPOCH + timedelta(seconds=ns / 1e9)


def get_unreplied(since_hours: int = 48) -> list[dict]:
    if not CHAT_DB.exists():
        raise FileNotFoundError(
            f"{CHAT_DB} not found. Grant Full Disk Access to Terminal in "
            "System Settings → Privacy & Security → Full Disk Access."
        )

    cutoff_ns = (
        datetime.now() - APPLE_EPOCH - timedelta(hours=since_hours)
    ).total_seconds() * 1e9

    with _conn() as conn:
        rows = conn.execute("""
            WITH ranked AS (
                SELECT
                    cmj.chat_id,
                    m.text,
                    m.date,
                    m.is_from_me,
                    m.handle_id,
                    ROW_NUMBER() OVER (PARTITION BY cmj.chat_id ORDER BY m.date DESC) AS rn
                FROM chat_message_join cmj
                JOIN message m ON cmj.message_id = m.rowid
                WHERE m.text IS NOT NULL AND m.date > ?
            )
            SELECT
                r.chat_id,
                c.chat_identifier,
                COALESCE(c.display_name, h.id) AS display_name,
                h.id AS sender,
                r.text,
                r.date
            FROM ranked r
            JOIN chat c ON r.chat_id = c.rowid
            LEFT JOIN handle h ON r.handle_id = h.rowid
            WHERE r.rn = 1 AND r.is_from_me = 0
            ORDER BY r.date DESC
        """, (cutoff_ns,)).fetchall()

    return [dict(r) for r in rows]


def get_messages_from(phone: str, since_ns: int) -> list[dict]:
    """Return messages received from `phone` after `since_ns` (Apple epoch ns), oldest first."""
    if not CHAT_DB.exists():
        return []
    with _conn() as conn:
        rows = conn.execute("""
            SELECT m.text, m.date, h.id AS sender
            FROM message m
            JOIN handle h ON m.handle_id = h.rowid
            WHERE h.id = ? AND m.is_from_me = 0 AND m.date > ? AND m.text IS NOT NULL
            ORDER BY m.date ASC
        """, (phone, since_ns)).fetchall()
    return [dict(r) for r in rows]


def send_imessage(recipient: str, text: str) -> bool:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Messages"
    set s to first service whose service type = iMessage
    send "{escaped}" to buddy "{recipient}" of s
end tell
'''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.returncode == 0
