from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import formatters

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Open Menu", callback_data="menu_open")],
        [InlineKeyboardButton("➕ Add Player", callback_data="menu_add")]
    ]
    
    await update.message.reply_text(
        formatters.format_welcome(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            formatters.format_help(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        formatters.format_settings(),
        parse_mode="HTML"
    )

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from leetify_client import client
    
    is_valid = client.validate_api_key()
    if is_valid:
        await update.message.reply_text(
            "<b>✅ Leetify API Connected</b>\n\nAPI key is valid and working!",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "<b>❌ API Error</b>\n\nLeetify API key is invalid or not working.",
            parse_mode="HTML"
        )
