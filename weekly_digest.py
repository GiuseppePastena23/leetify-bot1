import logging
from datetime import datetime, timedelta
import database
import formatters
import config
import discord_client

logger = logging.getLogger(__name__)

async def send_weekly_digest(bot):
    if not config.CHAT_ID:
        logger.error("CHAT_ID not configured")
        return
    
    week_start = database.get_week_start()
    stats = database.get_weekly_stats(week_start)
    
    digest = formatters.format_weekly_digest(stats, week_start)
    
    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            text=digest,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Sent weekly digest to {config.CHAT_ID}")
        
        if config.DISCORD_ENABLED and stats:
            week_stats = []
            for p in stats:
                week_stats.append({
                    "name": p.get("name", "Unknown"),
                    "matches": p.get("matches_played", 0),
                    "winrate": (p.get("wins", 0) / p.get("matches_played", 1)) * 100 if p.get("matches_played", 0) > 0 else 0,
                    "avg_rating": p.get("rating_sum", 0) / p.get("matches_played", 1) if p.get("matches_played", 0) > 0 else 0
                })
            discord_client.send_weekly_digest(week_stats)
            
    except Exception as e:
        logger.error(f"Failed to send weekly digest: {e}")

def get_player_of_the_week():
    week_start = database.get_week_start()
    stats = database.get_weekly_stats(week_start)
    
    if not stats:
        return None
    
    best_player = None
    best_score = -1
    
    for p in stats:
        matches = p.get("matches_played", 0)
        if matches < 3:
            continue
        
        wins = p.get("wins", 0)
        winrate = wins / matches if matches > 0 else 0
        avg_rating = p.get("rating_sum", 0) / matches if matches > 0 else 0
        kd = p.get("total_kills", 0) / p.get("total_deaths", 1) if p.get("total_deaths", 0) > 0 else 0
        
        score = (avg_rating * 2) + (winrate / 10) + (kd * 0.5)
        
        if score > best_score:
            best_score = score
            best_player = {
                "name": p.get("name", "Unknown"),
                "matches": matches,
                "wins": wins,
                "winrate": winrate * 100,
                "avg_rating": avg_rating,
                "kd": kd,
                "total_kills": p.get("total_kills", 0),
                "total_deaths": p.get("total_deaths", 0)
            }
    
    return best_player

async def send_player_of_week_alert(bot):
    player = get_player_of_the_week()
    
    if not player:
        return
    
    text = (
        f"⭐ <b>Player of the Week</b> ⭐\n"
        "═" * 25 + "\n\n"
        f"🏆 <b>{player['name']}</b>\n\n"
        f"📊 Matches: {player['matches']}\n"
        f"✅ Wins: {player['wins']}\n"
        f"📈 Win Rate: {player['winrate']:.1f}%\n"
        f"⭐ Avg Rating: {player['avg_rating']:.2f}\n"
        f"🎯 K/D: {player['kd']:.2f}"
    )
    
    if config.CHAT_ID:
        try:
            await bot.send_message(
                chat_id=config.CHAT_ID,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send player of week: {e}")
    
    if config.DISCORD_ENABLED:
        discord_client.send_player_of_week(player["name"], player)

def get_next_digest_time():
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
    
    return next_digest

async def send_weekly_analysis(bot):
    if not config.CHAT_ID:
        logger.error("CHAT_ID not configured")
        return
    
    week_start = database.get_week_start()
    stats = database.get_weekly_stats(week_start)
    
    if not stats:
        return
    
    player_of_week = get_player_of_the_week()
    
    team_stats = {
        "total_matches": 0,
        "total_wins": 0,
        "total_losses": 0,
        "total_kills": 0,
        "total_deaths": 0,
        "avg_rating": 0,
    }
    
    ratings = []
    for p in stats:
        matches = p.get("matches_played", 0)
        wins = p.get("wins", 0)
        losses = p.get("losses", 0)
        rating_sum = p.get("rating_sum", 0)
        
        team_stats["total_matches"] += matches
        team_stats["total_wins"] += wins
        team_stats["total_losses"] += losses
        team_stats["total_kills"] += p.get("total_kills", 0)
        team_stats["total_deaths"] += p.get("total_deaths", 0)
        
        if matches > 0:
            ratings.append(rating_sum / matches)
    
    if ratings:
        team_stats["avg_rating"] = sum(ratings) / len(ratings)
    
    team_kd = team_stats["total_kills"] / team_stats["total_deaths"] if team_stats["total_deaths"] > 0 else 0
    team_wr = (team_stats["total_wins"] / team_stats["total_matches"] * 100) if team_stats["total_matches"] > 0 else 0
    
    by_rating = sorted(stats, key=lambda x: x.get("rating_sum", 0) / max(x.get("matches_played", 1), 1), reverse=True)
    by_wr = sorted(stats, key=lambda x: x.get("wins", 0) / max(x.get("matches_played", 1), 1), reverse=True)
    
    analysis_text = (
        f"<b>📊 Weekly Analysis</b>\n"
        "═" * 25 + "\n\n"
        f"<b>🎮 Team Stats</b>\n"
        f"Total Matches: {team_stats['total_matches']}\n"
        f"Win Rate: {team_wr:.1f}% ({team_stats['total_wins']}W - {team_stats['total_losses']}L)\n"
        f"Team K/D: {team_kd:.2f}\n"
        f"Avg Rating: {team_stats['avg_rating']:.2f}\n\n"
    )
    
    if player_of_week:
        analysis_text += (
            f"<b>⭐ Player of the Week</b>\n"
            f"{player_of_week['name']}\n"
            f"Rating: {player_of_week['avg_rating']:.2f} | WR: {player_of_week['winrate']:.1f}% | K/D: {player_of_week['kd']:.2f}\n\n"
        )
    
    analysis_text += "<b>🏆 Top by Rating</b>\n"
    for i, p in enumerate(by_rating[:3], 1):
        matches = p.get("matches_played", 0)
        avg = p.get("rating_sum", 0) / matches if matches > 0 else 0
        analysis_text += f"{i}. {p.get('name', 'Unknown')}: {avg:.2f}\n"
    
    analysis_text += "\n<b>🔥 Hot Streak (Win Rate)</b>\n"
    for i, p in enumerate(by_wr[:3], 1):
        matches = p.get("matches_played", 0)
        wr = (p.get("wins", 0) / matches * 100) if matches > 0 else 0
        analysis_text += f"{i}. {p.get('name', 'Unknown')}: {wr:.1f}%\n"
    
    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            text=analysis_text,
            parse_mode="HTML"
        )
        logger.info(f"Sent weekly analysis to {config.CHAT_ID}")
    except Exception as e:
        logger.error(f"Failed to send weekly analysis: {e}")
