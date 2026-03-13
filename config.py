import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
LEETIFY_API_KEY = os.getenv("LEETIFY_API_KEY", "")
FACEIT_API_KEY = os.getenv("FACEIT_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CHAT_ID = os.getenv("CHAT_ID", "")
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "300"))
WEEKLY_DIGEST_DAY = int(os.getenv("WEEKLY_DIGEST_DAY", "6"))
WEEKLY_DIGEST_HOUR = int(os.getenv("WEEKLY_DIGEST_HOUR", "20"))

BASE_URL = "https://api-public.cs-prod.leetify.com"
FACEIT_BASE_URL = "https://open.faceit.com/data/v1"

HEADERS = {
    "Authorization": f"Bearer {LEETIFY_API_KEY}",
    "Accept": "application/json"
}

FACEIT_HEADERS = {
    "Authorization": f"Bearer {FACEIT_API_KEY}",
    "Accept": "application/json"
}
