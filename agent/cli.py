from datetime import datetime

import click
from rich.console import Console
from rich.table import Table

from .ai import ask_assistant, generate_morning_brief
from .db import init_db
from .reminders import add_reminder, delete_reminder, list_reminders
from .scheduler import start_daemon
from .sms import send_sms
from .tasks import add_task, complete_task, delete_task, list_tasks

console = Console()

PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}


@click.group()
def cli():
    """Viraj — personal life agent."""
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


# ── AI ────────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("question", nargs=-1, required=True)
def ask(question):
    """Ask the AI assistant a question."""
    q = " ".join(question)
    console.print(f"[dim]{q}[/dim]\n")
    answer = ask_assistant(q)
    console.print(f"[bold cyan]Assistant:[/bold cyan] {answer}")


# ── Daemon ────────────────────────────────────────────────────────────────────

@cli.command()
def start():
    """Start the background daemon (reminders + morning brief)."""
    start_daemon()


# ── Manual triggers ───────────────────────────────────────────────────────────

@cli.command()
def brief():
    """Generate and send the morning brief now."""
    msg = generate_morning_brief()
    console.print(msg)
    sent = send_sms(msg)
    if sent:
        console.print("\n[green]Brief sent via SMS.[/green]")


@cli.command("test-sms")
def test_sms():
    """Send a test SMS to verify Twilio is configured."""
    sent = send_sms("Viraj agent is online and working!")
    if sent:
        console.print("[green]Test SMS sent![/green]")
    else:
        console.print("[yellow]SMS not sent — check your .env file.[/yellow]")
