from .tasks import list_tasks, get_due_today
from .reminders import list_reminders
from .config import MS_CLIENT_ID


def generate_morning_brief() -> str:
    tasks = list_tasks("pending")
    due_today = get_due_today()
    upcoming = list_reminders()

    lines = ["Good morning! Here's your briefing:"]

    if due_today:
        lines.append(f"\n{len(due_today)} task(s) due today:")
        for t in due_today:
            lines.append(f"  - {t['title']}")
    else:
        lines.append("\nNo tasks due today.")

    other = len(tasks) - len(due_today)
    if other > 0:
        lines.append(f"{other} other pending task(s).")

    if upcoming:
        lines.append("\nUpcoming reminders:")
        for r in upcoming[:3]:
            lines.append(f"  - {r['title']} at {r['fire_at']}")

    if MS_CLIENT_ID:
        try:
            from .outlook import get_upcoming_events
            events = get_upcoming_events(days=1)
            if events:
                lines.append("\nToday's calendar:")
                for e in events:
                    when = e["start"].strftime("%H:%M") if e["start"] else "?"
                    lines.append(f"  - {when} {e['subject']}")
        except Exception:
            pass

        try:
            from .outlook import get_recent_emails
            emails = get_recent_emails(hours=24, max_results=5)
            if emails:
                lines.append(f"\n{len(emails)} unread email(s):")
                for e in emails:
                    lines.append(f"  - {e['from']}: {e['subject']}")
        except Exception:
            pass

    return "\n".join(lines)
