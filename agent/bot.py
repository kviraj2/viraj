import re

from .ai import generate_morning_brief
from .reminders import add_reminder, list_reminders
from .tasks import add_task, complete_task, list_tasks



def _respond(text: str) -> str:
    original = text.strip()
    lower = original.lower()

    # brief
    if lower in ("brief", "briefing", "morning brief", "gm"):
        return generate_morning_brief()

    # tasks
    if lower in ("tasks", "task list", "list tasks", "todo", "todos"):
        tasks = list_tasks("pending")
        if not tasks:
            return "No pending tasks!"
        lines = [f"Pending tasks ({len(tasks)}):"]
        for t in tasks:
            due = f" · due {t['due_date']}" if t["due_date"] else ""
            lines.append(f"  [{t['priority'][0].upper()}] #{t['id']} {t['title']}{due}")
        return "\n".join(lines)

    # done <id>
    m = re.match(r"^done\s+(\d+)$", lower)
    if m:
        complete_task(int(m.group(1)))
        return f"Task #{m.group(1)} done ✓"

    # task: <title>  or  add task <title>
    m = re.match(r"^(?:add\s+)?task[:\s]+(.+)$", original, re.IGNORECASE)
    if m:
        title = m.group(1).strip()
        task_id = add_task(title)
        return f"Task added: {title} (#{task_id})"

    # reminders
    if lower in ("reminders", "remind list", "list reminders"):
        reminders = list_reminders()
        if not reminders:
            return "No upcoming reminders."
        lines = [f"Upcoming reminders ({len(reminders)}):"]
        for r in reminders:
            lines.append(f"  {r['fire_at']} — {r['title']}")
        return "\n".join(lines)

    # remind: <title> at YYYY-MM-DD HH:MM
    m = re.match(
        r"^remind(?:er)?[:\s]+(.+?)\s+at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})$",
        original, re.IGNORECASE,
    )
    if m:
        title, fire_at = m.group(1).strip(), m.group(2)
        r_id = add_reminder(title, fire_at)
        return f"Reminder set: {title} at {fire_at} (#{r_id})"

    # inbox
    if lower in ("inbox", "messages", "unreplied"):
        from .messages import get_unreplied
        try:
            msgs = get_unreplied(since_hours=48)
        except Exception as e:
            return f"Error reading inbox: {e}"
        if not msgs:
            return "No unreplied messages in the last 48h."
        lines = [f"Unreplied ({len(msgs)}):"]
        for msg in msgs[:5]:
            name = msg["display_name"] or msg["sender"] or "?"
            preview = (msg["text"] or "")[:60]
            lines.append(f"  {name}: {preview}")
        return "\n".join(lines)

    # help
    if lower in ("help", "?", "commands"):
        return (
            "Commands:\n"
            "  brief — morning briefing\n"
            "  tasks — list pending tasks\n"
            "  task: <title> — add a task\n"
            "  done <id> — complete a task\n"
            "  reminders — list reminders\n"
            "  remind: <title> at YYYY-MM-DD HH:MM\n"
            "  inbox — unreplied messages"
        )

    # Fallback: Ollama with strict grounding — only data we provide
    try:
        from .ollama_ai import _chat
        tasks = list_tasks("pending")
        reminders = list_reminders()

        task_lines = "\n".join(
            f"- #{t['id']} [{t['priority']}] {t['title']}"
            + (f" (due {t['due_date']})" if t["due_date"] else "")
            for t in tasks[:15]
        ) or "none"

        reminder_lines = "\n".join(
            f"- {r['fire_at']}: {r['title']}" for r in reminders[:10]
        ) or "none"

        system = f"""You are Viraj's personal assistant. Be concise (2-3 sentences max).

IMPORTANT: You ONLY know what is listed below. Do NOT invent, guess, or mention \
any meetings, events, calendar items, people, or facts not explicitly listed here. \
If asked about something not in this list, say you don't have that information.

Pending tasks:
{task_lines}

Upcoming reminders:
{reminder_lines}

You do NOT have access to email, calendar, contacts, or any other data."""

        return _chat(system, original)
    except RuntimeError as e:
        return f"Didn't understand that. Type 'help' for commands.\n({e})"
