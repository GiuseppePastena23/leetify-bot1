import logging
from datetime import datetime, timedelta
import database
import formatters
import config

logger = logging.getLogger(__name__)

async def send_weekly_digest(bot):
    if not config.CHAT_ID:
        logger.error("CHAT_ID not configured")
        return
    
    week_start = database.get_week_start()
    stats = database.get_weekly_stats(week_start)
    
    digest = formatters.format_weekly_digest(stats, week_start)
    
    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            text=digest,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Sent weekly digest to {config.CHAT_ID}")
    except Exception as e:
        logger.error(f"Failed to send weekly digest: {e}")

def get_next_digest_time():
    now = datetime.now()
    days_ahead = config.WEEKLY_DIGEST_DAY - now.weekday()
    
    if days_ahead <= 0:
        days_ahead += 7
    
    next_digest = now.replace(
        hour=config.WEEKLY_DIGEST_HOUR,
        minute=0,
        second=0,
        microsecond=0
    ) + timedelta(days=days_ahead)
    
    return next_digest
