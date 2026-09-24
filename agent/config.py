import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path.home() / ".viraj"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "viraj.db"

NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

MORNING_BRIEF_HOUR = int(os.getenv("MORNING_BRIEF_HOUR", "8"))
MORNING_BRIEF_MINUTE = int(os.getenv("MORNING_BRIEF_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
