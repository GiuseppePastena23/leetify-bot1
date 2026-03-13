import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

import config
import database
import match_detector
import weekly_digest
from handlers import commands, players, stats, matches, menu

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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
    
    from datetime import timedelta
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
    
    scheduler.start()
    logger.info("Scheduler started")

async def post_shutdown(application: Application):
    logger.info("Bot shutting down")

async def chat_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
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
    
    application.add_handler(CommandHandler("start", commands.start_command))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("settings", commands.settings_command))
    application.add_handler(CommandHandler("ping", commands.ping_command))
    
    application.add_handler(CommandHandler("add", players.add_player_command))
    application.add_handler(CommandHandler("remove", players.remove_player_command))
    application.add_handler(CommandHandler("edit", players.edit_player_command))
    application.add_handler(CommandHandler("list", players.list_players_command))
    
    application.add_handler(CommandHandler("stats", stats.stats_command))
    application.add_handler(CommandHandler("compare", stats.compare_command))
    application.add_handler(CommandHandler("leaderboard", stats.leaderboard_command))
    application.add_handler(CommandHandler("map", stats.map_command))
    application.add_handler(CommandHandler("match", stats.match_command))
    
    application.add_handler(CommandHandler("check", matches.check_command))
    
    application.add_handler(CommandHandler("menu", menu.menu_command))
    
    application.add_handler(CallbackQueryHandler(menu.menu_callback, pattern=r"^menu_"))
    application.add_handler(CallbackQueryHandler(players.remove_callback, pattern=r"^remove_"))
    application.add_handler(CallbackQueryHandler(menu.stats_callback, pattern=r"^stats_"))
    application.add_handler(CallbackQueryHandler(menu.compare1_callback, pattern=r"^compare1_"))
    application.add_handler(CallbackQueryHandler(menu.compare2_callback, pattern=r"^compare2_"))
    application.add_handler(CallbackQueryHandler(menu.map_callback, pattern=r"^map_"))
    application.add_handler(CallbackQueryHandler(menu.match_list_callback, pattern=r"^match_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(menu.match_detail_callback, pattern=r"^mdetail_"))
    application.add_handler(CallbackQueryHandler(menu.ai_analysis_callback, pattern=r"^ai_"))
    
    application.add_handler(CallbackQueryHandler(stats.stats_callback, pattern=r"^stats_"))
    application.add_handler(CallbackQueryHandler(stats.compare_callback1, pattern=r"^compare1_"))
    application.add_handler(CallbackQueryHandler(stats.compare_callback2, pattern=r"^compare2_"))
    application.add_handler(CallbackQueryHandler(stats.map_callback, pattern=r"^map_"))
    application.add_handler(CallbackQueryHandler(stats.match_callback, pattern=r"^match_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(stats.match_detail_callback, pattern=r"^matchdetail_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message_handler))
    
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
