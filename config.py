import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Groq gives a free, no-credit-card API that is OpenAI-compatible.
# Get a key at https://console.groq.com/keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

DB_PATH = os.environ.get("DB_PATH", "coach.db")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is not set. Add it to your .env file locally, "
        "or as a Railway environment variable in production."
    )

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add it to your .env file locally, "
        "or as a Railway environment variable in production. "
        "Get a free key (no credit card) at https://console.groq.com/keys"
    )
