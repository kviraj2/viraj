import signal
import sys
import time

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .ai import generate_morning_brief
from .config import MORNING_BRIEF_HOUR, MORNING_BRIEF_MINUTE, TIMEZONE
from .notify import send_notification
from .reminders import get_pending_reminders, mark_reminder_sent


def _check_reminders():
    for reminder in get_pending_reminders():
        send_notification(f"Reminder: {reminder['title']}")
        mark_reminder_sent(reminder["id"])


def _send_morning_brief():
    send_notification(generate_morning_brief())


def start_daemon():
    tz = pytz.timezone(TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)

    scheduler.add_job(
        _send_morning_brief,
        CronTrigger(hour=MORNING_BRIEF_HOUR, minute=MORNING_BRIEF_MINUTE, timezone=tz),
        id="morning_brief",
    )
    scheduler.add_job(_check_reminders, "interval", minutes=1, id="check_reminders")

    scheduler.start()
    print(
        f"Daemon running. Morning brief at {MORNING_BRIEF_HOUR:02d}:{MORNING_BRIEF_MINUTE:02d} "
        f"({TIMEZONE}). Ctrl+C to stop."
    )

    def _shutdown(signum, frame):
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
