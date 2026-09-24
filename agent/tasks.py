from datetime import datetime
from .db import get_conn


def add_task(title, priority="medium", due_date=None):
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, priority, due_date) VALUES (?, ?, ?)",
            (title, priority, due_date),
        )
        return cursor.lastrowid


def list_tasks(status="pending"):
    with get_conn() as conn:
        if status == "all":
            return conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC"
            ).fetchall()
        return conn.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY due_date, priority, created_at",
            (status,),
        ).fetchall()


def complete_task(task_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'done', completed_at = datetime('now') WHERE id = ?",
            (task_id,),
        )


def delete_task(task_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def get_due_today():
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE status = 'pending' AND due_date <= ? ORDER BY priority",
            (today,),
        ).fetchall()
