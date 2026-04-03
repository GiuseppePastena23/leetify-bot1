import logging
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import config
import database
import match_detector
import weekly_digest
from handlers import commands, players, stats, matches, menu

os.makedirs(config.LOG_DIR, exist_ok=True)

log_file = os.path.join(config.LOG_DIR, "bot.log")

root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, config.LOG_LEVEL))

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=config.LOG_MAX_BYTES,
    backupCount=config.LOG_BACKUP_COUNT,
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

user_command_timestamps = {}

def is_chat_allowed(update: Update) -> bool:
    if not config.ALLOWED_GROUP_ID:
        return True
    
    chat = update.effective_chat
    if not chat:
        return False
    
    return str(chat.id) == config.ALLOWED_GROUP_ID

def is_rate_limited(user_id: int) -> bool:
    import time
    now = time.time()
    last_used = user_command_timestamps.get(user_id, 0)
    
    if now - last_used < config.RATE_LIMIT_SECONDS:
        return True
    
    user_command_timestamps[user_id] = now
    return False

def group_command_handler(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_chat_allowed(update):
            if update.message:
                await update.message.reply_text(
                    "<b>❌ Bot not available in this chat.</b>\n\n"
                    "This bot is only available in the allowed group.",
                    parse_mode="HTML"
                )
            return
        
        user_id = update.effective_user.id if update.effective_user else 0
        if is_rate_limited(user_id):
            return
        
        await func(update, context)
    return wrapper

async def post_init(application: Application):
    database.init_db()
    logger.info("Database initialized")
    
    match_detector.set_bot(application.bot)
    logger.info("Bot instance set in match_detector")
    
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        match_detector.check_and_send_reports,
        "interval",
        seconds=config.POLLING_INTERVAL,
        id="match_polling"
    )
    
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
    
    scheduler.add_job(
        lambda: weekly_digest.send_weekly_digest(application.bot),
        "cron",
        day_of_week=config.WEEKLY_DIGEST_DAY,
        hour=config.WEEKLY_DIGEST_HOUR,
        id="weekly_digest"
    )
    
    scheduler.add_job(
        lambda: weekly_digest.send_weekly_analysis(application.bot),
        "cron",
        day_of_week=config.WEEKLY_ANALYSIS_DAY,
        hour=config.WEEKLY_ANALYSIS_HOUR,
        id="weekly_analysis"
    )
    
    if config.STAT_OF_DAY_ENABLED:
        scheduler.add_job(
            lambda: stats.send_daily_stat(application.bot),
            "cron",
            hour=config.STAT_OF_DAY_HOUR,
            id="stat_of_day"
        )
    
    scheduler.start()
    logger.info("Scheduler started")
    
    if config.ADMIN_USER_ID:
        try:
            await application.bot.send_message(
                chat_id=int(config.ADMIN_USER_ID),
                text="<b>✅ Bot Started</b>\n\nLogging to file enabled.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not send startup message to admin: {e}")

async def post_shutdown(application: Application):
    logger.info("Bot shutting down - flushing logs")
    for handler in root_logger.handlers:
        handler.flush()

async def chat_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    if not is_chat_allowed(update):
        await update.message.reply_text(
            "<b>❌ Bot not available in this chat.</b>\n\n"
            "This bot is only available in the allowed group.",
            parse_mode="HTML"
        )
        return
    
    user_id = update.effective_user.id if update.effective_user else 0
    if is_rate_limited(user_id):
        return
    
    text = update.message.text.strip().lower()
    
    if text in ["menu", "open menu", "show menu"]:
        await menu.menu_command(update, context)
    elif text in ["stats", "show stats"]:
        await stats.stats_command(update, context)
    elif text in ["matches", "match history", "my matches"]:
        await stats.match_command(update, context)
    elif text in ["players", "list players", "show players"]:
        await players.list_players_command(update, context)
    elif text in ["leaderboard", "rankings", "top"]:
        await stats.leaderboard_command(update, context)
    elif text in ["help", "commands", "what can you do"]:
        await commands.help_command(update, context)
    elif text.startswith("add "):
        context.args = text[4:].split()
        await players.add_player_command(update, context)
    elif text.startswith("remove ") or text.startswith("delete "):
        cmd = "remove" if text.startswith("remove ") else "remove"
        context.args = text[len(cmd)+1:].split()
        await players.remove_player_command(update, context)
    elif text.startswith("edit "):
        context.args = text[5:].split()
        await players.edit_player_command(update, context)
    elif text.startswith("stats "):
        context.args = text[6:].split()
        await stats.stats_command(update, context)
    elif text.startswith("map "):
        context.args = text[4:].split()
        await stats.map_command(update, context)
    elif text.startswith("compare "):
        context.args = text[8:].split()
        await stats.compare_command(update, context)

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in config")
        return
    
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    application.add_handler(CommandHandler("start", group_command_handler(commands.start_command)))
    application.add_handler(CommandHandler("help", group_command_handler(commands.help_command)))
    application.add_handler(CommandHandler("settings", group_command_handler(commands.settings_command)))
    application.add_handler(CommandHandler("ping", group_command_handler(commands.ping_command)))
    
    application.add_handler(CommandHandler("add", group_command_handler(players.add_player_command)))
    application.add_handler(CommandHandler("remove", group_command_handler(players.remove_player_command)))
    application.add_handler(CommandHandler("edit", group_command_handler(players.edit_player_command)))
    application.add_handler(CommandHandler("list", group_command_handler(players.list_players_command)))
    
    application.add_handler(CommandHandler("stats", group_command_handler(stats.stats_command)))
    application.add_handler(CommandHandler("compare", group_command_handler(stats.compare_command)))
    application.add_handler(CommandHandler("leaderboard", group_command_handler(stats.leaderboard_command)))
    application.add_handler(CommandHandler("pow", group_command_handler(stats.player_of_week_command)))
    application.add_handler(CommandHandler("playerofweek", group_command_handler(stats.player_of_week_command)))
    application.add_handler(CommandHandler("team", group_command_handler(stats.team_dashboard_command)))
    application.add_handler(CommandHandler("dashboard", group_command_handler(stats.team_dashboard_command)))
    application.add_handler(CommandHandler("testanalysis", group_command_handler(stats.test_weekly_analysis_command)))
    application.add_handler(CommandHandler("teststat", group_command_handler(stats.test_stat_of_day_command)))
    application.add_handler(CommandHandler("testai", group_command_handler(stats.test_analyze_command)))
    application.add_handler(CommandHandler("statofday", group_command_handler(stats.stat_of_day_command)))
    application.add_handler(CommandHandler("randomstat", group_command_handler(stats.stat_of_day_command)))
    application.add_handler(CommandHandler("analyze", group_command_handler(stats.analyze_player_command)))
    application.add_handler(CommandHandler("ai", group_command_handler(stats.analyze_player_command)))
    application.add_handler(CommandHandler("myteam", group_command_handler(stats.myteam_command)))
    application.add_handler(CommandHandler("team", group_command_handler(stats.myteam_command)))
    application.add_handler(CommandHandler("map", group_command_handler(stats.map_command)))
    application.add_handler(CommandHandler("match", group_command_handler(stats.match_command)))
    
    application.add_handler(CommandHandler("check", group_command_handler(matches.check_command)))
    
    application.add_handler(CommandHandler("menu", group_command_handler(menu.menu_command)))
    
    application.add_handler(CallbackQueryHandler(menu.menu_callback, pattern=r"^menu_"))
    application.add_handler(CallbackQueryHandler(players.remove_callback, pattern=r"^remove_"))
    application.add_handler(CallbackQueryHandler(menu.stats_callback, pattern=r"^stats_"))
    application.add_handler(CallbackQueryHandler(menu.compare1_callback, pattern=r"^compare1_"))
    application.add_handler(CallbackQueryHandler(menu.compare2_callback, pattern=r"^compare2_"))
    application.add_handler(CallbackQueryHandler(stats.ai_profile_callback, pattern=r"^ai_profile_"))
    application.add_handler(CallbackQueryHandler(menu.ai_analysis_callback, pattern=r"^ai_[0-9]+_"))
    application.add_handler(CallbackQueryHandler(stats.team_callback, pattern=r"^team_"))
    application.add_handler(CallbackQueryHandler(menu.map_callback, pattern=r"^map_"))
    application.add_handler(CallbackQueryHandler(menu.match_list_callback, pattern=r"^match_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(menu.match_detail_callback, pattern=r"^mdetail_"))
    application.add_handler(CallbackQueryHandler(menu.match_detail_callback, pattern=r"^matchdetail_"))
    
    application.add_handler(CallbackQueryHandler(stats.stats_callback, pattern=r"^stats_"))
    application.add_handler(CallbackQueryHandler(stats.compare_callback1, pattern=r"^compare1_"))
    application.add_handler(CallbackQueryHandler(stats.compare_callback2, pattern=r"^compare2_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message_handler))
    
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
