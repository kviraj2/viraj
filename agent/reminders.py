from .db import get_conn


def add_reminder(title, fire_at):
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO reminders (title, fire_at) VALUES (?, ?)",
            (title, fire_at),
        )
        return cursor.lastrowid


def list_reminders():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM reminders WHERE sent = 0 ORDER BY fire_at"
        ).fetchall()


def delete_reminder(reminder_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))


def get_pending_reminders():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM reminders WHERE sent = 0 AND fire_at <= datetime('now')"
        ).fetchall()


def mark_reminder_sent(reminder_id):
    with get_conn() as conn:
        conn.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
