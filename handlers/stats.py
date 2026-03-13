from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database
import leetify_client
import formatters

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
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text("<b>No tracked players.</b>", parse_mode="HTML")
        return
    
    client = leetify_client.client
    
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
    
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

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
        
        recent_matches = profile.get("recent_matches", [])
        
        if not recent_matches:
            await update.message.reply_text(f"<b>No map data available for {player['name']}.</b>", parse_mode="HTML")
            return
        
        text = formatters.format_player_map_stats(profile, player["name"])
        await update.message.reply_text(text, parse_mode="HTML")
    
    else:
        if not players:
            await update.message.reply_text("<b>No tracked players.</b>", parse_mode="HTML")
            return
        
        keyboard = []
        for p in players:
            keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"map_{p['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "<b>Select a player to see map stats:</b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def map_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    player_id = int(query.data.split("_")[1])
    player = database.get_player_by_internal_id(player_id)
    
    if not player:
        await query.edit_message_text("<b>Player not found.</b>", parse_mode="HTML")
        return
    
    client = leetify_client.client
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        await query.edit_message_text("<b>Failed to fetch player stats.</b>", parse_mode="HTML")
        return
    
    text = formatters.format_player_map_stats(profile, player["name"])
    await query.edit_message_text(text, parse_mode="HTML")

async def match_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = database.get_all_players()
    
    if not players:
        await update.message.reply_text("<b>No tracked players.</b>", parse_mode="HTML")
        return
    
    if len(players) == 1:
        await show_match_list(update, players[0])
        return
    
    keyboard = []
    for p in players:
        keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"match_{p['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "<b>Select a player to see recent matches:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def show_match_list(update: Update, player: dict):
    client = leetify_client.client
    
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        msg = f"❌ Could not fetch matches for {player['name']}"
        if update.message:
            await update.message.reply_text(msg, parse_mode="HTML")
        return
    
    recent_matches = profile.get("recent_matches", [])
    
    if not recent_matches:
        msg = f"No recent matches for {player['name']}"
        if update.message:
            await update.message.reply_text(msg, parse_mode="HTML")
        return
    
    keyboard = []
    for i, match in enumerate(recent_matches[:10], 1):
        map_name = match.get("map_name", "Unknown")
        outcome = match.get("outcome", "Unknown")
        score = match.get("score", [0, 0])
        finished_at = match.get("finished_at", "")
        date_str = ""
        if finished_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%m/%d %H:%M")
            except:
                pass
        
        emoji = "W" if outcome == "win" else "L"
        rating = match.get("leetify_rating", 0)
        r_emoji = "🟢" if rating > 0 else "🔴" if rating < 0 else "🟡"
        label = f"{emoji} {map_name} {score[0]}-{score[1]} {r_emoji}{rating:.2f} ({date_str})"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"matchdetail_{player['id']}_{i-1}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            f"<b>Select a match for {player['name']}:</b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.callback_query.message.reply_text(
            f"<b>Select a match for {player['name']}:</b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def match_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    player_id = int(parts[1])
    player = database.get_player_by_internal_id(player_id)
    
    if not player:
        await query.edit_message_text("<b>Player not found.</b>", parse_mode="HTML")
        return
    
    await show_match_list(query, player)

async def match_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    player_id = int(parts[1])
    match_index = int(parts[2])
    
    player = database.get_player_by_internal_id(player_id)
    if not player:
        await query.edit_message_text("<b>Player not found.</b>", parse_mode="HTML")
        return
    
    client = leetify_client.client
    profile = client.get_player_profile(player["leetify_id"])
    
    if not profile or "error" in profile:
        await query.edit_message_text("<b>Could not fetch player data.</b>", parse_mode="HTML")
        return
    
    recent_matches = profile.get("recent_matches", [])
    if match_index >= len(recent_matches):
        await query.edit_message_text("<b>Match not found.</b>", parse_mode="HTML")
        return
    
    match_data = recent_matches[match_index]
    game_id = match_data.get("id", "")
    
    match_details = client.get_match_details(game_id)
    
    if not match_details:
        await query.edit_message_text("<b>Could not fetch match details.</b>", parse_mode="HTML")
        return
    
    lines = format_full_match_details(match_details, player["leetify_id"])
    msg = "\n".join(lines)
    
    if len(msg) > 4000:
        msg = msg[:4000] + "\n\n... (truncated)"
    
    await query.edit_message_text(msg, parse_mode="HTML")

def format_full_match_details(match_data: dict, player_id: str):
    from datetime import datetime
    
    game_id = match_data.get("id", "Unknown")
    finished_at = match_data.get("finished_at", "")
    if finished_at:
        try:
            dt = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
            date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            date = finished_at
    else:
        date = "Unknown"
    
    map_name = match_data.get("map_name", "Unknown")
    
    team_scores = match_data.get("team_scores", [])
    score_str = "0-0"
    if team_scores:
        scores = [ts.get("score", 0) for ts in team_scores]
        if len(scores) >= 2:
            score_str = f"{scores[0]}-{scores[1]}"
    
    match_link = f"https://leetify.com/app/match/{game_id}"
    
    stats = match_data.get("stats", [])
    
    player_stats = None
    player_team = None
    for p in stats:
        if p.get("steam64_id") == player_id:
            player_stats = p
            player_team = p.get("initial_team_number")
            break
    
    lines = [
        f"<b>🎮 MATCH DETAILS</b>",
        "═" * 30,
        f"📅 {date}",
        f"🗺️ {map_name} | <b>Score:</b> {score_str}",
        f"<a href='{match_link}'>📊 View on Leetify</a>",
        ""
    ]
    
    if player_stats:
        name = player_stats.get("name", "Unknown")
        kills = player_stats.get("total_kills", 0)
        deaths = player_stats.get("total_deaths", 0)
        kd_ratio = player_stats.get("kd_ratio", 0)
        adr = player_stats.get("total_damage", 0) / 24 if player_stats.get("rounds_count", 0) > 0 else 0
        adr = round(adr, 1)
        
        leetify_rating = player_stats.get("leetify_rating", 0)
        ct_rating = player_stats.get("ct_leetify_rating", 0)
        t_rating = player_stats.get("t_leetify_rating", 0)
        
        hs = player_stats.get("accuracy_head", 0) * 100 if player_stats.get("accuracy_head", 0) else 0
        spray = player_stats.get("spray_accuracy", 0) * 100 if player_stats.get("spray_accuracy", 0) else 0
        
        mvps = player_stats.get("mvps", 0)
        assists = player_stats.get("total_assists", 0)
        
        rounds_won = player_stats.get("rounds_won", 0)
        rounds_lost = player_stats.get("rounds_lost", 0)
        
        preaim = player_stats.get("preaim", 0)
        reaction = player_stats.get("reaction_time", 0)
        
        multi1k = player_stats.get("multi1k", 0)
        multi2k = player_stats.get("multi2k", 0)
        multi3k = player_stats.get("multi3k", 0)
        
        lines.append(f"<b>{name}</b>")
        
        is_win = False
        if team_scores and player_team:
            team_score = next((ts for ts in team_scores if ts.get("team_number") == player_team), None)
            if team_score:
                max_score = max(ts.get("score", 0) for ts in team_scores)
                is_win = team_score.get("score", 0) == max_score
        
        if is_win:
            lines.append("<b>✅ WIN</b>")
        else:
            lines.append("<b>❌ LOSE</b>")
        lines.append("")
        
        lines.append("<b>📊 OVERVIEW:</b>")
        lines.append(f"  Kills: <code>{kills}</code>")
        lines.append(f"  Deaths: <code>{deaths}</code>")
        lines.append(f"  K/D: <code>{round(kd_ratio, 2)}</code>")
        lines.append(f"  ADR: <code>{adr}</code>")
        lines.append(f"  Assists: <code>{assists}</code>")
        lines.append(f"  MVPs: <code>{mvps}</code>")
        lines.append("")
        
        lines.append("<b>⭐ RATING:</b>")
        lines.append(f"  Overall: <code>{round(leetify_rating, 2)}</code>")
        lines.append(f"  CT Side: <code>{round(ct_rating, 2)}</code>")
        lines.append(f"  T Side: <code>{round(t_rating, 2)}</code>")
        lines.append("")
        
        lines.append("<b>🎯 DETAILED STATS:</b>")
        lines.append(f"  Headshot: <code>{round(hs, 1)}%</code>")
        lines.append(f"  Spray: <code>{round(spray, 1)}%</code>")
        lines.append(f"  Pre-aim: <code>{round(preaim, 1)}%</code>")
        lines.append(f"  Reaction: <code>{round(reaction * 1000)}ms</code>")
        lines.append("")
        
        lines.append("<b>🎮 ROUNDS:</b>")
        lines.append(f"  Won: <code>{rounds_won}</code>")
        lines.append(f"  Lost: <code>{rounds_lost}</code>")
        lines.append("")
        
        if multi1k or multi2k or multi3k:
            lines.append("<b>💪 MULTI-KILLS:</b>")
            if multi1k:
                lines.append(f"  1K: <code>{multi1k}</code>")
            if multi2k:
                lines.append(f"  2K: <code>{multi2k}</code>")
            if multi3k:
                lines.append(f"  3K: <code>{multi3k}</code>")
            lines.append("")
    
    lines.append("═" * 30)
    lines.append("<b>👥 ALL PLAYERS:</b>")
    
    for p in sorted(stats, key=lambda x: x.get("total_kills", 0), reverse=True)[:10]:
        pname = p.get("name", "Unknown")[:15]
        kills = p.get("total_kills", 0)
        deaths = p.get("total_deaths", 0)
        kd = p.get("kd_ratio", 0)
        dmg = p.get("total_damage", 0)
        adr = round(dmg / 24, 1) if p.get("rounds_count", 0) > 0 else 0
        rating = p.get("leetify_rating", 0)
        mvps = p.get("mvps", 0)
        is_mvp = " ⭐" if mvps > 0 else ""
        lines.append(f"  {pname:<15} <code>{kills}K</code> <code>{deaths}D</code> | <code>{round(kd, 1)}</code> KD | <code>{adr}</code> ADR | <code>{round(rating, 2)}</code> R{is_mvp}")
    
    return lines
