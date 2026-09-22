"""Static settings for BlogBot. Secrets are read from .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

# All paths are resolved relative to this file, so the bot works the same
# whether it is started from cron, Task Scheduler or an interactive shell.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- General settings -------------------------------------------------------
PROMPTS_PER_RUN = 2       # Her çalıştırmada kaç prompt
SCHEDULE_TIME = "09:00"   # HH:MM formatı
TIMEZONE = "Europe/Istanbul"
LOG_LEVEL = "INFO"
OUTPUT_DIR = "output"

# --- Scrape.do --------------------------------------------------------------
API_URL = "https://api.scrape.do/plugin/chatgpt/chat"
REQUEST_TIMEOUT = 60      # seconds; a typical response takes ~23s
RETRY_DELAY = 30          # seconds between retries; failed requests are retried until they succeed

# --- Files ------------------------------------------------------------------
PROMPTS_FILE = BASE_DIR / "prompts.txt"
PROGRESS_FILE = BASE_DIR / "progress.json"
LOG_FILE = BASE_DIR / "blogbot.log"
OUTPUT_PATH = BASE_DIR / OUTPUT_DIR
RAW_OUTPUT_PATH = OUTPUT_PATH / "raw"

# --- Secrets (.env) ---------------------------------------------------------
SCRAPE_DO_TOKEN = os.getenv("SCRAPE_DO_TOKEN", "").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip()
EMAIL_TO = os.getenv("EMAIL_TO", "").strip()
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "mail.privateemail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587").strip() or 587)
