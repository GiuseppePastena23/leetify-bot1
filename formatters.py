from typing import Optional, Any
from datetime import datetime
import html

def get_nested(data: dict, *keys, default=0) -> Any:
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    if result is None:
        return default
    if isinstance(result, (int, float)):
        return result
    return default

def esc(text):
    return html.escape(str(text))

def format_match_list(matches: list, player_name: str) -> str:
    if not matches:
        return f"<b>No matches found for {player_name}</b>"
    
    lines = [
        f"<b>🎮 Match History - {player_name}</b>",
        "═" * 25,
        ""
    ]
    
    for i, match in enumerate(matches[:10], 1):
        map_name = match.get("map_name", "Unknown")
        outcome = match.get("outcome", "?")
        score = match.get("score", [0, 0])
        rating = match.get("leetify_rating", 0)
        
        emoji = "✅" if outcome == "win" else "❌" if outcome == "loss" else "➖"
        
        lines.append(f"{i}. {emoji} {map_name} | {score[0]}-{score[1]} | ⭐{rating:.2f}")
    
    return "\n".join(lines)

def format_match_report(match_data: dict, tracked_players: list) -> str:
    game_id = match_data.get("id", "Unknown")
    date = match_data.get("date", "")
    if date:
        try:
            dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
            date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    score = match_data.get("score", {})
    score_ct = score.get("ct", 0)
    score_t = score.get("t", 0)
    score_str = f"{score_ct}-{score_t}"
    
    match_link = f"https://leetify.com/app/match/{game_id}"
    players = match_data.get("players", [])
    tracked_player_ids = {p["id"] for p in tracked_players}
    
    team_stats = {}
    for player in players:
        team_id = player.get("teamId")
        if team_id not in team_stats:
            team_stats[team_id] = {"players": [], "is_win": player.get("isWin", False)}
        team_stats[team_id]["players"].append(player)
    
    opponent_avg_rating = 0
    opponent_count = 0
    tracked_team_id = None
    
    for team_id, stats in team_stats.items():
        for p in stats["players"]:
            if p.get("id") in tracked_player_ids:
                tracked_team_id = team_id
                break
        if tracked_team_id and team_id != tracked_team_id:
            for p in stats["players"]:
                rating = p.get("rating", 0)
                if rating:
                    opponent_avg_rating += rating
                    opponent_count += 1
    
    if opponent_count > 0:
        opponent_avg_rating /= opponent_count
    
    lines = [
        f"<b>🎮 MATCH REPORT</b>",
        "═" * 20,
        f"<b>📅 Date:</b> {date}",
        f"<a href='{match_link}'>📊 View on Leetify</a>",
        f"<b>⚔️ Score:</b> {score_str}",
        ""
    ]
    
    for team_id, stats in team_stats.items():
        is_tracked = team_id == tracked_team_id
        is_win = stats["is_win"]
        
        if is_tracked:
            if is_win:
                lines.append("<b>🏆 YOUR TEAM WIN!</b>")
            else:
                lines.append("<b>💀 YOUR TEAM LOST</b>")
        else:
            lines.append("<b>⚔️ OPPONENTS</b>")
        
        lines.append("─" * 20)
        
        for p in stats["players"]:
            p_id = p.get("id", "")
            name = esc(p.get("name", "Unknown"))
            kills = p.get("kills", 0)
            deaths = p.get("deaths", 0)
            assists = p.get("assists", 0)
            kd = round(kills / deaths, 2) if deaths > 0 else kills
            adr = p.get("adr", 0)
            if not adr:
                total_dmg = p.get("totalDamage", p.get("damage", 0))
                rounds = p.get("rounds", 24)
                adr = round(total_dmg / rounds, 1) if rounds > 0 else 0
            kast = p.get("kast", 0)
            rating = p.get("rating", p.get("leetifyRating", 0))
            mvp = p.get("isMvp", p.get("mvp", False))
            
            indicator = "🟢" if p_id in tracked_player_ids else "⚪"
            mvp_indicator = " ⭐" if mvp else ""
            
            lines.append(
                f"{indicator} <b>{name}</b>{mvp_indicator}: {kills}K {deaths}D {assists}A | "
                f"<code>{kd}</code> KD | <code>{adr}</code> ADR | <code>{kast}%</code> KAST | <code>{rating:.2f}</code> R"
            )
        
        lines.append("")
    
    if opponent_avg_rating > 0:
        lines.append(f"🔴 Opponents avg rating: <code>{round(opponent_avg_rating, 2)}</code>")
        lines.append("")
    
    improvements = []
    for team_id, stats in team_stats.items():
        is_tracked = team_id == tracked_team_id
        if not is_tracked:
            continue
            
        for p in stats["players"]:
            if p.get("id") not in tracked_player_ids:
                continue
            
            areas = p.get("areasToImprove", [])
            if areas:
                name = esc(p.get("name", "Unknown"))
                areas_str = ", ".join(areas[:3])
                improvements.append(f"• <b>{name}</b>: {areas_str}")
    
    if improvements:
        lines.append("<b>📈 AREAS TO IMPROVE:</b>")
        for imp in improvements:
            lines.append(imp)
    
    return "\n".join(lines)

def format_player_stats(profile: dict) -> str:
    name = esc(profile.get("name", "Unknown"))
    leetify_id = profile.get("id", "")
    profile_link = f"https://leetify.com/profile/{leetify_id}"
    
    win_rate = profile.get("winrate", 0)
    if win_rate and win_rate <= 1.0:
        win_rate = round(win_rate * 100, 1)
    
    matches = profile.get("total_matches", 0)
    
    rating = profile.get("rating", {})
    ranks = profile.get("ranks", {})
    display_rating = ranks.get("leetify", rating.get("aim", 0))
    stats = profile.get("stats", {})
    
    rating_color = get_rating_color(display_rating)
    
    lines = [
        f"<b>📊 PLAYER STATS</b>",
        "═" * 25,
        f"<b>{name}</b>",
        f"<a href='{profile_link}'>🔗 View Leetify Profile</a>",
        "",
        f"<b>🎮 Matches:</b> {matches}",
        f"<b>⭐ Leetify Rating:</b> <code>{round(display_rating, 2)}</code>",
        f"<b>🏆 Win Rate:</b> {win_rate}%",
        ""
    ]
    
    if rating:
        lines.append("<b>🎯 RATINGS</b>")
        lines.append("─" * 25)
        lines.append(f"  🎯 Aim: <code>{round(rating.get('aim', 0), 2)}</code>")
        lines.append(f"  👀 Positioning: <code>{round(rating.get('positioning', 0), 2)}</code>")
        lines.append(f"  💣 Utility: <code>{round(rating.get('utility', 0), 2)}</code>")
        lines.append(f"  🎰 Clutch: <code>{round(rating.get('clutch', 0), 2)}</code>")
        lines.append(f"  ⚔️ Opening: <code>{round(rating.get('opening', 0), 2)}</code>")
        lines.append(f"  🛡️ CT Side: <code>{round(rating.get('ct_leetify', 0), 2)}</code>")
        lines.append(f"  🔴 T Side: <code>{round(rating.get('t_leetify', 0), 2)}</code>")
    
    if stats:
        lines.append("")
        lines.append("<b>📈 DETAILED STATS</b>")
        lines.append("─" * 25)
        lines.append(f"  🎯 Headshot: <code>{round(stats.get('accuracy_head', 0), 1)}%</code>")
        lines.append(f"  ⚡ Reaction: <code>{round(stats.get('reaction_time_ms', 0))}ms</code>")
        lines.append(f"  🔫 Spray: <code>{round(stats.get('spray_accuracy', 0), 1)}%</code>")
        lines.append(f"  👀 Pre-aim: <code>{round(stats.get('preaim', 0), 1)}%</code>")
        lines.append(f"  💣 Utility/Dmg: <code>{round(stats.get('utility_on_death_avg', 0))}</code>")
        lines.append(f"  🔄 Counter-strafe: <code>{round(stats.get('counter_strafing_good_shots_ratio', 0), 1)}%</code>")
        lines.append(f"  💥 Trade Kills: <code>{round(stats.get('trade_kills_success_percentage', 0), 1)}%</code>")
        lines.append(f"  💥 Trade Deaths: <code>{round(stats.get('traded_deaths_success_percentage', 0), 1)}%</code>")
        lines.append(f"  💣 HE Dmg: <code>{round(stats.get('he_foes_damage_avg', 0), 1)}</code>")
        lines.append(f"  💣 Flashes: <code>{round(stats.get('flashbang_thrown', 0), 1)}</code>")
        lines.append(f"  ⚔️ T Opening: <code>{round(stats.get('t_opening_duel_success_percentage', 0), 1)}%</code>")
        lines.append(f"  ⚔️ CT Opening: <code>{round(stats.get('ct_opening_duel_success_percentage', 0), 1)}%</code>")
    
    premier = ranks.get("premier", 0)
    wingman = ranks.get("wingman", 0)
    faceit = ranks.get("faceit", 0)
    
    if premier or wingman or faceit:
        lines.append("")
        lines.append("<b>🏅 RANKS</b>")
        lines.append("─" * 25)
        if premier:
            lines.append(f"  🅿️ Premier: <code>{premier}</code>")
        if wingman:
            lines.append(f"  🗡️ Wingman: <code>{wingman}</code>")
        if faceit:
            lines.append(f"  🎯 FACEIT: <code>{faceit}</code>")
    
    competitive = ranks.get("competitive", [])
    if competitive:
        lines.append("")
        lines.append("<b>🗺️ MAP RANKS</b>")
        lines.append("─" * 25)
        for m in competitive:
            map_name = m.get("map_name", "Unknown")
            rank = m.get("rank", 0)
            lines.append(f"  {map_name}: <code>{rank}</code>")
    
    return "\n".join(lines)

def get_rating_color(rating):
    if rating >= 1.3:
        return "green"
    elif rating >= 1.1:
        return "lightgreen"
    elif rating >= 0.9:
        return "yellow"
    elif rating >= 0.7:
        return "orange"
    else:
        return "red"

def format_csstats_player(data: dict) -> str:
    if not data:
        return "❌ Player not found on CSStats"
    
    name = esc(data.get("nickname", "Unknown"))
    steam_id = data.get("steamId", "")
    profile_link = f"https://csstats.gg/player/{steam_id}"
    
    stats = data.get("stats", {})
    wins = data.get("wins", 0)
    losses = data.get("losses", 0)
    matches = wins + losses
    wr = round((wins / matches * 100), 1) if matches > 0 else 0
    
    kd = stats.get("kd", 0)
    adr = stats.get("adr", 0)
    hs = stats.get("hs", 0)
    bhs = stats.get("bhs", 0)
    matches_count = stats.get("matches", 0)
    
    lines = [
        f"<b>📊 CSSTATS.GG</b>",
        "═" * 25,
        f"<b>{name}</b>",
        f"<a href='{profile_link}'>🔗 View Profile</a>",
        "",
        f"<b>🎮 Matches:</b> {matches_count}",
        f"<b>🏆 Win Rate:</b> {wr}% ({wins}W/{losses}L)",
        f"<b>💀 K/D:</b> <code>{kd}</code>",
        f"<b>💥 ADR:</b> <code>{adr}</code>",
        f"<b>🎯 Headshot:</b> <code>{hs}%</code>",
        f"<b>💣 Bombs Defused:</b> <code>{bhs}</code>",
    ]
    
    return "\n".join(lines)

def format_csgrind_player(data: dict) -> str:
    if not data:
        return "❌ Player not found on CSGrind"
    
    name = esc(data.get("name", data.get("nickname", "Unknown")))
    player_id = data.get("id", data.get("player_id", ""))
    profile_link = f"https://csgrind.com/id/{player_id}"
    
    faceit = data.get("faceit", {})
    premier = data.get("premier", {})
    wingman = data.get("wingman", {})
    
    lines = [
        f"<b>📊 CSGRIND</b>",
        "═" * 25,
        f"<b>{name}</b>",
        f"<a href='{profile_link}'>🔗 View Profile</a>",
        ""
    ]
    
    if premier:
        elo = premier.get("elo", "N/A")
        kd = premier.get("kd", "N/A")
        win_rate = premier.get("winRate", "N/A")
        matches = premier.get("matches", "N/A")
        lines.append("<b>🅿️ PREMIER</b>")
        lines.append(f"  ELO: <code>{elo}</code>")
        lines.append(f"  K/D: <code>{kd}</code>")
        lines.append(f"  Win Rate: <code>{win_rate}%</code>")
        lines.append(f"  Matches: <code>{matches}</code>")
    
    if faceit:
        elo = faceit.get("elo", "N/A")
        kd = faceit.get("kd", "N/A")
        win_rate = faceit.get("winRate", "N/A")
        matches = faceit.get("matches", "N/A")
        lines.append("")
        lines.append("<b>🎯 FACEIT</b>")
        lines.append(f"  ELO: <code>{elo}</code>")
        lines.append(f"  K/D: <code>{kd}</code>")
        lines.append(f"  Win Rate: <code>{win_rate}%</code>")
        lines.append(f"  Matches: <code>{matches}</code>")
    
    if wingman:
        elo = wingman.get("elo", "N/A")
        kd = wingman.get("kd", "N/A")
        win_rate = wingman.get("winRate", "N/A")
        matches = wingman.get("matches", "N/A")
        lines.append("")
        lines.append("<b>🗡️ WINGMAN</b>")
        lines.append(f"  ELO: <code>{elo}</code>")
        lines.append(f"  K/D: <code>{kd}</code>")
        lines.append(f"  Win Rate: <code>{win_rate}%</code>")
        lines.append(f"  Matches: <code>{matches}</code>")
    
    return "\n".join(lines)

def format_faceit_player(player_info: dict, stats: dict) -> str:
    if not player_info:
        return ""
    
    name = esc(player_info.get("nickname", "Unknown"))
    player_id = player_info.get("player_id", "")
    faceit_url = f"https://faceit.com/players/{player_id}"
    
    if not stats:
        return f"<b>📊 FACEIT</b>\n{name}\n(No stats available)"
    
    lifetime = stats.get("lifetime", {})
    
    lines = [
        f"<b>📊 FACEIT</b>",
        "═" * 25,
        f"<b>{name}</b>",
        f"<a href='{faceit_url}'>🔗 View Profile</a>",
        ""
    ]
    
    if lifetime:
        lines.append("<b>📈 Lifetime Stats</b>")
        lines.append(f"  🎮 Matches: <code>{lifetime.get('matches', 'N/A')}</code>")
        lines.append(f"  🏆 Win Rate: <code>{lifetime.get('winRate', 'N/A')}%</code>")
        lines.append(f"  💀 K/D: <code>{lifetime.get('kdr', 'N/A')}</code>")
        lines.append(f"  ⭐ ELO: <code>{lifetime.get('elo', 'N/A')}</code>")
        lines.append(f"  🎯 HS: <code>{lifetime.get('headshots', 'N/A')}%</code>")
        lines.append(f"  💥 K/R: <code>{lifetime.get('kr', 'N/A')}</code>")
    
    return "\n".join(lines)

def format_compare(p1_data: dict, p2_data: dict) -> str:
    p1_name = esc(p1_data.get("name", "Player 1"))
    p2_name = esc(p2_data.get("name", "Player 2"))
    
    p1_ranks = p1_data.get("ranks", {})
    p2_ranks = p2_data.get("ranks", {})
    
    p1_rating = p1_ranks.get("leetify", p1_data.get("rating", {}).get("aim", 0))
    p2_rating = p2_ranks.get("leetify", p2_data.get("rating", {}).get("aim", 0))
    
    p1_wr = p1_data.get("winrate", 0) * 100 if p1_data.get("winrate", 0) else 0
    p2_wr = p2_data.get("winrate", 0) * 100 if p2_data.get("winrate", 0) else 0
    
    p1_matches = p1_data.get("total_matches", 0)
    p2_matches = p2_data.get("total_matches", 0)
    
    p1_stats = p1_data.get("stats", {})
    p2_stats = p2_data.get("stats", {})
    
    p1_hs = p1_stats.get("accuracy_head", 0)
    p2_hs = p2_stats.get("accuracy_head", 0)
    
    p1_reaction = p1_stats.get("reaction_time_ms", 0)
    p2_reaction = p2_stats.get("reaction_time_ms", 0)
    
    def diff(val1, val2):
        if val1 is None:
            val1 = 0
        if val2 is None:
            val2 = 0
        d = round(val1 - val2, 2)
        if d > 0:
            return f"+{d} 🟢"
        elif d < 0:
            return f"{d} 🔴"
        return "0 ⚪"
    
    lines = [
        f"<b>⚔️ PLAYER COMPARE</b>",
        "═" * 35,
        f"         <b>{p1_name[:12]:<12}</b> | <b>{p2_name[:12]:<12}</b> | <b>Diff</b>",
        "─" * 50,
        f"<b>Rating</b> | {p1_rating:<12.2f} | {p2_rating:<12.2f} | {diff(p1_rating, p2_rating)}",
        f"<b>Win%</b>   | {p1_wr:<12.1f} | {p2_wr:<12.1f} | {diff(p1_wr, p2_wr)}",
        f"<b>Matches</b>| {p1_matches:<12} | {p2_matches:<12} | {p1_matches - p2_matches:+d}",
        f"<b>HS%</b>    | {p1_hs:<12.1f} | {p2_hs:<12.1f} | {diff(p1_hs, p2_hs)}",
        f"<b>Reaction</b>| {int(p1_reaction):<12d} | {int(p2_reaction):<12d} | {int(p1_reaction - p2_reaction):+d}ms",
    ]
    
    return "\n".join(lines)

def format_leaderboard(players_data: list, week_start: str) -> str:
    if not players_data:
        return "No data available for this week."
    
    lines = [
        f"<b>🏆 WEEKLY LEADERBOARD</b>",
        "═" * 25,
        f"📅 Week: {week_start}",
        ""
    ]
    
    by_kd = []
    by_rating = []
    by_kills = []
    by_wr = []
    
    for p in players_data:
        name = esc(p.get("name", "Unknown"))
        matches = p.get("matches_played", 0)
        if matches == 0:
            continue
            
        wins = p.get("wins", 0)
        kills = p.get("total_kills", 0)
        deaths = p.get("total_deaths", 0)
        rating = p.get("rating_sum", 0) / matches if matches > 0 else 0
        wr = (wins / matches) * 100 if matches > 0 else 0
        
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        
        by_kd.append((name, kd))
        by_rating.append((name, rating))
        by_kills.append((name, kills))
        by_wr.append((name, wr))
    
    by_kd.sort(key=lambda x: x[1], reverse=True)
    by_rating.sort(key=lambda x: x[1], reverse=True)
    by_kills.sort(key=lambda x: x[1], reverse=True)
    by_wr.sort(key=lambda x: x[1], reverse=True)
    
    lines.append("<b>💀 K/D RATING</b>")
    medals = ["🥇", "🥈", "🥉", "  ", "  "]
    for i, (name, val) in enumerate(by_kd[:5], 1):
        lines.append(f"{medals[i-1]} {i}. {name}: <code>{val}</code>")
    lines.append("")
    
    lines.append("<b>⚡ MOST KILLS</b>")
    for i, (name, val) in enumerate(by_kills[:5], 1):
        lines.append(f"{medals[i-1]} {i}. {name}: <code>{val}</code>")
    lines.append("")
    
    lines.append("<b>⭐ HIGHEST RATING</b>")
    for i, (name, val) in enumerate(by_rating[:5], 1):
        lines.append(f"{medals[i-1]} {i}. {name}: <code>{round(val, 2)}</code>")
    lines.append("")
    
    lines.append("<b>🏆 BEST WIN RATE</b>")
    for i, (name, val) in enumerate(by_wr[:5], 1):
        lines.append(f"{medals[i-1]} {i}. {name}: <code>{round(val, 1)}%</code>")
    
    return "\n".join(lines)

def format_weekly_digest(players_data: list, week_start: str) -> str:
    if not players_data:
        return "No matches played this week."
    
    lines = [
        f"<b>📊 WEEKLY DIGEST</b>",
        "═" * 25,
        f"📅 Week of {week_start}",
        ""
    ]
    
    for p in players_data:
        name = esc(p.get("name", "Unknown"))
        matches = p.get("matches_played", 0)
        wins = p.get("wins", 0)
        losses = p.get("losses", 0)
        kills = p.get("total_kills", 0)
        deaths = p.get("total_deaths", 0)
        rating = p.get("rating_sum", 0) / matches if matches > 0 else 0
        mvp = p.get("mvp_count", 0)
        
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        wr = round((wins / matches) * 100, 1) if matches > 0 else 0
        
        lines.append(
            f"<b>👤 {name}</b>\n"
            f"  🎮 <code>{matches}</code> matches | <code>{wins}W</code> <code>{losses}L</code> (<code>{wr}%</code> WR)\n"
            f"  💀 <code>{kills}</code>K <code>{deaths}</code>D (<code>{kd}</code> K/D)\n"
            f"  ⭐ Rating: <code>{round(rating, 2)}</code> | MVP: <code>{mvp}</code>\n"
        )
    
    return "\n".join(lines)

def format_player_list(players: list) -> str:
    if not players:
        return "<b>No players tracked yet.</b>\n\nUse /add to add players to track."
    
    lines = [
        f"<b>👥 TRACKED PLAYERS</b>",
        "═" * 25,
        ""
    ]
    
    for p in players:
        name = esc(p.get("name", "Unknown"))
        leetify_id = p.get("leetify_id", "")
        link = f"https://leetify.com/profile/{leetify_id}"
        lines.append(f"• <a href='{link}'>{name}</a>")
    
    lines.append("")
    lines.append(f"<i>Total: {len(players)} player(s)</i>")
    
    return "\n".join(lines)

def format_settings() -> str:
    from config import POLLING_INTERVAL, WEEKLY_DIGEST_DAY, WEEKLY_DIGEST_HOUR, DISCORD_ENABLED, LOG_LEVEL
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    lines = [
        f"<b>⚙️ SETTINGS</b>",
        "═" * 25,
        f"⏱️ Polling interval: <code>{POLLING_INTERVAL} seconds</code>",
        f"📅 Weekly digest: <code>{days[WEEKLY_DIGEST_DAY]} at {WEEKLY_DIGEST_HOUR}:00</code>",
        f"📝 Logging: <code>{LOG_LEVEL}</code>",
        f"💬 Discord: <code>{'Enabled' if DISCORD_ENABLED else 'Disabled'}</code>",
    ]
    
    return "\n".join(lines)

def format_player_map_stats(profile: dict, player_name: str) -> str:
    maps = profile.get("maps", [])
    
    if not maps:
        return f"<b>🗺️ MAP STATS - {esc(player_name)}</b>\n\nNo map data available."
    
    lines = [
        f"<b>🗺️ MAP STATS - {esc(player_name)}</b>",
        "═" * 25,
        ""
    ]
    
    for m in maps:
        map_name = m.get("map_name", "Unknown")
        wins = m.get("wins", 0)
        losses = m.get("losses", 0)
        matches = wins + losses
        wr = round((wins / matches * 100), 1) if matches > 0 else 0
        rating = m.get("rating", 0)
        kd = m.get("kd", 0)
        adr = m.get("adr", 0)
        
        wr_emoji = "🟢" if wr >= 50 else "🟡" if wr >= 40 else "🔴"
        
        lines.append(
            f"<b>{map_name}</b>\n"
            f"  🎮 <code>{matches}</code> | {wr_emoji} <code>{wr}%</code> WR | ⭐ <code>{round(rating, 2)}</code>\n"
            f"  💀 K/D: <code>{round(kd, 2)}</code> | 💥 ADR: <code>{round(adr, 1)}</code>\n"
        )
    
    return "\n".join(lines)

def format_full_match_details_v2(match_data: dict, player_leetify_id: str) -> str:
    game_id = match_data.get("id", "Unknown")
    
    # Date
    date_raw = match_data.get("finished_at", match_data.get("date", ""))
    date = "Unknown"
    if date_raw:
        try:
            if isinstance(date_raw, str):
                dt = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
                date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            date = str(date_raw)
    
    map_name = match_data.get("map_name", "Unknown")
    
    # Handle team scores - team numbers can be 2 and 3
    team_scores = match_data.get("team_scores", [])
    score_str = "0-0"
    if team_scores and len(team_scores) >= 2:
        s1 = team_scores[0].get("score", 0)
        s2 = team_scores[1].get("score", 0)
        score_str = f"{s1}-{s2}"
    
    match_link = f"https://leetify.com/app/match/{game_id}"
    
    # Players are in "stats" field
    players = match_data.get("stats", [])
    print(f"[FORMATTER] Found {len(players)} players in stats")
    
    # Find our player
    player_data = None
    player_name = "Unknown"
    
    for p in players:
        pid = p.get("id", "")
        if str(pid) == str(player_leetify_id):
            player_data = p
            player_name = p.get("name", "Unknown")
            break
    
    # If not found, try finding by steam64_id
    if not player_data:
        for p in players:
            sid = p.get("steam64_id", "")
            if str(sid) == str(player_leetify_id):
                player_data = p
                player_name = p.get("name", "Unknown")
                break
    
    # If still not found, use first player
    if not player_data and players:
        player_data = players[0]
        player_name = player_data.get("name", "Unknown")
    
    print(f"[FORMATTER] Selected player: {player_name}")
    print(f"[FORMATTER] Player data: {player_data}")
    
    # Extract all stats from player data - use CORRECT field names from API
    kills = player_data.get("total_kills", 0) if player_data else 0
    deaths = player_data.get("total_deaths", 0) if player_data else 0
    assists = player_data.get("total_assists", 0) if player_data else 0
    kd = player_data.get("kd_ratio", 0) if player_data else 0
    
    # ADR - total_damage / rounds_count
    total_damage = player_data.get("total_damage", 0) if player_data else 0
    rounds_count = player_data.get("rounds_count", 19) if player_data else 19
    adr = round(total_damage / rounds_count, 1) if rounds_count > 0 else 0
    
    # ACS (same as ADR in this API)
    acs = adr
    
    # Rating
    rating = player_data.get("leetify_rating", 0) if player_data else 0
    
    # Headshot percentage
    hs = player_data.get("accuracy_head", 0) * 100 if player_data else 0
    
    # MVP
    mvps = player_data.get("mvps", 0) if player_data else 0
    
    # Ratings
    ct_rating = player_data.get("ct_leetify_rating", 0) if player_data else 0
    t_rating = player_data.get("t_leetify_rating", 0) if player_data else 0
    dpr = player_data.get("dpr", 0) if player_data else 0
    
    # Accuracy stats
    accuracy = player_data.get("accuracy", 0) * 100 if player_data else 0
    accuracy_enemy = player_data.get("accuracy_enemy_spotted", 0) * 100 if player_data else 0
    
    # Shooting stats
    shots_fired = player_data.get("shots_fired", 0) if player_data else 0
    shots_hit = player_data.get("shots_hit_foe", 0) if player_data else 0
    
    # Spray & Pre-aim
    spray = player_data.get("spray_accuracy", 0) * 100 if player_data else 0
    preaim = player_data.get("preaim", 0) if player_data else 0
    
    # Reaction time
    reaction = player_data.get("reaction_time", 0) if player_data else 0
    
    # Utility stats
    utility_dmg = player_data.get("utility_on_death_avg", 0) if player_data else 0
    he_thrown = player_data.get("he_thrown", 0) if player_data else 0
    molotov_thrown = player_data.get("molotov_thrown", 0) if player_data else 0
    smoke_thrown = player_data.get("smoke_thrown", 0) if player_data else 0
    he_dmg = player_data.get("he_foes_damage_avg", 0) if player_data else 0
    
    # Flash stats
    flash_thrown = player_data.get("flashbang_thrown", 0) if player_data else 0
    flash_hit_foe = player_data.get("flashbang_hit_foe", 0) if player_data else 0
    flash_leading_kill = player_data.get("flashbang_leading_to_kill", 0) if player_data else 0
    flash_assist = player_data.get("flash_assist", 0) if player_data else 0
    
    # Counter-strafing
    cs_good = player_data.get("counter_strafing_shots_good", 0) if player_data else 0
    cs_all = player_data.get("counter_strafing_shots_all", 0) if player_data else 0
    cs_ratio = player_data.get("counter_strafing_shots_good_ratio", 0) * 100 if player_data else 0
    
    # Multi-kills
    multi1k = player_data.get("multi1k", 0) if player_data else 0
    multi2k = player_data.get("multi2k", 0) if player_data else 0
    multi3k = player_data.get("multi3k", 0) if player_data else 0
    multi4k = player_data.get("multi4k", 0) if player_data else 0
    multi5k = player_data.get("multi5k", 0) if player_data else 0
    
    # Trade stats
    trade_opp = player_data.get("trade_kill_opportunities", 0) if player_data else 0
    trade_kills = player_data.get("trade_kills_succeed", 0) if player_data else 0
    trade_pct = player_data.get("trade_kills_success_percentage", 0) * 100 if player_data else 0
    
    # Traded deaths
    traded_opp = player_data.get("traded_death_opportunities", 0) if player_data else 0
    traded_deaths = player_data.get("traded_deaths_succeed", 0) if player_data else 0
    traded_pct = player_data.get("traded_deaths_success_percentage", 0) * 100 if player_data else 0
    
    # Rounds
    rounds_won = player_data.get("rounds_won", 0) if player_data else 0
    rounds_lost = player_data.get("rounds_lost", 0) if player_data else 0
    rounds_survived = player_data.get("rounds_survived", 0) if player_data else 0
    survive_pct = player_data.get("rounds_survived_percentage", 0) * 100 if player_data else 0
    
    # Score
    score = player_data.get("score", 0) if player_data else 0
    
    # Outcome - determine win/loss from team
    player_team = player_data.get("initial_team_number", 2) if player_data else 2
    outcome = "unknown"
    if team_scores:
        for ts in team_scores:
            if ts.get("team_number") == player_team:
                other_score = 0
                for ts2 in team_scores:
                    if ts2.get("team_number") != player_team:
                        other_score = ts2.get("score", 0)
                        break
                if ts.get("score", 0) > other_score:
                    outcome = "win"
                else:
                    outcome = "loss"
                break
    
    result_emoji = "✅ WIN" if outcome == "win" else "❌ LOSS" if outcome == "loss" else "➖ TIE"
    
    # Build the output with ALL stats
    lines = [
        f"<b>🎮 MATCH DETAILS</b>",
        "═" * 30,
        f"📅 {date}",
        f"🗺️ {map_name}",
        f"⚔️ <b>Score:</b> {score_str} | <b>{result_emoji}</b>",
        f"<a href='{match_link}'>📊 View on Leetify</a>",
        ""
    ]
    
    if player_data:
        lines.append(f"<b>📊 {esc(player_name)}</b>")
        lines.append(f"  💀 <b>KILLS:</b> <code>{kills}</code> | <b>DEATHS:</b> <code>{deaths}</code> | <b>ASSISTS:</b> <code>{assists}</code>")
        lines.append(f"  📐 <b>K/D:</b> <code>{kd:.2f}</code> | <b>ADR:</b> <code>{adr}</code> | <b>ACS:</b> <code>{acs}</code>")
        lines.append(f"  💥 <b>TOTAL DMG:</b> <code>{total_damage}</code> | <b>DPR:</b> <code>{dpr:.1f}</code>")
        lines.append(f"  🎯 <b>ACCURACY:</b> <code>{accuracy:.1f}%</code> | <b>HS:</b> <code>{hs:.1f}%</code> | <b>VS SPOTTED:</b> <code>{accuracy_enemy:.1f}%</code>")
        lines.append(f"  ⚡ <b>REACTION:</b> <code>{reaction:.3f}s</code> | <b>PRE-AIM:</b> <code>{preaim:.1f}</code>")
        lines.append(f"  💨 <b>SPRAY:</b> <code>{spray:.1f}%</code> | <b>COUNTER-STRAFE:</b> <code>{cs_ratio:.1f}%</code> ({cs_good}/{cs_all})")
        lines.append(f"  ⭐ <b>RATING:</b> <code>{rating:.4f}</code> | <b>MVP:</b> <code>{mvps}</code> | <b>SCORE:</b> <code>{score}</code>")
        lines.append(f"  🛡️ <b>CT RATING:</b> <code>{ct_rating:.4f}</code> | 🔴 <b>T RATING:</b> <code>{t_rating:.4f}</code>")
        lines.append("")
        
        # Multi-kills
        if multi1k or multi2k or multi3k or multi4k or multi5k:
            mk = []
            if multi1k: mk.append(f"1K:{multi1k}")
            if multi2k: mk.append(f"2K:{multi2k}")
            if multi3k: mk.append(f"3K:{multi3k}")
            if multi4k: mk.append(f"4K:{multi4k}")
            if multi5k: mk.append(f"5K:{multi5k}")
            lines.append(f"  💪 <b>MULTI-KILLS:</b> <code>{', '.join(mk)}</code>")
        
        # Rounds
        lines.append(f"  🎮 <b>ROUNDS:</b> <code>{rounds_won}W</code> <code>{rounds_lost}L</code> | <b>SURVIVED:</b> <code>{rounds_survived}</code> ({survive_pct:.1f}%)")
        
        # Trade stats
        lines.append(f"  🔄 <b>TRADE:</b> <code>{trade_kills}</code>/<code>{trade_opp}</code> ({trade_pct:.1f}%) | <b>TRADED:</b> <code>{traded_deaths}</code>/<code>{traded_opp}</code> ({traded_pct:.1f}%)")
        
        # Utility
        lines.append(f"  💣 <b>UTILITY:</b> HE:<code>{he_thrown}</code> | Molly:<code>{molotov_thrown}</code> | Smoke:<code>{smoke_thrown}</code> | DMG:<code>{utility_dmg:.1f}</code>")
        
        # Grenades thrown
        lines.append(f"  💥 <b>GRENADES:</b> Flash:<code>{flash_thrown}</code> | Hit:<code>{flash_hit_foe}</code> | Lead Kill:<code>{flash_leading_kill}</code> | Assist:<code>{flash_assist}</code>")
        
        # Weapons stats
        lines.append(f"  🔫 <b>SHOTS:</b> Fired:<code>{shots_fired}</code> | Hit:<code>{shots_hit}</code>")
        
        lines.append("")
    
    # Team leaderboards
    if players:
        # Group by team using initial_team_number
        team2_players = [p for p in players if p.get("initial_team_number", 2) == 2]
        team3_players = [p for p in players if p.get("initial_team_number", 3) == 3]
        
        # Sort by kills
        team2_players.sort(key=lambda x: x.get("total_kills", 0), reverse=True)
        team3_players.sort(key=lambda x: x.get("total_kills", 0), reverse=True)
        
        for team_num, team_players, emoji, score_val in [(2, team2_players, "🛡️ CT", 6), (3, team3_players, "🔴 T", 13)]:
            lines.append(f"<b>{emoji} SIDE ({score_val} rounds)</b>")
            for p in team_players:
                name = esc(p.get("name", "Unknown")[:16])
                k = p.get("total_kills", 0)
                d = p.get("total_deaths", 0)
                a = p.get("total_assists", 0)
                r = p.get("leetify_rating", 0)
                mvp = " ⭐" if p.get("mvps", 0) > 0 else ""
                kd = p.get("kd_ratio", 0)
                dmg = p.get("total_damage", 0)
                adr_val = round(dmg / rounds_count, 1) if rounds_count > 0 else 0
                lines.append(f"  {name}: <code>{k}K</code> <code>{d}D</code> <code>{a}A</code> | <code>{kd:.2f}</code> KD | <code>{dmg}</code> DMG | <code>{adr_val}</code> ADR | <code>{r:.3f}</code>{mvp}")
            lines.append("")
    
    return "\n".join(lines)

def format_welcome() -> str:
    return """<b>🎯 Welcome to Leetify Bot!</b>

I'm your personal CS2 stats tracker. Here's what I can do:

<b>📊 Stats & Analysis</b>
• /stats - View player statistics
• /match - See match details
• /map - Map performance breakdown
• /compare - Compare two players

<b>👥 Player Management</b>
• /add - Add a player to track
• /remove - Remove a tracked player
• /list - See all tracked players
• /edit - Rename a player

<b>🏆 Rankings & Team</b>
• /leaderboard - Global rankings
• /leaderboard weekly - Weekly rankings
• /pow /playerofweek - Player of the Week
• /team /dashboard - Team dashboard
• /myteam - Create team & view stats

<b>🎲 Fun & AI</b>
• /statofday - Random stat of the day
• /analyze - AI profile analysis (shows player list)
• /analyze [name] - Analyze specific player

<b>👥 Team Features</b>
• /myteam - Create team & view stats
• /teststat - Test stat of the day
• /testai - Test AI analysis

<b>⚙️ Other</b>
• /menu - Inline menu
• /settings - Bot settings
• /help - Show this message

<i>Tip: Use /menu for a beautiful inline menu!</i>"""

def format_help() -> str:
    return """<b>📖 Help - All Commands</b>

<b>📊 Stats Commands</b>
• /stats - View player stats
• /stats [name] - Stats for specific player
• /match - Match history
• /map - Map performance
• /compare - Compare two players

<b>👥 Player Management</b>
• /add [id/url] - Add player to track
• /remove [name] - Remove player
• /list - List tracked players
• /edit [old] [new] - Rename player

<b>🏆 Leaderboard</b>
• /leaderboard - All-time rankings
• /leaderboard weekly - This week's rankings

<b>⭐ Team Features</b>
• /team - Team dashboard
• /myteam - Create team & view stats
• /pow - Player of the Week

<b>🎲 Fun & AI</b>
• /statofday - Random stat of the day
• /analyze - AI player profile analysis
• /analyze [name] - Analyze specific player

<b>⚙️ Other</b>
• /menu - Interactive menu
• /ping - Check API connection
• /settings - View settings
• /help - Show this message"""
