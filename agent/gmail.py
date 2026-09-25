import email
import imaplib
from datetime import datetime, timezone

from .config import GMAIL_APP_PASSWORD, GMAIL_EMAIL

IMAP_HOST = "imap.gmail.com"


def _conn() -> imaplib.IMAP4_SSL:
    conn = imaplib.IMAP4_SSL(IMAP_HOST)
    conn.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
    return conn


def get_unread_emails(max_results: int = 10) -> list[dict]:
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        return []

    conn = _conn()
    conn.select("INBOX")
    _, data = conn.search(None, "UNSEEN")
    uids = data[0].split()
    uids = uids[-max_results:]  # most recent

    emails = []
    for uid in reversed(uids):
        _, msg_data = conn.fetch(uid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject = email.header.decode_header(msg["Subject"] or "")[0]
        subject = subject[0].decode(subject[1] or "utf-8") if isinstance(subject[0], bytes) else subject[0]

        sender = email.header.decode_header(msg["From"] or "")[0]
        sender = sender[0].decode(sender[1] or "utf-8") if isinstance(sender[0], bytes) else sender[0]

        date_str = msg["Date"] or ""
        try:
            received = email.utils.parsedate_to_datetime(date_str)
        except Exception:
            received = None

        # Get plain text body preview
        preview = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        preview = payload.decode(part.get_content_charset() or "utf-8", errors="replace")[:200]
                    break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                preview = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")[:200]

        emails.append({
            "subject": subject,
            "from": sender,
            "received": received,
            "preview": preview.strip(),
        })

    conn.logout()
    return emails
