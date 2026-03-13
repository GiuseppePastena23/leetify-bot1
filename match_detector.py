import logging
from datetime import datetime, timedelta
from telegram import Bot
import database
import leetify_client
import formatters
import config

logger = logging.getLogger(__name__)

client = leetify_client.client
bot = None

def set_bot(bot_instance):
    global bot
    bot = bot_instance

def check_for_new_matches():
    players = database.get_all_players()
    
    if not players:
        return []
    
    player_matches = {}
    
    for player in players:
        leetify_id = player["leetify_id"]
        matches_data = client.get_player_matches(leetify_id, limit=10)
        
        if not matches_data or "error" in matches_data:
            continue
        
        matches = matches_data.get("matches", [])
        
        for match in matches:
            game_id = match.get("id")
            if not game_id:
                continue
            
            if game_id in player_matches:
                player_matches[game_id]["tracked_players"].append(player)
            else:
                player_matches[game_id] = {
                    "match_data": match,
                    "tracked_players": [player]
                }
    
    new_reports = []
    reported_matches = database.get_all_reported_match_ids()
    
    for game_id, data in player_matches.items():
        if game_id in reported_matches:
            continue
        
        tracked = data["tracked_players"]
        if len(tracked) < 1:
            continue
        
        match_details = client.get_match_details(game_id)
        
        if not match_details or "error" in match_details:
            logger.warning(f"Could not fetch details for match {game_id}")
            continue
        
        score = match_details.get("score", {})
        score_str = f"{score.get('ct', 0)}-{score.get('t', 0)}"
        database.mark_match_reported(game_id, score_str)
        
        for player in tracked:
            week_start = database.get_week_start()
            players_data = match_details.get("players", [])
            
            for p in players_data:
                if p.get("id") == player["leetify_id"]:
                    is_win = p.get("isWin", False)
                    kills = p.get("kills", 0)
                    deaths = p.get("deaths", 0)
                    rating = p.get("rating", 0)
                    mvp = 1 if p.get("isMvp", False) else 0
                    
                    database.update_weekly_stats(
                        player["id"], 
                        week_start, 
                        is_win, 
                        kills, 
                        deaths, 
                        rating,
                        mvp
                    )
                    break
        
        report = formatters.format_match_report(match_details, tracked)
        new_reports.append(report)
    
    return new_reports

async def send_match_report(report: str):
    if not bot:
        logger.error("Bot not initialized")
        return
    
    if not config.CHAT_ID:
        logger.error("CHAT_ID not configured")
        return
    
    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            text=report,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Sent match report to {config.CHAT_ID}")
    except Exception as e:
        logger.error(f"Failed to send match report: {e}")

async def check_and_send_reports():
    try:
        reports = check_for_new_matches()
        for report in reports:
            await send_match_report(report)
    except Exception as e:
        logger.error(f"Error in check_and_send_reports: {e}")
