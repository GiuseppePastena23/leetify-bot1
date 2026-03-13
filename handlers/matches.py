from telegram import Update
from telegram.ext import ContextTypes
import database
import match_detector
import config

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 <b>Checking for new matches...</b>", parse_mode="HTML")
    
    try:
        new_matches = match_detector.check_for_new_matches()
        
        if not new_matches:
            await update.message.reply_text("<b>✅ No new matches found.</b>", parse_mode="HTML")
            return
        
        for match in new_matches:
            await update.message.reply_text(match, parse_mode="HTML", disable_web_page_preview=True)
        
        count = len(new_matches)
        await update.message.reply_text(f"<b>✅ Found and reported {count} new match(es).</b>", parse_mode="HTML")
    
    except Exception as e:
        await update.message.reply_text(f"<b>❌ Error checking matches:</b> {str(e)}", parse_mode="HTML")
