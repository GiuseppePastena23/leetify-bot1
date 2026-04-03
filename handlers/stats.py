from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database
import leetify_client
import formatters
import config
import discord_client

def get_site_from_args(args):
    if not args:
        return "all"
    
    first_arg = args[0].lower()
    if first_arg in ["leetify", "csstats", "csgrind", "faceit", "all"]:
        return first_arg
    return "all"

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text(
            "<b>No players tracked yet.</b>\n\nUse <code>/add</code> to add players.",
            parse_mode="HTML"
        )
        return
    
    site = get_site_from_args(context.args)
    
    if len(players) == 1:
        await show_player_stats(update, context, players[0], site)
        return
    
    keyboard = []
    for p in players:
        keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"stats_{p['id']}_{site}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    site_emoji = {"leetify": "📊", "csstats": "🌐", "csgrind": "⛏️", "all": "📈"}
    await update.message.reply_text(
        f"Select a player ({site_emoji.get(site, '📈')} {site.upper()}):",
        reply_markup=reply_markup
    )

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    player_id = int(parts[1])
    site = parts[2] if len(parts) > 2 else "all"
    
    player = database.get_player_by_internal_id(player_id)
    
    if not player:
        await query.edit_message_text("<b>Player not found.</b>", parse_mode="HTML")
        return
    
    await show_player_stats_from_callback(query, context, player, site)

async def show_player_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, player: dict, site: str = "all"):
    client = leetify_client.client
    
    msg_parts = []
    
    if site in ["all", "leetify"]:
        leetify_profile = client.get_player_profile(player["leetify_id"])
        if leetify_profile and "error" not in leetify_profile:
            msg_parts.append(formatters.format_player_stats(leetify_profile))
        elif leetify_profile and "error" in leetify_profile:
            msg_parts.append(f"❌ Leetify: {leetify_profile.get('message', 'API error')}")
        else:
            msg_parts.append("❌ Leetify: Could not fetch stats")
    
    steam_id = player.get("steam_id", "")
    if steam_id and steam_id.startswith("7656119"):
        if site in ["all", "csstats"]:
            csstats_data = leetify_client.csstats_client.get_player(steam_id)
            if csstats_data and "error" not in csstats_data:
                msg_parts.append(formatters.format_csstats_player(csstats_data))
            elif csstats_data and "error" in csstats_data:
                msg_parts.append(f"⚠️ CSStats: {csstats_data.get('message', 'Service unavailable')}")
            else:
                msg_parts.append("⚠️ CSStats: No data available")
    
    if site in ["all", "faceit"]:
        faceit_id = player.get("faceit_id", "")
        if not faceit_id and steam_id:
            faceit_data = leetify_client.faceit_client.get_player_by_steam(steam_id)
            if faceit_data:
                faceit_id = faceit_data.get("player_id", "")
        
        if faceit_id:
            faceit_info = leetify_client.faceit_client._request(f"/players/{faceit_id}")
            faceit_stats = leetify_client.faceit_client.get_player_stats(faceit_id)
            
            if faceit_info and "error" not in faceit_info:
                msg_parts.append(formatters.format_faceit_player(faceit_info, faceit_stats))
            elif faceit_info and faceit_info.get("error") == "no_api_key":
                msg_parts.append("⚠️ FACEIT: No API key configured")
            elif faceit_info and faceit_info.get("error") == "invalid_api_key":
                msg_parts.append("⚠️ FACEIT: Invalid API key")
            else:
                msg_parts.append("⚠️ FACEIT: No data available")
        elif not leetify_client.faceit_client.headers:
            msg_parts.append("⚠️ FACEIT: API key not set in config")
    
    msg = "\n\n".join(msg_parts)
    
    if not msg.strip():
        msg = "No stats available for this site."
    
    if update.message:
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await update.callback_query.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)

async def show_player_stats_from_callback(query, context, player: dict, site: str = "all"):
    client = leetify_client.client
    
    msg_parts = []
    
    if site in ["all", "leetify"]:
        leetify_profile = client.get_player_profile(player["leetify_id"])
        if leetify_profile and "error" not in leetify_profile:
            msg_parts.append(formatters.format_player_stats(leetify_profile))
        elif leetify_profile and "error" in leetify_profile:
            msg_parts.append(f"❌ Leetify: {leetify_profile.get('message', 'API error')}")
        else:
            msg_parts.append("❌ Leetify: Could not fetch stats")
    
    steam_id = player.get("steam_id", "")
    if steam_id and steam_id.startswith("7656119"):
        if site in ["all", "csstats"]:
            csstats_data = leetify_client.csstats_client.get_player(steam_id)
            if csstats_data and "error" not in csstats_data:
                msg_parts.append(formatters.format_csstats_player(csstats_data))
            elif csstats_data and "error" in csstats_data:
                msg_parts.append(f"⚠️ CSStats: {csstats_data.get('message', 'Service unavailable')}")
            else:
                msg_parts.append("⚠️ CSStats: No data available")
    
    if site in ["all", "faceit"]:
        faceit_id = player.get("faceit_id", "")
        if not faceit_id and steam_id:
            faceit_data = leetify_client.faceit_client.get_player_by_steam(steam_id)
            if faceit_data:
                faceit_id = faceit_data.get("player_id", "")
        
        if faceit_id:
            faceit_info = leetify_client.faceit_client._request(f"/players/{faceit_id}")
            faceit_stats = leetify_client.faceit_client.get_player_stats(faceit_id)
            
            if faceit_info and "error" not in faceit_info:
                msg_parts.append(formatters.format_faceit_player(faceit_info, faceit_stats))
            elif faceit_info and faceit_info.get("error") == "no_api_key":
                msg_parts.append("⚠️ FACEIT: No API key configured")
            elif faceit_info and faceit_info.get("error") == "invalid_api_key":
                msg_parts.append("⚠️ FACEIT: Invalid API key")
            else:
                msg_parts.append("⚠️ FACEIT: No data available")
        elif not leetify_client.faceit_client.headers:
            msg_parts.append("⚠️ FACEIT: API key not set in config")
    
    msg = "\n\n".join(msg_parts)
    
    if not msg.strip():
        msg = "No stats available for this site."
    
    await query.edit_message_text(msg, parse_mode="HTML", disable_web_page_preview=True)

async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text(
            "<b>No players tracked yet.</b>\n\nUse <code>/add</code> to add players.",
            parse_mode="HTML"
        )
        return
    
    if len(players) < 2:
        await update.message.reply_text(
            "<b>You need at least 2 players to compare.</b>",
            parse_mode="HTML"
        )
        return
    
    keyboard = []
    for p in players:
        keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"compare1_{p['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "<b>Select the first player:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def compare_callback1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    player_id = int(query.data.split("_")[1])
    context.user_data["compare_player1"] = player_id
    
    players = database.get_all_players()
    keyboard = []
    for p in players:
        if p["id"] != player_id:
            keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"compare2_{p['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "<b>Select the second player:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def compare_callback2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    player2_id = int(query.data.split("_")[1])
    player1_id = context.user_data.get("compare_player1")
    
    if not player1_id:
        await query.edit_message_text("<b>Error: Please start /compare again.</b>", parse_mode="HTML")
        return
    
    player1 = database.get_player_by_internal_id(player1_id)
    player2 = database.get_player_by_internal_id(player2_id)
    
    if not player1 or not player2:
        await query.edit_message_text("<b>Error: Player not found.</b>", parse_mode="HTML")
        return
    
    client = leetify_client.client
    
    p1_data = client.get_player_profile(player1["leetify_id"])
    p2_data = client.get_player_profile(player2["leetify_id"])
    
    if not p1_data or "error" in p1_data:
        await query.edit_message_text(f"❌ Failed to fetch stats for {player1['name']}.", parse_mode="HTML")
        return
    
    if not p2_data or "error" in p2_data:
        await query.edit_message_text(f"❌ Failed to fetch stats for {player2['name']}.", parse_mode="HTML")
        return
    
    await query.edit_message_text(
        formatters.format_compare(p1_data, p2_data),
        parse_mode="HTML"
    )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args if context.args else []
    weekly = "weekly" in args or "-w" in args
    
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text("<b>No tracked players.</b>", parse_mode="HTML")
        return
    
    client = leetify_client.client
    
    if weekly:
        week_start = database.get_week_start()
        stats = database.get_weekly_stats(week_start)
        
        if not stats:
            await update.message.reply_text(
                "<b>No weekly stats yet.</b>\n\nPlay some matches this week!",
                parse_mode="HTML"
            )
            return
        
        week_stats = []
        for p in stats:
            matches = p.get("matches_played", 0)
            wins = p.get("wins", 0)
            week_stats.append({
                "name": p.get("name", "Unknown"),
                "matches": matches,
                "wins": wins,
                "losses": p.get("losses", 0),
                "winrate": (wins / matches * 100) if matches > 0 else 0,
                "avg_rating": p.get("rating_sum", 0) / matches if matches > 0 else 0
            })
        
        by_rating = sorted(week_stats, key=lambda x: x.get("avg_rating", 0), reverse=True)
        by_wr = sorted(week_stats, key=lambda x: x.get("winrate", 0), reverse=True)
        
        medals = ["🥇", "🥈", "🥉", "  ", "  "]
        
        lines = [
            "<b>🏆 Weekly Leaderboard</b>",
            "═" * 25,
            ""
        ]
        
        lines.append("<b>⭐ RATING:</b>")
        for i, p in enumerate(by_rating[:5], 1):
            lines.append(f"{medals[i-1]} {i}. {p['name']}: <code>{p['avg_rating']:.2f}</code> ({p['matches']} matches)")
        lines.append("")
        
        lines.append("<b>🏆 WIN RATE:</b>")
        for i, p in enumerate(by_wr[:5], 1):
            lines.append(f"{medals[i-1]} {i}. {p['name']}: <code>{p['winrate']:.1f}%</code> ({p['wins']}-{p['losses']})")
        
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return
    
    player_stats = []
    
    for player in players:
        profile = client.get_player_profile(player["leetify_id"])
        
        if profile and "error" not in profile:
            player_stats.append({
                "name": player["name"],
                "leetify_rating": profile.get("ranks", {}).get("leetify", 0),
                "winrate": profile.get("winrate", 0) * 100,
                "matches": profile.get("total_matches", 0),
            })
    
    if not player_stats:
        await update.message.reply_text("<b>Could not fetch player stats.</b>", parse_mode="HTML")
        return
    
    by_rating = sorted(player_stats, key=lambda x: x.get("leetify_rating", 0), reverse=True)
    by_wr = sorted(player_stats, key=lambda x: x.get("winrate", 0), reverse=True)
    by_matches = sorted(player_stats, key=lambda x: x.get("matches", 0), reverse=True)
    
    medals = ["🥇", "🥈", "🥉", "  ", "  "]
    
    lines = [
        "<b>🏆 LEADERBOARD</b>",
        "═" * 25,
        ""
    ]
    
    lines.append("<b>⭐ RATING:</b>")
    for i, p in enumerate(by_rating[:5], 1):
        lines.append(f"{medals[i-1]} {i}. {p['name']}: <code>{p['leetify_rating']:.2f}</code>")
    lines.append("")
    
    lines.append("<b>🏆 WIN RATE:</b>")
    for i, p in enumerate(by_wr[:5], 1):
        lines.append(f"{medals[i-1]} {i}. {p['name']}: <code>{round(p['winrate'], 1)}%</code>")
    lines.append("")
    
    lines.append("<b>🎮 MATCHES:</b>")
    for i, p in enumerate(by_matches[:5], 1):
        lines.append(f"{medals[i-1]} {i}. {p['name']}: <code>{p['matches']}</code>")
    
    lines.append("")
    lines.append("<i>Use /leaderboard weekly for weekly stats</i>")
    
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    
    import discord_client
    if config.DISCORD_ENABLED:
        discord_client.send_leaderboard("Leaderboard", [
            {"rank": i+1, "name": p["name"], "rating": p.get("leetify_rating", 0), "winrate": p.get("winrate", 0)}
            for i, p in enumerate(by_rating[:10])
        ])

async def player_of_week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import weekly_digest
    
    player = weekly_digest.get_player_of_the_week()
    
    if not player:
        await update.message.reply_text(
            "<b>❌ No player of the week yet.</b>\n\n"
            "Need at least 3 matches played this week to qualify.",
            parse_mode="HTML"
        )
        return
    
    text = (
        f"⭐ <b>Player of the Week</b> ⭐\n"
        "═" * 25 + "\n\n"
        f"🏆 <b>{player['name']}</b>\n\n"
        f"📊 Matches: {player['matches']}\n"
        f"✅ Wins: {player['wins']}\n"
        f"📈 Win Rate: {player['winrate']:.1f}%\n"
        f"⭐ Avg Rating: {player['avg_rating']:.2f}\n"
        f"🎯 K/D: {player['kd']:.2f}\n\n"
        f"<i>Minimum 3 matches required to qualify</i>"
    )
    
    await update.message.reply_text(text, parse_mode="HTML")

async def team_dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text(
            "<b>❌ No players tracked.</b>\n\nUse <code>/add</code> to add players.",
            parse_mode="HTML"
        )
        return
    
    client = leetify_client.client
    
    team_stats = {
        "total_players": len(players),
        "total_matches": 0,
        "total_wins": 0,
        "total_losses": 0,
        "avg_rating": 0,
        "avg_winrate": 0,
        "total_kills": 0,
        "total_deaths": 0,
        "best_player": None,
        "best_rating": 0
    }
    
    ratings = []
    
    for player in players:
        profile = client.get_player_profile(player["leetify_id"])
        
        if profile and "error" not in profile:
            matches = profile.get("total_matches", 0)
            winrate = profile.get("winrate", 0) * 100
            rating = profile.get("ranks", {}).get("leetify", 0)
            kills = profile.get("total_kills", 0)
            deaths = profile.get("total_deaths", 0)
            
            wins = int(matches * winrate / 100)
            
            team_stats["total_matches"] += matches
            team_stats["total_wins"] += wins
            team_stats["total_losses"] += matches - wins
            team_stats["total_kills"] += kills
            team_stats["total_deaths"] += deaths
            
            ratings.append(rating)
            
            if rating > team_stats["best_rating"]:
                team_stats["best_rating"] = rating
                team_stats["best_player"] = player["name"]
    
    if ratings:
        team_stats["avg_rating"] = sum(ratings) / len(ratings)
    
    if team_stats["total_matches"] > 0:
        team_stats["avg_winrate"] = (team_stats["total_wins"] / team_stats["total_matches"]) * 100
    
    team_kd = team_stats["total_kills"] / team_stats["total_deaths"] if team_stats["total_deaths"] > 0 else 0
    
    text = (
        f"<b>📊 Team Dashboard</b>\n"
        "═" * 25 + "\n\n"
        f"<b>👥 Players:</b> {team_stats['total_players']}\n"
        f"<b>🎮 Total Matches:</b> {team_stats['total_matches']}\n"
        f"<b>✅ Wins:</b> {team_stats['total_wins']}\n"
        f"<b>❌ Losses:</b> {team_stats['total_losses']}\n"
        f"<b>📈 Win Rate:</b> {team_stats['avg_winrate']:.1f}%\n\n"
        f"<b>⭐ Average Rating:</b> {team_stats['avg_rating']:.2f}\n"
        f"<b>🎯 Team K/D:</b> {team_kd:.2f}\n\n"
        f"<b>🏆 Best Player:</b> {team_stats['best_player'] or 'N/A'}\n"
        f"<b>   Rating:</b> {team_stats['best_rating']:.2f}"
    )
    
    await update.message.reply_text(text, parse_mode="HTML")

import random
from datetime import datetime
import hashlib

_stat_cache = {}

async def stat_of_day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text(
            "<b>❌ No players tracked.</b>\n\nUse /add to add players first!",
            parse_mode="HTML"
        )
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"stat_{today}"
    
    if cache_key in _stat_cache:
        stat_type, player_name, stat_value, description = _stat_cache[cache_key]
    else:
        client = leetify_client.client
        player_data = []
        
        for player in players:
            profile = client.get_player_profile(player["leetify_id"])
            if profile and "error" not in profile:
                player_data.append({
                    "name": player["name"],
                    "profile": profile
                })
        
        if not player_data:
            await update.message.reply_text("<b>❌ Could not fetch player stats.</b>", parse_mode="HTML")
            return
        
        stat_types = ["hs", "adr", "rating", "winrate", "matches", "kd", "clutch", "multi"]
        stat_type = random.choice(stat_types)
        
        best_player = None
        best_value = -1
        
        for p in player_data:
            profile = p["profile"]
            
            if stat_type == "hs":
                hs = profile.get("headshot_percentage", 0) * 100
                if hs > best_value:
                    best_value = hs
                    best_player = p["name"]
                    stat_value = f"{hs:.1f}%"
                    description = "headshot percentage"
            
            elif stat_type == "adr":
                adr = profile.get("adr", 0)
                if adr > best_value:
                    best_value = adr
                    best_player = p["name"]
                    stat_value = f"{adr:.1f}"
                    description = "average damage per round"
            
            elif stat_type == "rating":
                rating = profile.get("ranks", {}).get("leetify", 0)
                if rating > best_value:
                    best_value = rating
                    best_player = p["name"]
                    stat_value = f"{rating:.2f}"
                    description = "Leetify rating"
            
            elif stat_type == "winrate":
                wr = profile.get("winrate", 0) * 100
                matches = profile.get("total_matches", 0)
                if matches >= 10 and wr > best_value:
                    best_value = wr
                    best_player = p["name"]
                    stat_value = f"{wr:.1f}%"
                    description = "win rate"
            
            elif stat_type == "matches":
                matches = profile.get("total_matches", 0)
                if matches > best_value:
                    best_value = matches
                    best_player = p["name"]
                    stat_value = str(matches)
                    description = "total matches"
            
            elif stat_type == "kd":
                kills = profile.get("total_kills", 0)
                deaths = profile.get("total_deaths", 1)
                kd = kills / deaths if deaths > 0 else 0
                if kd > best_value:
                    best_value = kd
                    best_player = p["name"]
                    stat_value = f"{kd:.2f}"
                    description = "K/D ratio"
            
            elif stat_type == "clutch":
                clutches = profile.get("clutch_1v1_wins", 0) + profile.get("clutch_1v2_wins", 0) + profile.get("clutch_1v3_wins", 0)
                if clutches > best_value:
                    best_value = clutches
                    best_player = p["name"]
                    stat_value = str(clutches)
                    description = "clutch wins"
            
            elif stat_type == "multi":
                multi = profile.get("multi_2k", 0) + profile.get("multi_3k", 0) + profile.get("multi_4k", 0) + profile.get("multi_5k", 0)
                if multi > best_value:
                    best_value = multi
                    best_player = p["name"]
                    stat_value = str(multi)
                    description = "multi-kills"
        
        if not best_player:
            await update.message.reply_text("<b>❌ Not enough data for a stat.</b>", parse_mode="HTML")
            return
        
        player_name = best_player
        _stat_cache[cache_key] = (stat_type, player_name, stat_value, description)
    
    emojis = {
        "hs": "🎯",
        "adr": "💥",
        "rating": "⭐",
        "winrate": "🏆",
        "matches": "🎮",
        "kd": "⚔️",
        "clutch": "😱",
        "multi": "🔥"
    }
    
    emoji = emojis.get(stat_type, "📊")
    
    text = (
        f"<b>🎲 Stat of the Day</b>\n"
        "═" * 25 + "\n\n"
        f"{emoji} <b>{player_name}</b>\n"
        f"Has the highest <b>{description}</b> on the team!\n\n"
        f"📈 Value: <code>{stat_value}</code>\n\n"
        f"<i>New stat every day at midnight</i>"
    )
    
    await update.message.reply_text(text, parse_mode="HTML")

async def analyze_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text(
            "<b>❌ No players tracked.</b>\n\nUse /add to add players first!",
            parse_mode="HTML"
        )
        return
    
    client = leetify_client.client
    
    if context.args:
        name = " ".join(context.args)
        player = database.get_player_by_name(name)
        
        if not player:
            await update.message.reply_text(f"<b>❌ Player '{name}' not found.</b>", parse_mode="HTML")
            return
        
        profile = client.get_player_profile(player["leetify_id"])
        
        if not profile or "error" in profile:
            await update.message.reply_text("<b>❌ Could not fetch player profile.</b>", parse_mode="HTML")
            return
        
        await send_ai_analysis(update, profile, player["name"])
        return
    
    keyboard = []
    for p in players:
        keyboard.append([InlineKeyboardButton(f"🤖 {p['name']}", callback_data=f"ai_profile_{p['id']}")])
    
    keyboard.append([InlineKeyboardButton("🎲 Random", callback_data="ai_profile_random")])
    
    await update.message.reply_text(
        "<b>🤖 Select a player to analyze:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

team_selections = {}

async def myteam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text(
            "<b>❌ No players tracked.</b>\n\nUse /add to add players first!",
            parse_mode="HTML"
        )
        return
    
    if len(players) < 5:
        await update.message.reply_text(
            f"<b>❌ Need at least 5 players to create a team.</b>\n\nYou have {len(players)} players tracked.",
            parse_mode="HTML"
        )
        return
    
    user_id = update.effective_user.id if update.effective_user else 0
    team_selections[user_id] = []
    
    keyboard = []
    for p in players:
        keyboard.append([InlineKeyboardButton(f"➕ {p['name']}", callback_data=f"team_add_{p['id']}")])
    
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="team_done")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="team_cancel")])
    
    text = (
        "<b>👥 Create Your Team</b>\n"
        "═" * 25 + "\n\n"
        "Select exactly <b>5 players</b> for your team:\n\n"
        "Selected: <code>0/5</code>"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def team_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id if query.from_user else 0
    data = query.data
    
    if data == "team_cancel":
        if user_id in team_selections:
            del team_selections[user_id]
        await query.edit_message_text("<b>❌ Team selection cancelled.</b>", parse_mode="HTML")
        return
    
    if data == "team_done":
        if user_id not in team_selections or len(team_selections[user_id]) != 5:
            await query.answer("Select exactly 5 players!", show_alert=True)
            return
        
        await query.edit_message_text("<b>🔄 Calculating team stats...</b>", parse_mode="HTML")
        
        player_ids = team_selections[user_id]
        players = [database.get_player_by_internal_id(pid) for pid in player_ids]
        
        text = await calculate_team_stats(players)
        await query.message.reply_text(text, parse_mode="HTML")
        
        del team_selections[user_id]
        return
    
    if data.startswith("team_add_"):
        player_id = int(data.replace("team_add_", ""))
        
        if user_id not in team_selections:
            team_selections[user_id] = []
        
        current = team_selections[user_id]
        
        if player_id in current:
            await query.answer("Player already selected!", show_alert=True)
            return
        
        if len(current) >= 5:
            await query.answer("Already have 5 players!", show_alert=True)
            return
        
        current.append(player_id)
        
        player = database.get_player_by_internal_id(player_id)
        await query.answer(f"Added {player['name']}!", show_alert=False)
        
        players = database.get_all_players()
        
        keyboard = []
        for p in players:
            if p['id'] in current:
                keyboard.append([InlineKeyboardButton(f"✅ {p['name']}", callback_data=f"team_add_{p['id']}")])
            else:
                keyboard.append([InlineKeyboardButton(f"➕ {p['name']}", callback_data=f"team_add_{p['id']}")])
        
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="team_done")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="team_cancel")])
        
        text = (
            "<b>👥 Create Your Team</b>\n"
            "═" * 25 + "\n\n"
            "Select exactly <b>5 players</b> for your team:\n\n"
            f"Selected: <code>{len(current)}/5</code>\n"
            f"Players: {', '.join([database.get_player_by_internal_id(pid)['name'] for pid in current])}"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

async def calculate_team_stats(players):
    if not players:
        return "<b>❌ No players found.</b>"
    
    client = leetify_client.client
    
    player_profiles = []
    for p in players:
        profile = client.get_player_profile(p["leetify_id"])
        if profile and "error" not in profile:
            player_profiles.append({"player": p, "profile": profile})
    
    if not player_profiles:
        return "<b>❌ Could not fetch player profiles.</b>"
    
    total_matches = 0
    total_wins = 0
    total_kills = 0
    total_deaths = 0
    total_adr = 0
    total_rating = 0
    
    map_stats = {}
    
    for pp in player_profiles:
        profile = pp["profile"]
        
        matches = profile.get("total_matches", 0)
        winrate = profile.get("winrate", 0)
        kills = profile.get("total_kills", 0)
        deaths = profile.get("total_deaths", 0)
        adr = profile.get("adr", 0)
        rating = profile.get("ranks", {}).get("leetify", 0)
        
        total_matches += matches
        total_wins += int(matches * winrate)
        total_kills += kills
        total_deaths += deaths
        total_adr += adr
        total_rating += rating
        
        maps = profile.get("maps", {})
        for map_name, stats in maps.items():
            if map_name not in map_stats:
                map_stats[map_name] = {"wins": 0, "matches": 0}
            map_stats[map_name]["wins"] += stats.get("wins", 0)
            map_stats[map_name]["matches"] += stats.get("matches", 0)
    
    num_players = len(player_profiles)
    
    avg_matches = total_matches // num_players
    avg_wins = total_wins // num_players
    avg_kd = total_kills / total_deaths if total_deaths > 0 else 0
    avg_adr = total_adr / num_players
    avg_rating = total_rating / num_players
    overall_wr = (total_wins / total_matches * 100) if total_matches > 0 else 0
    
    best_maps = []
    worst_maps = []
    if map_stats:
        map_list = []
        for map_name, stats in map_stats.items():
            wr = (stats["wins"] / stats["matches"] * 100) if stats["matches"] > 0 else 0
            map_list.append((map_name, wr, stats["matches"]))
        
        map_list.sort(key=lambda x: x[1], reverse=True)
        best_maps = map_list[:3]
        worst_maps = map_list[-2:] if len(map_list) >= 2 else []
    
    lines = [
        "<b>👥 Team Analysis</b>",
        "═" * 30,
        ""
    ]
    
    lines.append("<b>📊 TEAM STATS:</b>")
    lines.append(f"Players: <code>{num_players}</code>")
    lines.append(f"Avg Matches: <code>{avg_matches}</code>")
    lines.append(f"Win Rate: <code>{overall_wr:.1f}%</code>")
    lines.append(f"Avg K/D: <code>{avg_kd:.2f}</code>")
    lines.append(f"Avg ADR: <code>{avg_adr:.1f}</code>")
    lines.append(f"Avg Rating: <code>{avg_rating:.2f}</code>")
    lines.append("")
    
    if best_maps:
        lines.append("<b>🗺️ BEST MAPS:</b>")
        for m, wr, matches in best_maps:
            if matches >= 5:
                lines.append(f"  • {m}: <code>{wr:.1f}%</code> ({matches} matches)")
        lines.append("")
    
    if worst_maps:
        lines.append("<b>⚠️ MAPS TO WORK ON:</b>")
        for m, wr, matches in worst_maps:
            if matches >= 5:
                lines.append(f"  • {m}: <code>{wr:.1f}%</code> ({matches} matches)")
        lines.append("")
    
    lines.append("<b>🎯 PLAYER BREAKDOWN:</b>")
    for pp in player_profiles:
        p = pp["player"]
        prof = pp["profile"]
        rating = prof.get("ranks", {}).get("leetify", 0)
        k = prof.get("total_kills", 0)
        d = prof.get("total_deaths", 1)
        kd = k / d if d > 0 else 0
        adr = prof.get("adr", 0)
        wr = prof.get("winrate", 0) * 100
        
        lines.append(f"  {p['name']}: <code>{rating:.2f}</code rating | <code>{kd:.2f}</code KD | <code>{adr:.0f}</code ADR | <code>{wr:.0f}%</code WR")
    
    return "\n".join(lines)

async def send_ai_analysis(update, profile, player_name):
    await update.message.reply_text(
        f"<b>🤖 Analyzing {player_name}...</b>",
        parse_mode="HTML"
    )
    
    import ai_analysis
    result = ai_analysis.analyze_player_profile(profile, player_name)
    await update.message.reply_text(result, parse_mode="HTML")

async def ai_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "ai_profile_random":
        players = database.get_all_players()
        if not players:
            await query.edit_message_text("<b>❌ No players tracked.</b>", parse_mode="HTML")
            return
        
        player = random.choice(players)
        client = leetify_client.client
        profile = client.get_player_profile(player["leetify_id"])
        
        if not profile or "error" in profile:
            await query.edit_message_text("<b>❌ Could not fetch player profile.</b>", parse_mode="HTML")
            return
        
        await query.edit_message_text(
            f"<b>🤖 Analyzing {player['name']}...</b>",
            parse_mode="HTML"
        )
        
        import ai_analysis
        result = ai_analysis.analyze_player_profile(profile, player["name"])
        await query.message.reply_text(result, parse_mode="HTML")
        return
    
    player_id = data.replace("ai_profile_", "")
    
    if not player_id.isdigit():
        await query.answer("Invalid selection", show_alert=True)
        return
    
    player = database.get_player_by_internal_id(int(player_id))
    
    if not player:
        await query.edit_message_text("<b>❌ Player not found.</b>", parse_mode="HTML")
        return
    
    client = leetify_client.client
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        await query.edit_message_text("<b>❌ Could not fetch player profile.</b>", parse_mode="HTML")
        return
    
    await query.edit_message_text(
        f"<b>🤖 Analyzing {player['name']}...</b>",
        parse_mode="HTML"
    )
    
    import ai_analysis
    result = ai_analysis.analyze_player_profile(profile, player["name"])
    await query.message.reply_text(result, parse_mode="HTML")

async def send_daily_stat(bot):
    import config
    if not config.CHAT_ID:
        return
    
    players = database.get_all_players()
    
    if not players:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"stat_{today}"
    
    if cache_key in _stat_cache:
        stat_type, player_name, stat_value, description = _stat_cache[cache_key]
    else:
        client = leetify_client.client
        player_data = []
        
        for player in players:
            profile = client.get_player_profile(player["leetify_id"])
            if profile and "error" not in profile:
                player_data.append({
                    "name": player["name"],
                    "profile": profile
                })
        
        if not player_data:
            return
        
        stat_types = ["hs", "adr", "rating", "winrate", "matches", "kd", "clutch", "multi"]
        stat_type = random.choice(stat_types)
        
        best_player = None
        best_value = -1
        stat_value = "0"
        description = "stat"
        
        for p in player_data:
            profile = p["profile"]
            
            if stat_type == "hs":
                hs = profile.get("headshot_percentage", 0) * 100
                if hs > best_value:
                    best_value = hs
                    best_player = p["name"]
                    stat_value = f"{hs:.1f}%"
                    description = "headshot percentage"
            
            elif stat_type == "adr":
                adr = profile.get("adr", 0)
                if adr > best_value:
                    best_value = adr
                    best_player = p["name"]
                    stat_value = f"{adr:.1f}"
                    description = "average damage per round"
            
            elif stat_type == "rating":
                rating = profile.get("ranks", {}).get("leetify", 0)
                if rating > best_value:
                    best_value = rating
                    best_player = p["name"]
                    stat_value = f"{rating:.2f}"
                    description = "Leetify rating"
            
            elif stat_type == "winrate":
                wr = profile.get("winrate", 0) * 100
                matches = profile.get("total_matches", 0)
                if matches >= 10 and wr > best_value:
                    best_value = wr
                    best_player = p["name"]
                    stat_value = f"{wr:.1f}%"
                    description = "win rate"
            
            elif stat_type == "matches":
                matches = profile.get("total_matches", 0)
                if matches > best_value:
                    best_value = matches
                    best_player = p["name"]
                    stat_value = str(matches)
                    description = "total matches"
            
            elif stat_type == "kd":
                kills = profile.get("total_kills", 0)
                deaths = profile.get("total_deaths", 1)
                kd = kills / deaths if deaths > 0 else 0
                if kd > best_value:
                    best_value = kd
                    best_player = p["name"]
                    stat_value = f"{kd:.2f}"
                    description = "K/D ratio"
            
            elif stat_type == "clutch":
                clutches = profile.get("clutch_1v1_wins", 0) + profile.get("clutch_1v2_wins", 0) + profile.get("clutch_1v3_wins", 0)
                if clutches > best_value:
                    best_value = clutches
                    best_player = p["name"]
                    stat_value = str(clutches)
                    description = "clutch wins"
            
            elif stat_type == "multi":
                multi = profile.get("multi_2k", 0) + profile.get("multi_3k", 0) + profile.get("multi_4k", 0) + profile.get("multi_5k", 0)
                if multi > best_value:
                    best_value = multi
                    best_player = p["name"]
                    stat_value = str(multi)
                    description = "multi-kills"
        
        if not best_player:
            return
        
        player_name = best_player
        _stat_cache[cache_key] = (stat_type, player_name, stat_value, description)
    
    emojis = {
        "hs": "🎯",
        "adr": "💥",
        "rating": "⭐",
        "winrate": "🏆",
        "matches": "🎮",
        "kd": "⚔️",
        "clutch": "😱",
        "multi": "🔥"
    }
    
    emoji = emojis.get(stat_type, "📊")
    
    text = (
        f"<b>🎲 Stat of the Day</b>\n"
        "═" * 25 + "\n\n"
        f"{emoji} <b>{player_name}</b>\n"
        f"Has the highest <b>{description}</b> on the team!\n\n"
        f"📈 Value: <code>{stat_value}</code>"
    )
    
    try:
        await bot.send_message(chat_id=config.CHAT_ID, text=text, parse_mode="HTML")
    except Exception as e:
        import logging
        logging.error(f"Failed to send stat of the day: {e}")

async def test_weekly_analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import weekly_digest
    
    await update.message.reply_text(
        "<b>🔄 Sending weekly analysis...</b>",
        parse_mode="HTML"
    )
    
    await weekly_digest.send_weekly_analysis(update.message.bot)

async def test_stat_of_day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>🔄 Sending stat of the day...</b>",
        parse_mode="HTML"
    )
    
    await send_daily_stat(update.message.bot)

async def test_analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text(
            "<b>❌ No players tracked.</b>",
            parse_mode="HTML"
        )
        return
    
    player = players[0]
    client = leetify_client.client
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        await update.message.reply_text(
            "<b>❌ Could not fetch player profile.</b>",
            parse_mode="HTML"
        )
        return
    
    await send_ai_analysis(update, profile, player["name"])

async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    client = leetify_client.client
    
    if context.args:
        name = " ".join(context.args)
        player = database.get_player_by_name(name)
        
        if not player:
            await update.message.reply_text(f"<b>❌ Player '{name}' not found.</b>", parse_mode="HTML")
            return
        
        profile = client.get_player_profile(player["leetify_id"])
        
        if not profile or "error" in profile:
            await update.message.reply_text("<b>❌ Failed to fetch player stats.</b>", parse_mode="HTML")
            return
        
        text = formatters.format_player_map_stats(profile, player["name"])
        await update.message.reply_text(text, parse_mode="HTML")
        return
    
    if not players:
        await update.message.reply_text("<b>No players tracked.</b>", parse_mode="HTML")
        return
    
    if len(players) == 1:
        profile = client.get_player_profile(players[0]["leetify_id"])
        if profile and "error" not in profile:
            text = formatters.format_player_map_stats(profile, players[0]["name"])
            await update.message.reply_text(text, parse_mode="HTML")
        else:
            await update.message.reply_text("<b>Could not fetch stats.</b>", parse_mode="HTML")
        return
    
    keyboard = []
    for p in players:
        keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"map_{p['id']}")])
    
    await update.message.reply_text(
        "Select a player:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def match_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    client = leetify_client.client
    
    if context.args:
        name = " ".join(context.args)
        player = database.get_player_by_name(name)
        
        if not player:
            await update.message.reply_text(f"<b>❌ Player '{name}' not found.</b>", parse_mode="HTML")
            return
        
        profile = client.get_player_profile(player["leetify_id"])
        
        if not profile or "error" in profile:
            await update.message.reply_text("<b>❌ Failed to fetch player matches.</b>", parse_mode="HTML")
            return
        
        recent_matches = profile.get("recent_matches", [])
        
        if not recent_matches:
            await update.message.reply_text(f"<b>No recent matches for {player['name']}.</b>", parse_mode="HTML")
            return
        
        text = formatters.format_match_list(recent_matches, player["name"])
        await update.message.reply_text(text, parse_mode="HTML")
        return
    
    if not players:
        await update.message.reply_text("<b>No players tracked.</b>", parse_mode="HTML")
        return
    
    if len(players) == 1:
        profile = client.get_player_profile(players[0]["leetify_id"])
        if profile and "error" not in profile:
            recent_matches = profile.get("recent_matches", [])
            text = formatters.format_match_list(recent_matches, players[0]["name"])
            await update.message.reply_text(text, parse_mode="HTML")
        else:
            await update.message.reply_text("<b>Could not fetch matches.</b>", parse_mode="HTML")
        return
    
    keyboard = []
    for p in players:
        keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"match_{p['id']}")])
    
    await update.message.reply_text(
        "Select a player:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
