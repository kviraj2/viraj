from .tasks import list_tasks, get_due_today
from .reminders import list_reminders


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

    return "\n".join(lines)
