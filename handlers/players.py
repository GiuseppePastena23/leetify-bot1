from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database
import leetify_client
import formatters

async def add_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        keyboard = [[InlineKeyboardButton("➕ Add Player", callback_data="menu_add")]]
        await update.message.reply_text(
            "<b>Usage: /add &lt;leetify_id_or_url&gt;</b>\n\n"
            "Example: <code>/add 76561198157232800</code>\n"
            "Example: <code>/add https://leetify.com/profile/76561198157232800</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return
    
    input_str = " ".join(context.args)
    client = leetify_client.client
    
    leetify_id = client.extract_leetify_id(input_str)
    if not leetify_id:
        await update.message.reply_text(
            "<b>❌ Invalid Leetify ID or URL</b>\n\n"
            "Please provide a valid Steam ID or Leetify profile URL.",
            parse_mode="HTML"
        )
        return
    
    profile = client.get_player_profile(leetify_id)
    if not profile or "error" in profile:
        error_msg = profile.get("message", "") if profile else ""
        await update.message.reply_text(
            f"<b>❌ Player not found on Leetify</b>\n\n"
            f"This could mean:\n"
            f"• The profile is set to private\n"
            f"• The Steam ID is incorrect\n"
            f"• The player has no matches on Leetify\n\n"
            f"<i>Try opening the profile in your browser to verify it exists.</i>",
            parse_mode="HTML"
        )
        return
    
    name = profile.get("name", "Unknown")
    steam_id = profile.get("steamId", "")
    
    if database.player_exists(leetify_id):
        link = f"https://leetify.com/profile/{leetify_id}"
        await update.message.reply_text(
            f"<b>⚠️ Already Tracking</b>\n\n"
            f"<a href='{link}'>{name}</a> is already being tracked.",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return
    
    success = database.add_player(leetify_id, steam_id, name)
    if success:
        link = f"https://leetify.com/profile/{leetify_id}"
        await update.message.reply_text(
            f"<b>✅ Player Added!</b>\n\n"
            f"<a href='{link}'>{name}</a> is now being tracked.\n\n"
            f"<i>Use /menu to browse stats!</i>",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text("<b>❌ Failed to add player.</b>", parse_mode="HTML")

async def remove_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        players = database.get_all_players()
        if not players:
            await update.message.reply_text("<b>No players tracked yet.</b>", parse_mode="HTML")
            return
        
        keyboard = []
        for p in players:
            keyboard.append([InlineKeyboardButton(
                f"❌ {p['name']}", 
                callback_data=f"remove_{p['leetify_id']}"
            )])
        
        await update.message.reply_text(
            "<b>Select a player to remove:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return
    
    name = " ".join(context.args)
    player = database.get_player_by_name(name)
    
    if not player:
        await update.message.reply_text(
            f"<b>❌ Player '{name}' not found.</b>\n\n"
            f"Use /list to see all tracked players.",
            parse_mode="HTML"
        )
        return
    
    success = database.remove_player(player["leetify_id"])
    if success:
        await update.message.reply_text(
            f"<b>✅ Removed {player['name']}</b> from tracked players.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("<b>❌ Failed to remove player.</b>", parse_mode="HTML")

async def edit_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "<b>Usage: /edit &lt;old_name&gt; &lt;new_name&gt;</b>\n\n"
            "Example: <code>/edit Player1 Nick</code>",
            parse_mode="HTML"
        )
        return
    
    old_name = context.args[0]
    new_name = " ".join(context.args[1:])
    
    player = database.get_player_by_name(old_name)
    if not player:
        await update.message.reply_text(
            f"<b>❌ Player '{old_name}' not found.</b>",
            parse_mode="HTML"
        )
        return
    
    success = database.update_player_name(player["leetify_id"], new_name)
    if success:
        await update.message.reply_text(
            f"<b>✅ Renamed to {new_name}</b>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("<b>❌ Failed to rename player.</b>", parse_mode="HTML")

async def list_players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    await update.message.reply_text(
        formatters.format_player_list(players),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def remove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    leetify_id = query.data.replace("remove_", "")
    player = database.get_player_by_id(leetify_id)
    
    if not player:
        await query.edit_message_text("<b>❌ Player not found.</b>", parse_mode="HTML")
        return
    
    success = database.remove_player(leetify_id)
    if success:
        await query.edit_message_text(
            f"<b>✅ Removed {player['name']}</b> from tracked players.",
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text("<b>❌ Failed to remove player.</b>", parse_mode="HTML")
