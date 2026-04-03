from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import config
import database
import leetify_client
import formatters

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
            InlineKeyboardButton("🎮 Matches", callback_data="menu_match")
        ],
        [
            InlineKeyboardButton("🗺️ Maps", callback_data="menu_map"),
            InlineKeyboardButton("⚔️ Compare", callback_data="menu_compare")
        ],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard"),
            InlineKeyboardButton("👥 Players", callback_data="menu_players")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_back")]]
    return InlineKeyboardMarkup(keyboard)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "<b>🎯 Leetify Bot</b>\n"
        "═" * 20 + "\n\n"
        "Track your CS2 stats and monitor your team's performance!\n\n"
        "<b>Select an option below:</b>"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_open" or data == "menu_back":
        await query.edit_message_text(
            "<b>🎯 Main Menu</b>\n"
            "═" * 20 + "\n\n"
            "Select an option:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    elif data == "menu_stats":
        players = database.get_all_players()
        if not players:
            await query.edit_message_text(
                "<b>❌ No Players Tracked</b>\n\n"
                "Use <code>/add</code> to add players first!",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            return
        
        if len(players) == 1:
            await show_stats_for_player(query, players[0])
            return
        
        keyboard = []
        for p in players:
            keyboard.append([InlineKeyboardButton(f"👤 {p['name']}", callback_data=f"stats_{p['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_back")])
        
        await query.edit_message_text(
            "<b>📊 Select Player for Stats</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    elif data == "menu_match":
        players = database.get_all_players()
        if not players:
            await query.edit_message_text(
                "<b>❌ No Players Tracked</b>\n\n"
                "Use <code>/add</code> to add players first!",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            return
        
        if len(players) == 1:
            await show_match_list_for_player(query, players[0])
            return
        
        keyboard = []
        for p in players:
            keyboard.append([InlineKeyboardButton(f"👤 {p['name']}", callback_data=f"match_{p['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_back")])
        
        await query.edit_message_text(
            "<b>🎮 Select Player for Match History</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    elif data == "menu_map":
        players = database.get_all_players()
        if not players:
            await query.edit_message_text(
                "<b>❌ No Players Tracked</b>\n\n"
                "Use <code>/add</code> to add players first!",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            return
        
        keyboard = []
        for p in players:
            keyboard.append([InlineKeyboardButton(f"🗺️ {p['name']}", callback_data=f"map_{p['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_back")])
        
        await query.edit_message_text(
            "<b>🗺️ Select Player for Map Stats</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    elif data == "menu_compare":
        players = database.get_all_players()
        if len(players) < 2:
            await query.edit_message_text(
                "<b>❌ Need More Players</b>\n\n"
                "Use <code>/add</code> to add at least 2 players!",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            return
        
        keyboard = []
        for p in players:
            keyboard.append([InlineKeyboardButton(f"👤 {p['name']}", callback_data=f"compare1_{p['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_back")])
        
        await query.edit_message_text(
            "<b>⚔️ Select First Player to Compare</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    elif data == "menu_leaderboard":
        await show_leaderboard(query)
    
    elif data == "menu_players":
        players = database.get_all_players()
        if not players:
            text = "<b>👥 No tracked players</b>\n\nUse <code>/add</code> to add players!"
        else:
            text = "<b>👥 Tracked Players:</b>\n\n"
            for p in players:
                text += f"• {p['name']}\n"
            text += f"\n<i>Total: {len(players)} player(s)</i>"
        
        keyboard = [[InlineKeyboardButton("➕ Add Player", callback_data="menu_add")]]
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_back")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    elif data == "menu_settings":
        from config import POLLING_INTERVAL, WEEKLY_DIGEST_DAY, WEEKLY_DIGEST_HOUR, FACEIT_API_KEY
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        text = (
            "<b>⚙️ Settings</b>\n"
            "═" * 25 + "\n\n"
            f"⏱️ <b>Polling:</b> {POLLING_INTERVAL}s\n"
            f"📅 <b>Weekly Digest:</b> {days[WEEKLY_DIGEST_DAY]} at {WEEKLY_DIGEST_HOUR}:00\n\n"
            f"✅ <b>Leetify API:</b> Connected\n"
            f"{'✅' if FACEIT_API_KEY else '❌'} <b>FACEIT API:</b> {'Connected' if FACEIT_API_KEY else 'Not set'}"
        )
        await query.edit_message_text(
            text,
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
    
    elif data == "menu_add":
        text = (
            "<b>➕ Add New Player</b>\n\n"
            "Send me a Leetify profile URL or Steam ID:\n\n"
            "<code>/add 76561198157232800</code>\n"
            "<code>/add https://leetify.com/profile/...</code>"
        )
        await query.edit_message_text(
            text,
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )

async def show_stats_for_player(query, player: dict):
    await query.answer("Loading stats...", show_alert=False)
    
    client = leetify_client.client
    
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        await query.edit_message_text(
            "<b>❌ Could not fetch stats</b>\n\n"
            "The player profile might be private or the API key is invalid.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = formatters.format_player_stats(profile)
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_stats")]]
    
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    except Exception as e:
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def show_match_list_for_player(query, player: dict):
    await query.answer("Loading matches...", show_alert=False)
    
    client = leetify_client.client
    
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        await query.edit_message_text(
            "<b>❌ Could not fetch matches</b>",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    recent_matches = profile.get("recent_matches", [])
    
    if not recent_matches:
        await query.edit_message_text(
            "<b>❌ No recent matches</b>",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    keyboard = []
    for i, match in enumerate(recent_matches[:10]):
        map_name = match.get("map_name", "?")
        outcome = match.get("outcome", "?")
        score = match.get("score", [0, 0])
        rating = match.get("leetify_rating", 0)
        emoji = "✅" if outcome == "win" else "❌"
        r_emoji = "🟢" if rating > 0 else "🔴" if rating < 0 else "🟡"
        label = f"{emoji} {map_name} {score[0]}-{score[1]} {r_emoji}{rating:.2f}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"mdetail_{player['id']}_{i}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_match")])
    
    await query.edit_message_text(
        f"<b>🎮 Recent Matches - {player['name']}</b>\n\nSelect a match:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def show_leaderboard(query):
    await query.answer("Loading leaderboard...", show_alert=False)
    
    players = database.get_all_players()
    
    if not players:
        await query.edit_message_text(
            "<b>❌ No players tracked</b>",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    client = leetify_client.client
    
    player_stats = []
    for player in players:
        profile = client.get_player_profile(player["leetify_id"])
        if profile and "error" not in profile:
            player_stats.append({
                "name": player["name"],
                "rating": profile.get("ranks", {}).get("leetify", 0),
                "winrate": profile.get("winrate", 0) * 100,
                "matches": profile.get("total_matches", 0)
            })
    
    if not player_stats:
        await query.edit_message_text(
            "<b>❌ Could not fetch stats</b>",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    by_rating = sorted(player_stats, key=lambda x: x["rating"], reverse=True)
    by_wr = sorted(player_stats, key=lambda x: x["winrate"], reverse=True)
    
    medals = ["🥇", "🥈", "🥉", "  ", "  "]
    
    text = "<b>🏆 LEADERBOARD</b>\n"
    text += "═" * 25 + "\n\n"
    
    text += "<b>⭐ RATING:</b>\n"
    for i, p in enumerate(by_rating[:5], 1):
        text += f"{medals[i-1]} {i}. {p['name']}: <code>{round(p['rating'], 2)}</code>\n"
    
    text += "\n<b>🏆 WIN RATE:</b>\n"
    for i, p in enumerate(by_wr[:5], 1):
        text += f"{medals[i-1]} {i}. {p['name']}: <code>{round(p['winrate'], 1)}%</code>\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    player_id = int(query.data.split("_")[1])
    player = database.get_player_by_internal_id(player_id)
    
    if not player:
        await query.edit_message_text("<b>❌ Player not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    await show_stats_for_player(query, player)

async def match_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    player_id = int(query.data.split("_")[1])
    player = database.get_player_by_internal_id(player_id)
    
    if not player:
        await query.edit_message_text("<b>❌ Player not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    await show_match_list_for_player(query, player)

async def map_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Loading map stats...", show_alert=False)
    
    player_id = int(query.data.split("_")[1])
    player = database.get_player_by_internal_id(player_id)
    
    if not player:
        await query.edit_message_text("<b>❌ Player not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    client = leetify_client.client
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        await query.edit_message_text("<b>❌ Could not fetch map stats</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    text = formatters.format_player_map_stats(profile, player["name"])
    
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def compare1_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    player_id = int(query.data.split("_")[1])
    context.user_data["compare_p1"] = player_id
    
    players = database.get_all_players()
    
    keyboard = []
    for p in players:
        if p["id"] != player_id:
            keyboard.append([InlineKeyboardButton(f"👤 {p['name']}", callback_data=f"compare2_{p['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_compare")])
    
    await query.edit_message_text(
        "<b>⚔️ Select Second Player</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def compare2_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Comparing players...", show_alert=False)
    
    player2_id = int(query.data.split("_")[1])
    player1_id = context.user_data.get("compare_p1")
    
    if not player1_id:
        await query.edit_message_text("<b>❌ Error. Try /compare again</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    player1 = database.get_player_by_internal_id(player1_id)
    player2 = database.get_player_by_internal_id(player2_id)
    
    if not player1 or not player2:
        await query.edit_message_text("<b>❌ Player not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    client = leetify_client.client
    
    p1_data = client.get_player_profile(player1["leetify_id"])
    p2_data = client.get_player_profile(player2["leetify_id"])
    
    if not p1_data or not p2_data:
        await query.edit_message_text("<b>❌ Could not fetch stats</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    text = formatters.format_compare(p1_data, p2_data)
    
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def match_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Loading match details...", show_alert=False)
    
    parts = query.data.split("_")
    player_id = int(parts[1])
    match_index = int(parts[2])
    
    player = database.get_player_by_internal_id(player_id)
    if not player:
        await query.edit_message_text("<b>❌ Player not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    client = leetify_client.client
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile:
        await query.edit_message_text("<b>❌ Could not fetch data</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    recent_matches = profile.get("recent_matches", [])
    if match_index >= len(recent_matches):
        await query.edit_message_text("<b>❌ Match not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    match_data = recent_matches[match_index]
    game_id = match_data.get("id", "")
    map_name = match_data.get("map_name", "Unknown")
    
    match_details = client.get_match_details(game_id)
    
    if not match_details:
        await query.edit_message_text("<b>❌ Could not fetch match details</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    text = formatters.format_full_match_details_v2(match_details, player["leetify_id"])
    
    keyboard = [
        [InlineKeyboardButton("🤖 AI Analysis", callback_data=f"ai_{player_id}_{match_index}")],
        [InlineKeyboardButton("🔙 Back to Matches", callback_data=f"match_{player_id}")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def ai_analysis_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Analyzing match with AI...", show_alert=True)
    
    parts = query.data.split("_")
    player_id = int(parts[1])
    match_index = int(parts[2])
    
    player = database.get_player_by_internal_id(player_id)
    if not player:
        await query.edit_message_text("<b>❌ Player not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    client = leetify_client.client
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile:
        await query.edit_message_text("<b>❌ Could not fetch data</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    recent_matches = profile.get("recent_matches", [])
    if match_index >= len(recent_matches):
        await query.edit_message_text("<b>❌ Match not found</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    match_data = recent_matches[match_index]
    game_id = match_data.get("id", "")
    map_name = match_data.get("map_name", "Unknown")
    
    match_details = client.get_match_details(game_id)
    
    if not match_details:
        await query.edit_message_text("<b>❌ Could not fetch match details</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    # Get player stats from match details
    players = match_details.get("stats", [])
    player_stats = None
    
    for p in players:
        sid = str(p.get("steam64_id", ""))
        if sid == str(player["leetify_id"]) or sid == str(player.get("steam_id", "")):
            player_stats = p
            break
    
    if not player_stats and players:
        player_stats = players[0]
    
    if not player_stats:
        await query.edit_message_text("<b>❌ Could not get player stats</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    
    # Get AI analysis
    import ai_analysis
    analysis = ai_analysis.analyze_match(player_stats, map_name)
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Match", callback_data=f"mdetail_{player_id}_{match_index}")]]
    
    await query.edit_message_text(analysis, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
