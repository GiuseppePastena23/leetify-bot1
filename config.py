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

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

WEEKLY_ANALYSIS_DAY = int(os.getenv("WEEKLY_ANALYSIS_DAY", "0"))
WEEKLY_ANALYSIS_HOUR = int(os.getenv("WEEKLY_ANALYSIS_HOUR", "18"))

STAT_OF_DAY_HOUR = int(os.getenv("STAT_OF_DAY_HOUR", "9"))
STAT_OF_DAY_ENABLED = os.getenv("STAT_OF_DAY_ENABLED", "true").lower() == "true"

ALLOWED_GROUP_ID = os.getenv("ALLOWED_GROUP_ID", "")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "2"))

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "false").lower() == "true"

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
