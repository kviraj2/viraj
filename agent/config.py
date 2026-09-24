import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path.home() / ".viraj"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "viraj.db"

NTFY_TOPIC = os.getenv("NTFY_TOPIC")

MORNING_BRIEF_HOUR = int(os.getenv("MORNING_BRIEF_HOUR", "8"))
MORNING_BRIEF_MINUTE = int(os.getenv("MORNING_BRIEF_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")

# Ollama (local AI)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Microsoft / Outlook
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_TENANT_ID = os.getenv("MS_TENANT_ID", "common")
