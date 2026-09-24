from datetime import datetime

import click
from rich.console import Console
from rich.table import Table

from .ai import generate_morning_brief
from .db import init_db
from .messages import get_unreplied, send_imessage, _from_apple_ns
from .notify import send_notification
from .ollama_ai import classify_spam, draft_reply
from .outlook import auth as outlook_auth, get_upcoming_events
from .reminders import add_reminder, delete_reminder, list_reminders
from .scheduler import start_daemon
from .tasks import add_task, complete_task, delete_task, list_tasks

console = Console()

PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}


@click.group()
def cli():
    """Bestie — personal life agent."""
    init_db()


# ── Tasks ──────────────────────────────────────────────────────────────────────

@cli.group()
def task():
    """Manage tasks."""


@task.command("add")
@click.argument("title")
@click.option("--priority", "-p", type=click.Choice(["low", "medium", "high"]), default="medium")
@click.option("--due", "-d", default=None, help="Due date (YYYY-MM-DD)")
def task_add(title, priority, due):
    """Add a new task."""
    if due:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD.[/red]")
            return
    task_id = add_task(title, priority, due)
    console.print(f"[green]Task #{task_id} added:[/green] {title}")


@task.command("list")
@click.option(
    "--filter", "-f", "status",
    type=click.Choice(["pending", "done", "all"]),
    default="pending",
)
def task_list(status):
    """List tasks."""
    tasks = list_tasks(status)
    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return
    table = Table(title=f"Tasks ({status})", show_lines=False)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Priority", width=8)
    table.add_column("Title")
    table.add_column("Due", width=12)
    table.add_column("Status", width=10)
    for t in tasks:
        color = PRIORITY_COLORS.get(t["priority"], "white")
        table.add_row(
            str(t["id"]),
            f"[{color}]{t['priority']}[/{color}]",
            t["title"],
            t["due_date"] or "-",
            t["status"],
        )
    console.print(table)


@task.command("done")
@click.argument("task_id", type=int)
def task_done(task_id):
    """Mark a task as done."""
    complete_task(task_id)
    console.print(f"[green]Task #{task_id} marked as done.[/green]")


@task.command("delete")
@click.argument("task_id", type=int)
def task_delete(task_id):
    """Delete a task."""
    delete_task(task_id)
    console.print(f"[red]Task #{task_id} deleted.[/red]")


# ── Reminders ─────────────────────────────────────────────────────────────────

@cli.group()
def remind():
    """Manage reminders."""


@remind.command("add")
@click.argument("title")
@click.option("--at", "-a", required=True, help="When to fire (YYYY-MM-DD HH:MM)")
def remind_add(title, at):
    """Add a reminder."""
    try:
        datetime.strptime(at, "%Y-%m-%d %H:%M")
    except ValueError:
        console.print("[red]Invalid format. Use: YYYY-MM-DD HH:MM[/red]")
        return
    reminder_id = add_reminder(title, at)
    console.print(f"[green]Reminder #{reminder_id} set:[/green] {title} at {at}")


@remind.command("list")
def remind_list():
    """List upcoming reminders."""
    reminders = list_reminders()
    if not reminders:
        console.print("[dim]No upcoming reminders.[/dim]")
        return
    table = Table(title="Upcoming Reminders")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Title")
    table.add_column("When", width=18)
    for r in reminders:
        table.add_row(str(r["id"]), r["title"], r["fire_at"])
    console.print(table)


@remind.command("delete")
@click.argument("reminder_id", type=int)
def remind_delete(reminder_id):
    """Delete a reminder."""
    delete_reminder(reminder_id)
    console.print(f"[red]Reminder #{reminder_id} deleted.[/red]")


# ── Notifications ─────────────────────────────────────────────────────────────

@cli.command()
def brief():
    """Generate and send the morning brief now."""
    msg = generate_morning_brief()
    console.print(msg)
    sent = send_notification(msg, title="Morning Brief")
    if sent:
        console.print("\n[green]Brief sent via ntfy.[/green]")


@cli.command("test-notify")
def test_notify():
    """Send a test notification to verify ntfy is configured."""
    sent = send_notification("Bestie is online and working!", title="Test")
    if sent:
        console.print("[green]Test notification sent![/green]")
    else:
        console.print("[yellow]Not sent — set NTFY_TOPIC in your .env file.[/yellow]")


# ── Inbox (iMessage) ──────────────────────────────────────────────────────────

@cli.group()
def inbox():
    """Manage iMessage inbox."""


@inbox.command("list")
@click.option("--hours", "-h", default=48, show_default=True, help="Look back N hours")
def inbox_list(hours):
    """Show unreplied messages."""
    try:
        msgs = get_unreplied(since_hours=hours)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        return
    if not msgs:
        console.print("[dim]No unreplied messages.[/dim]")
        return
    table = Table(title=f"Unreplied messages (last {hours}h)")
    table.add_column("From", style="cyan")
    table.add_column("Message")
    table.add_column("When", width=20)
    for m in msgs:
        when = _from_apple_ns(m["date"]).strftime("%Y-%m-%d %H:%M")
        table.add_row(
            m["display_name"] or m["sender"] or "?",
            (m["text"] or "")[:80],
            when,
        )
    console.print(table)


@inbox.command("process")
@click.option("--hours", "-h", default=48, show_default=True, help="Look back N hours")
def inbox_process(hours):
    """AI reviews unreplied messages: marks spam, drafts replies."""
    try:
        msgs = get_unreplied(since_hours=hours)
    except (FileNotFoundError, RuntimeError) as e:
        console.print(f"[red]{e}[/red]")
        return
    if not msgs:
        console.print("[dim]No unreplied messages.[/dim]")
        return

    for m in msgs:
        name = m["display_name"] or m["sender"] or "?"
        text = m["text"] or ""
        sender = m["sender"] or ""
        console.rule(f"[cyan]{name}[/cyan]")
        console.print(f"[dim]{text}[/dim]\n")

        try:
            spam = classify_spam(sender, text)
        except RuntimeError as e:
            console.print(f"[yellow]Ollama error: {e}[/yellow]")
            continue

        if spam:
            console.print("[red]Classified as spam.[/red]")
            if click.confirm("Skip (mark as ignored)?", default=True):
                continue

        try:
            draft = draft_reply(name, text)
        except RuntimeError as e:
            console.print(f"[yellow]Could not draft reply: {e}[/yellow]")
            continue

        console.print(f"\n[bold]Draft reply:[/bold] {draft}\n")
        choice = click.prompt("Action", type=click.Choice(["send", "edit", "skip"]), default="skip")

        if choice == "skip":
            continue
        elif choice == "edit":
            edited = click.edit(draft)
            if edited:
                draft = edited.strip()

        if choice in ("send", "edit"):
            if send_imessage(sender, draft):
                console.print(f"[green]Sent.[/green]")
            else:
                console.print(f"[red]Failed to send — check Messages.app permissions.[/red]")


# ── Calendar (Outlook) ────────────────────────────────────────────────────────

@cli.group()
def calendar():
    """Outlook calendar."""


@calendar.command("auth")
def calendar_auth():
    """Authenticate with Microsoft (run once)."""
    from .config import MS_CLIENT_ID
    if not MS_CLIENT_ID:
        console.print(
            "[yellow]MS_CLIENT_ID not set.[/yellow]\n\n"
            "To set up Outlook access:\n"
            "  1. Go to portal.azure.com → App registrations → New registration\n"
            "  2. Name it 'bestie', set account type to 'Personal Microsoft accounts only'\n"
            "  3. Under Authentication → Add platform → Mobile/desktop → enable https://login.microsoftonline.com/common/oauth2/nativeclient\n"
            "  4. Copy the Application (client) ID and add to .env:\n"
            "     MS_CLIENT_ID=<your-client-id>"
        )
        return
    try:
        outlook_auth()
        console.print("[green]Authenticated successfully.[/green]")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")


@calendar.command("show")
@click.option("--days", "-d", default=7, show_default=True, help="Days ahead to show")
def calendar_show(days):
    """Show upcoming Outlook calendar events."""
    from .config import MS_CLIENT_ID
    if not MS_CLIENT_ID:
        console.print("[yellow]Run `bestie calendar auth` first to connect Outlook.[/yellow]")
        return
    try:
        events = get_upcoming_events(days=days)
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        return
    if not events:
        console.print("[dim]No upcoming events.[/dim]")
        return
    table = Table(title=f"Next {days} days")
    table.add_column("When", width=18)
    table.add_column("Event")
    table.add_column("Location")
    for e in events:
        when = e["start"].strftime("%a %b %d %H:%M") if e["start"] else "?"
        loc = e["location"] or ("[blue]Online[/blue]" if e["is_online"] else "")
        table.add_row(when, e["subject"], loc)
    console.print(table)


# ── Daemon ────────────────────────────────────────────────────────────────────

@cli.command()
def start():
    """Start the background daemon (reminders + morning brief)."""
    start_daemon()
