import requests
import time
import hashlib
import config

cache = {}

def get_cache_key(player_data, map_name):
    key_str = f"{player_data.get('total_kills', 0)}_{player_data.get('total_deaths', 0)}_{map_name}"
    return hashlib.md5(key_str.encode()).hexdigest()

def analyze_match(player_data: dict, map_name: str) -> str:
    cache_key = get_cache_key(player_data, map_name)
    
    if cache_key in cache:
        return cache[cache_key]
    
    if not config.GEMINI_API_KEY:
        return local_analysis(player_data, map_name)
    
    kills = player_data.get("total_kills", 0)
    deaths = player_data.get("total_deaths", 0)
    assists = player_data.get("total_assists", 0)
    kd = player_data.get("kd_ratio", 0)
    total_damage = player_data.get("total_damage", 0)
    rounds_count = player_data.get("rounds_count", 19)
    adr = round(total_damage / rounds_count, 1) if rounds_count > 0 else 0
    
    rating = player_data.get("leetify_rating", 0)
    ct_rating = player_data.get("ct_leetify_rating", 0)
    t_rating = player_data.get("t_leetify_rating", 0)
    
    hs_pct = round((player_data.get("accuracy_head", 0)) * 100, 1)
    spray = round((player_data.get("spray_accuracy", 0)) * 100, 1)
    preaim = round(player_data.get("preaim", 0), 1)
    reaction = round(player_data.get("reaction_time", 0), 3)
    
    cs_ratio = round((player_data.get("counter_strafing_shots_good_ratio", 0)) * 100, 1)
    
    utility_dmg = round(player_data.get("utility_on_death_avg", 0), 1)
    he_thrown = player_data.get("he_thrown", 0)
    smoke_thrown = player_data.get("smoke_thrown", 0)
    flash_thrown = player_data.get("flashbang_thrown", 0)
    
    trade_pct = round((player_data.get("trade_kills_success_percentage", 0)) * 100, 1)
    
    rounds_won = player_data.get("rounds_won", 0)
    rounds_lost = player_data.get("rounds_lost", 0)
    survive_pct = round((player_data.get("rounds_survived_percentage", 0)) * 100, 1)
    
    multi1k = player_data.get("multi1k", 0)
    multi2k = player_data.get("multi2k", 0)
    multi3k = player_data.get("multi3k", 0)
    mvps = player_data.get("mvps", 0)
    
    result = None
    
    for attempt in range(3):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config.GEMINI_API_KEY}"
            
            prompt = f"""You are a professional CS2 COACH. Analyze this match on {map_name} and give specific, actionable advice.

MATCH DATA:
- Map: {map_name}
- Result: {rounds_won}W-{rounds_lost}L
- K/D: {kd:.2f} ({kills}K/{deaths}D/{assists}A)
- ADR: {adr}
- Rating: {rating:.3f}
- CT Rating: {ct_rating:.3f} | T Rating: {t_rating:.3f}
- Headshot: {hs_pct}%
- Spray: {spray}%
- Pre-aim: {preaim}
- Reaction: {reaction}s
- Counter-strafe: {cs_ratio}%
- Utility Dmg: {utility_dmg}
- Trade: {trade_pct}%
- Survival: {survive_pct}%
- Multi-kills: 1K:{multi1k} 2K:{multi2k} 3K:{multi3k}
- MVPs: {mvps}
- Nades: HE:{he_thrown} Smoke:{smoke_thrown} Flash:{flash_thrown}

Write as a CS2 coach. Include:
1. ONE SENTENCE match overview
2. STRENGTHS (2 things done well)
3. AREAS TO IMPROVE (2-3 specific things)  
4. ONE SPECIFIC DRILL/PRACTICE TIP
5. MAP ADVICE for {map_name}

Be direct, serious, use few emojis. Maximum 8 sentences total."""

            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 400}
            }
            
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and result["candidates"]:
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    analysis = f"<b>🤖 GEMINI AI</b>\n─" * 8 + "\n\n{text}"
                    cache[cache_key] = analysis
                    return analysis
            
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
                
            break
            
        except Exception as e:
            print(f"[AI] Error: {e}")
            break
    
    return local_analysis(player_data, map_name)

def local_analysis(player_data, map_name):
    kills = player_data.get("total_kills", 0)
    deaths = player_data.get("total_deaths", 0)
    assists = player_data.get("total_assists", 0)
    kd = player_data.get("kd_ratio", 0)
    total_damage = player_data.get("total_damage", 0)
    rounds_count = player_data.get("rounds_count", 19)
    adr = round(total_damage / rounds_count, 1) if rounds_count > 0 else 0
    
    rating = player_data.get("leetify_rating", 0)
    ct_rating = player_data.get("ct_leetify_rating", 0)
    t_rating = player_data.get("t_leetify_rating", 0)
    
    hs_pct = round((player_data.get("accuracy_head", 0)) * 100, 1)
    spray = round((player_data.get("spray_accuracy", 0)) * 100, 1)
    preaim = round(player_data.get("preaim", 0), 1)
    reaction = round(player_data.get("reaction_time", 0), 3)
    
    cs_ratio = round((player_data.get("counter_strafing_shots_good_ratio", 0)) * 100, 1)
    utility_dmg = round(player_data.get("utility_on_death_avg", 0), 1)
    trade_pct = round((player_data.get("trade_kills_success_percentage", 0)) * 100, 1)
    
    rounds_won = player_data.get("rounds_won", 0)
    rounds_lost = player_data.get("rounds_lost", 0)
    survive_pct = round((player_data.get("rounds_survived_percentage", 0)) * 100, 1)
    
    multi1k = player_data.get("multi1k", 0)
    multi2k = player_data.get("multi2k", 0)
    multi3k = player_data.get("multi3k", 0)
    mvps = player_data.get("mvps", 0)
    
    # Coach analysis
    lines = [
        f"<b>🎯 COACH ANALYSIS - {map_name}</b>",
        "═" * 25,
        ""
    ]
    
    # Match overview
    if rounds_won > rounds_lost:
        lines.append(f"✅ <b>WIN</b> - {rounds_won}-{rounds_lost}")
    elif rounds_won < rounds_lost:
        lines.append(f"❌ <b>LOSS</b> - {rounds_won}-{rounds_lost}")
    else:
        lines.append(f"➖ <b>DRAW</b> - {rounds_won}-{rounds_lost}")
    
    lines.append(f"Rating: <code>{rating:.3f}</code> | K/D: <code>{kd:.2f}</code> | ADR: <code>{adr}</code>")
    lines.append("")
    
    # Strengths
    strengths = []
    if kd >= 1.2:
        strengths.append("Good aim")
    if adr >= 90:
        strengths.append("High damage")
    if ct_rating > t_rating + 0.05:
        strengths.append("Strong CT side")
    if t_rating > ct_rating + 0.05:
        strengths.append("Strong T side")
    if trade_pct >= 35:
        strengths.append("Good trading")
    if spray >= 30:
        strengths.append("Spray control")
    if survive_pct >= 35:
        strengths.append("Survival")
    if multi3k >= 1:
        strengths.append("Multi-kills")
    
    if strengths:
        lines.append("<b>✅ STRENGTHS:</b>")
        for s in strengths[:3]:
            lines.append(f"  • {s}")
        lines.append("")
    
    # Weaknesses
    weak = []
    if kd < 0.8:
        weak.append("Aim duels")
    if adr < 70:
        weak.append("Damage output")
    if hs_pct < 20:
        weak.append("Headshot accuracy")
    if spray < 20:
        weak.append("Spray control")
    if reaction > 0.75:
        weak.append("Reaction time")
    if cs_ratio < 50:
        weak.append("Movement")
    if utility_dmg < 80:
        weak.append("Utility usage")
    if trade_pct < 25:
        weak.append("Trading")
    
    if weak:
        lines.append("<b>❌ IMPROVE:</b>")
        for w in weak[:3]:
            lines.append(f"  • {w}")
        lines.append("")
    
    # Tips
    tips = []
    
    if ct_rating > t_rating + 0.1:
        tips.append("Play more CT sides")
    elif t_rating > ct_rating + 0.1:
        tips.append("Focus on T side")
    
    if map_name.lower() in ["de_mirage", "mirage"]:
        tips.append("Practice Mirage smokes/flashes")
    elif map_name.lower() in ["de_inferno", "inferno"]:
        tips.append("Work on inferno molotovs")
    elif map_name.lower() in ["de_dust2", "dust2"]:
        tips.append("Long range duels")
    elif map_name.lower() in ["de_ancient", "ancient"]:
        tips.append("A short executes")
    elif map_name.lower() in ["de_nuke", "nuke"]:
        tips.append("Nuke rush plays")
    elif map_name.lower() in ["de_vertigo", "vertigo"]:
        tips.append("Vertigo mid control")
    elif map_name.lower() in ["de_anubis", "anubis"]:
        tips.append("Anubis utility")
    elif map_name.lower() in ["de_overpass", "overpass"]:
        tips.append("Overpass smokes")
    
    if tips:
        lines.append("<b>💡 TIPS:</b>")
        for t in tips[:2]:
            lines.append(f"  • {t}")
    
    lines.append("")
    lines.append(f"<i>Stats: {kills}K/{deaths}D | {adr} ADR | {hs_pct}% HS | {spray}% Spray</i>")
    
    return "\n".join(lines)
