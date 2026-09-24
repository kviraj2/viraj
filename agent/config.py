import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path.home() / ".viraj"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "viraj.db"

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
USER_PHONE = os.getenv("USER_PHONE")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

MORNING_BRIEF_HOUR = int(os.getenv("MORNING_BRIEF_HOUR", "8"))
MORNING_BRIEF_MINUTE = int(os.getenv("MORNING_BRIEF_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
