import anthropic
from .config import ANTHROPIC_API_KEY
from .tasks import list_tasks, get_due_today
from .reminders import list_reminders


def _task_context() -> str:
    tasks = list_tasks("pending")
    due_today = get_due_today()
    lines = [f"Pending tasks ({len(tasks)} total):"]
    for t in tasks[:15]:
        due = f", due {t['due_date']}" if t["due_date"] else ""
        lines.append(f"  [{t['priority']}] {t['title']}{due}")
    if due_today:
        lines.append(f"\nTasks due today: {len(due_today)}")
    return "\n".join(lines)


def ask_assistant(question: str) -> str:
    if not ANTHROPIC_API_KEY:
        return (
            "ANTHROPIC_API_KEY is not set in your .env file. "
            "Get a key at https://console.anthropic.com — or skip this feature and just use tasks/reminders."
        )
    system = f"""You are a personal life assistant. Be concise and practical.

Current task context:
{_task_context()}"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


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
