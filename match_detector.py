import logging
from datetime import datetime, timedelta
from telegram import Bot
import database
import leetify_client
import formatters
import config
import discord_client

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
        
        player_match_info = {}
        
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
                    
                    player_match_info[player["leetify_id"]] = {
                        "rating": rating,
                        "isWin": is_win,
                        "outcome": "Win" if is_win else "Loss"
                    }
                    break
        
        score = match_details.get("score", {})
        match_info = {
            "map_name": match_details.get("map_name", "Unknown"),
            "score": f"{score.get('ct', 0)}-{score.get('t', 0)}",
            "rating": 0,
            "rating_change": 0,
            "outcome": "Unknown"
        }
        
        for leetify_id, info in player_match_info.items():
            match_info["rating"] = info["rating"]
            match_info["outcome"] = info["outcome"]
        
        report = formatters.format_match_report(match_details, tracked)
        new_reports.append({
            "report": report,
            "match_info": match_info,
            "players": tracked
        })
    
    return new_reports

async def send_match_report(report: str, match_data: dict = None, players: list = None):
    if not bot:
        logger.error("Bot not initialized")
        return
    
    if config.CHAT_ID:
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
    
    if match_data and players and config.DISCORD_ENABLED:
        for player in players:
            try:
                rating = match_data.get("rating", 0)
                rating_change = match_data.get("rating_change", 0)
                outcome = "Win" if match_data.get("isWin", False) else "Loss"
                discord_client.send_match_alert(
                    player_name=player.get("name", "Unknown"),
                    match_result=outcome,
                    rating=rating,
                    rating_change=rating_change,
                    map_name=match_data.get("map_name", "Unknown"),
                    score=match_data.get("score", "0-0")
                )
            except Exception as e:
                logger.error(f"Failed to send Discord alert: {e}")

async def check_and_send_reports():
    try:
        reports = check_for_new_matches()
        for report_data in reports:
            report = report_data.get("report", "")
            await send_match_report(report)
            
            if config.DISCORD_ENABLED:
                for player in report_data.get("players", []):
                    match_info = report_data.get("match_info", {})
                    try:
                        rating = match_info.get("rating", 0)
                        rating_change = match_info.get("rating_change", 0)
                        discord_client.send_match_alert(
                            player_name=player.get("name", "Unknown"),
                            match_result=match_info.get("outcome", "Unknown"),
                            rating=rating,
                            rating_change=rating_change,
                            map_name=match_info.get("map_name", "Unknown"),
                            score=match_info.get("score", "0-0")
                        )
                    except Exception as e:
                        logger.error(f"Failed to send Discord alert: {e}")
    except Exception as e:
        logger.error(f"Error in check_and_send_reports: {e}")
