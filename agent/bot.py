import re

from .ai import generate_morning_brief
from .config import GMAIL_EMAIL, GMAIL_APP_PASSWORD, MS_CLIENT_ID
from .reminders import add_reminder, list_reminders
from .tasks import add_task, complete_task, list_tasks


def _get_calendar_lines() -> str:
    if not MS_CLIENT_ID:
        return "none (Outlook not connected)"
    try:
        from .outlook import get_upcoming_events
        events = get_upcoming_events(days=7)
        if not events:
            return "none"
        return "\n".join(
            f"- {e['start'].strftime('%a %b %d %H:%M') if e['start'] else '?'}: {e['subject']}"
            + (" [online]" if e["is_online"] else f" {e['location']}" if e["location"] else "")
            for e in events
        )
    except Exception:
        return "unavailable"


def _get_email_lines() -> str:
    lines = []
    if MS_CLIENT_ID:
        try:
            from .outlook import get_recent_emails
            for e in get_recent_emails(hours=24, max_results=5):
                lines.append(f"- [Outlook] From {e['from']}: {e['subject']} — {e['preview'][:80]}")
        except Exception:
            pass
    if GMAIL_EMAIL and GMAIL_APP_PASSWORD:
        try:
            from .gmail import get_unread_emails
            for e in get_unread_emails(max_results=5):
                lines.append(f"- [Gmail] From {e['from']}: {e['subject']} — {e['preview'][:80]}")
        except Exception:
            pass
    return "\n".join(lines) if lines else "none"


def _get_imessage_lines() -> str:
    try:
        from .messages import get_unreplied
        msgs = get_unreplied(since_hours=48)
        if not msgs:
            return "none"
        return "\n".join(
            f"- {m['display_name'] or m['sender'] or '?'}: {(m['text'] or '')[:80]}"
            for m in msgs[:10]
        )
    except Exception:
        return "unavailable"


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

    # calendar
    if lower in ("calendar", "events", "schedule", "what's on", "whats on"):
        if not MS_CLIENT_ID:
            return "Outlook not connected. Run `bestie calendar auth` on your Mac first."
        try:
            from .outlook import get_upcoming_events
            events = get_upcoming_events(days=7)
        except Exception as e:
            return f"Calendar error: {e}"
        if not events:
            return "No upcoming events in the next 7 days."
        lines = ["Upcoming events:"]
        for e in events:
            when = e["start"].strftime("%a %b %d %H:%M") if e["start"] else "?"
            loc = " [online]" if e["is_online"] else (f" · {e['location']}" if e["location"] else "")
            lines.append(f"  {when} — {e['subject']}{loc}")
        return "\n".join(lines)

    # emails (Outlook + Gmail combined)
    if lower in ("emails", "email", "mail", "unread"):
        all_emails = []
        if MS_CLIENT_ID:
            try:
                from .outlook import get_recent_emails
                for e in get_recent_emails(hours=24):
                    all_emails.append(("[Outlook]", e))
            except Exception as ex:
                all_emails.append(("[Outlook]", {"error": str(ex)}))
        if GMAIL_EMAIL and GMAIL_APP_PASSWORD:
            try:
                from .gmail import get_unread_emails
                for e in get_unread_emails(max_results=10):
                    all_emails.append(("[Gmail]", e))
            except Exception as ex:
                all_emails.append(("[Gmail]", {"error": str(ex)}))
        if not all_emails:
            return "No email accounts connected."
        lines = [f"Unread emails ({len(all_emails)}):"]
        for source, e in all_emails:
            if "error" in e:
                lines.append(f"  {source} error: {e['error']}")
                continue
            when = e["received"].strftime("%H:%M") if e.get("received") else "?"
            lines.append(f"  {source} {when} {e['from']}: {e['subject']}")
        return "\n".join(lines)

    # inbox (iMessage/SMS)
    if lower in ("inbox", "messages", "imessage", "texts", "unreplied"):
        try:
            from .messages import get_unreplied
            msgs = get_unreplied(since_hours=48)
        except Exception as e:
            return f"Error reading inbox: {e}"
        if not msgs:
            return "No unreplied iMessages/SMS in the last 48h."
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
            "  tasks — pending tasks\n"
            "  task: <title> — add a task\n"
            "  done <id> — complete a task\n"
            "  reminders — upcoming reminders\n"
            "  remind: <title> at YYYY-MM-DD HH:MM\n"
            "  calendar — Outlook events (next 7 days)\n"
            "  emails — unread Outlook emails (last 24h)\n"
            "  inbox — unreplied iMessages/SMS"
        )

    # Fallback: Ollama with full grounding — tasks, reminders, calendar, emails, iMessage
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

        calendar_lines = _get_calendar_lines()
        email_lines = _get_email_lines()
        imessage_lines = _get_imessage_lines()

        system = f"""You are Viraj's personal assistant. Be concise (2-3 sentences max).

IMPORTANT: You ONLY know what is listed below. Do NOT invent, guess, or mention \
any facts, people, or details not explicitly listed here. \
If asked about something not in this list, say you don't have that information.

Pending tasks:
{task_lines}

Upcoming reminders:
{reminder_lines}

Outlook calendar (next 7 days):
{calendar_lines}

Unread emails (last 24h):
{email_lines}

Unreplied iMessages/SMS (last 48h):
{imessage_lines}"""

        return _chat(system, original)
    except RuntimeError as e:
        return f"Didn't understand that. Type 'help' for commands.\n({e})"
