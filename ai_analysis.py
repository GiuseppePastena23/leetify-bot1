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

def get_profile_value(profile: dict, *keys, default=0):
    """Safely get nested profile values"""
    for key in keys:
        if profile is None:
            return default
        profile = profile.get(key, {})
        if profile is None or profile == {}:
            return default
    if isinstance(profile, (int, float)):
        return profile
    return default

def analyze_player_profile(profile: dict, player_name: str) -> str:
    if not profile or "error" in profile:
        return "<b>❌ Could not fetch player profile.</b>"
    
    if not config.GEMINI_API_KEY:
        return local_profile_analysis(profile, player_name)
    
    try:
        ranks = profile.get("ranks", {})
        rating = ranks.get("leetify", 0) if isinstance(ranks, dict) else 0
        
        if rating == 0 or rating > 3:
            rating = profile.get("rating", 0)
        
        if rating == 0 or rating > 3:
            rating = ranks.get("global", 0) if isinstance(ranks, dict) else 0
        
        if rating == 0 or rating > 3:
            rating = 1.0
        
        overview = profile.get("overview_stats", profile.get("lifetime", {}))
        
        if isinstance(overview, dict):
            kd = float(overview.get("kdr", overview.get("kd", 0)))
            adr = float(overview.get("adr", 0))
            hs_pct = float(overview.get("headshots", overview.get("hs", 0)))
            winrate = float(overview.get("winRate", overview.get("winrate", 0)))
            matches = int(overview.get("matches", 0))
        else:
            kd = profile.get("kd_ratio", 0)
            adr = profile.get("adr", 0)
            hs_pct = profile.get("headshot_percentage", 0) * 100
            winrate = profile.get("winrate", 0) * 100
            matches = profile.get("total_matches", 0)
        
        if adr == 0:
            adr = profile.get("average_damage_per_round", profile.get("damage_per_round", 0))
        
        kills = profile.get("total_kills", 0)
        deaths = profile.get("total_deaths", 1)
        if kills == 0 or deaths == 1:
            if kd > 0 and matches > 0:
                kills = int(kd * matches * 0.8)
                deaths = int(matches * 0.8)
        
        ct_rating = ranks.get("ct", ranks.get("ct_side", 0)) if isinstance(ranks, dict) else 0
        t_rating = ranks.get("t", ranks.get("t_side", 0)) if isinstance(ranks, dict) else 0
        
        spray = profile.get("spray_accuracy", 0)
        if spray and spray < 1:
            spray = spray * 100
        spray = spray if spray else 0
        
        preaim = profile.get("crosshair_placement", profile.get("preaim", 0))
        reaction = profile.get("reaction_time", 0)
        
        utility_dmg = profile.get("utility_damage_per_round", profile.get("utility_on_death_avg", 0))
        flash_thrown = profile.get("flashbang_thrown", 0)
        smoke_thrown = profile.get("smoke_thrown", 0)
        he_thrown = profile.get("he_thrown", 0)
        
        multi_2k = profile.get("multi_2k", profile.get("two_k", 0))
        multi_3k = profile.get("multi_3k", profile.get("three_k", 0))
        multi_4k = profile.get("multi_4k", profile.get("four_k", 0))
        
        clutch_1v1 = profile.get("clutch_1v1_wins", 0)
        clutch_1v2 = profile.get("clutch_1v2_wins", 0)
        clutch_1v3 = profile.get("clutch_1v3_wins", 0)
        
        first_kills = profile.get("opening_frags", profile.get("first_kills", 0))
        first_deaths = profile.get("opening_deaths", profile.get("first_deaths", 0))
        opening_diff = first_kills - first_deaths
        
        trade_pct = profile.get("trade_kill_percentage", 0)
        if trade_pct and trade_pct < 1:
            trade_pct = trade_pct * 100
        trade_pct = trade_pct if trade_pct else 0
        
        rounds_survived = profile.get("rounds_survived_percentage", 0)
        if rounds_survived and rounds_survived < 1:
            rounds_survived = rounds_survived * 100
        rounds_survived = rounds_survived if rounds_survived else 0
        
        damage_per_round = adr
        
        map_stats = profile.get("maps", {})
        best_maps = []
        worst_maps = []
        
        if map_stats and isinstance(map_stats, dict):
            map_list = []
            for map_name, stats in map_stats.items():
                if isinstance(stats, dict):
                    wr = stats.get("winrate", 0)
                    if wr and wr < 1:
                        wr = wr * 100
                    matches_map = stats.get("matches", 0)
                    if matches_map >= 5:
                        map_list.append((map_name, wr, matches_map))
            
            map_list.sort(key=lambda x: x[1], reverse=True)
            best_maps = map_list[:3]
            worst_maps = map_list[-2:] if len(map_list) >= 2 else []
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config.GEMINI_API_KEY}"
        
        maps_text = ""
        if best_maps:
            maps_text += "\nMAP PERFORMANCE (min 5 matches):"
            for m, wr, mcount in best_maps:
                maps_text += f"\n- {m}: {wr:.1f}% WR ({mcount} matches)"
            if worst_maps:
                maps_text += "\nWorst maps:"
                for m, wr, mcount in worst_maps:
                    maps_text += f"\n- {m}: {wr:.1f}% WR ({mcount} matches)"
        
        prompt = f"""You are a professional CS2 COACH. Analyze this player's overall stats and give detailed role suggestions and improvement tips.

PLAYER PROFILE - {player_name}:
═══════════════════════════════════
OVERALL STATS:
- Rating: {rating:.3f}
- K/D: {kd:.2f} ({kills}K/{deaths}D)
- ADR: {adr:.1f}
- Win Rate: {winrate:.1f}%
- Headshot: {hs_pct:.1f}%
- Matches: {matches}

SIDE RATINGS:
- CT Rating: {ct_rating:.3f}
- T Rating: {t_rating:.3f}
- Side Bias: {"CT" if ct_rating > t_rating + 0.1 else "T" if t_rating > ct_rating + 0.1 else "Balanced"}

SKILL METRICS:
- Spray Accuracy: {spray:.1f}%
- Crosshair Placement: {preaim:.2f} (lower is better)
- Reaction Time: {reaction:.3f}s
- Damage/Round: {damage_per_round:.1f}

OPENING DUELS:
- First Kills: {first_kills}
- First Deaths: {first_deaths}
- Opening Diff: {opening_diff:+d}
- Trade %: {trade_pct:.1f}%

UTILITY:
- Utility Dmg/Round: {utility_dmg:.1f}
- Flashes: {flash_thrown} | Smokes: {smoke_thrown} | HE: {he_thrown}

MULTI-KILLS:
- 2K: {multi_2k} | 3K: {multi_3k} | 4K+: {multi_4k}

CLUTCHES:
- 1v1: {clutch_1v1} | 1v2: {clutch_1v2} | 1v3: {clutch_1v3}
- Survival Rate: {rounds_survived:.1f}%
{maps_text}

Write as a CS2 coach. Include:
1. ONE SENTENCE overall assessment
2. RECOMMENDED ROLE with reasoning (Entry Fragger, AWPer, Support, Lurker, Hybrid, Anchor)
3. DETAILED STRENGTHS (4 things with specific numbers)
4. DETAILED AREAS TO IMPROVE (4 specific things)
5. BEST MAPS (based on actual WR data)
6. WORST MAPS (to avoid or practice)
7. ONE SPECIFIC DRILL or PRACTICE ROUTINE
8. PLAYSTYLE SUMMARY (passive/aggressive, entry/support/lurker)

Be direct, professional, use stats to backup your claims. Maximum 12 sentences total."""

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 500}
        }
        
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=25)
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and result["candidates"]:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return f"<b>🤖 AI Analysis - {player_name}</b>\n─" * 8 + f"\n\n{text}"
    
    except Exception as e:
        print(f"[AI Profile Analysis] Error: {e}")
    
    return local_profile_analysis(profile, player_name)

def safe_float(val, default=0.0):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        return default
    try:
        return float(val)
    except:
        return default

def safe_int(val, default=0):
    if isinstance(val, int):
        return int(val)
    if isinstance(val, dict):
        return default
    try:
        return int(val)
    except:
        return default

def local_profile_analysis(profile: dict, player_name: str) -> str:
    try:
        ranks = profile.get("ranks", {})
        rating = safe_float(ranks.get("leetify", 0)) if isinstance(ranks, dict) else 0.0
        
        if rating <= 0 or rating > 3:
            rating = safe_float(profile.get("rating", 0))
        
        if rating <= 0 or rating > 3:
            rating = safe_float(ranks.get("global", 0)) if isinstance(ranks, dict) else 0.0
        
        if rating <= 0 or rating > 3:
            rating = 1.0
        
        overview = profile.get("overview_stats", profile.get("lifetime", {}))
        
        kd = 0.0
        adr = 0.0
        hs_pct = 0.0
        winrate = 0.0
        matches = 0
        
        if isinstance(overview, dict):
            kd = safe_float(overview.get("kdr", 0))
            if kd == 0:
                kd = safe_float(overview.get("kd", 0))
            adr = safe_float(overview.get("adr", 0))
            hs_pct = safe_float(overview.get("headshots", 0))
            winrate = safe_float(overview.get("winRate", 0))
            if winrate > 1:
                winrate = winrate * 100
            matches = safe_int(overview.get("matches", 0))
        
        if adr == 0:
            adr = safe_float(profile.get("average_damage_per_round", 0))
        
        if matches == 0:
            matches = safe_int(profile.get("total_matches", 0))
        
        kills = safe_int(profile.get("total_kills", 0))
        deaths = safe_int(profile.get("total_deaths", 1))
        if deaths == 0:
            deaths = 1
        
        ct_rating = safe_float(ranks.get("ct", 0)) if isinstance(ranks, dict) else 0.0
        t_rating = safe_float(ranks.get("t", 0)) if isinstance(ranks, dict) else 0.0
        
        preaim = safe_float(profile.get("crosshair_placement", 0))
        
        utility_dmg = safe_float(profile.get("utility_damage_per_round", 0))
        flash_thrown = safe_int(profile.get("flashbang_thrown", 0))
        smoke_thrown = safe_int(profile.get("smoke_thrown", 0))
        he_thrown = safe_int(profile.get("he_thrown", 0))
        
        multi_2k = safe_int(profile.get("multi_2k", 0))
        multi_3k = safe_int(profile.get("multi_3k", 0))
        multi_4k = safe_int(profile.get("multi_4k", 0))
        
        clutch_1v1 = safe_int(profile.get("clutch_1v1_wins", 0))
        clutch_1v2 = safe_int(profile.get("clutch_1v2_wins", 0))
        clutch_1v3 = safe_int(profile.get("clutch_1v3_wins", 0))
        
        first_kills = safe_int(profile.get("opening_frags", 0))
        first_deaths = safe_int(profile.get("opening_deaths", 0))
        opening_diff = first_kills - first_deaths
        
        trade_pct = safe_float(profile.get("trade_kill_percentage", 0)) * 100
        rounds_survived = safe_float(profile.get("rounds_survived_percentage", 0)) * 100
        
        spray = safe_float(profile.get("spray_accuracy", 0))
        if 0 < spray <= 1:
            spray = spray * 100
    except Exception as e:
        return f"<b>❌ Error parsing profile: {e}</b>"
    
    lines = [
        f"<b>📊 Detailed Profile Analysis - {player_name}</b>",
        "═" * 30,
        ""
    ]
    
    lines.append(f"<b>⭐ Rating:</b> <code>{rating:.3f}</code> | <b>K/D:</b> <code>{kd:.2f}</code> | <b>ADR:</b> <code>{adr:.1f}</code>")
    lines.append(f"<b>🏆 Win Rate:</b> <code>{winrate:.1f}%</code> | <b>Matches:</b> <code>{matches}</code> | <b>HS%:</b> <code>{hs_pct:.1f}%</code>")
    lines.append("")
    
    lines.append(f"<b>⚔️ SIDE RATINGS:</b>")
    lines.append(f"CT: <code>{ct_rating:.3f}</code> | T: <code>{t_rating:.3f}</code>")
    if ct_rating > t_rating + 0.1:
        lines.append(f"<i>→ Strong CT side</i>")
    elif t_rating > ct_rating + 0.1:
        lines.append(f"<i>→ Strong T side</i>")
    lines.append("")
    
    lines.append(f"<b>🎯 OPENING DUELS:</b>")
    lines.append(f"First Kills: <code>{first_kills}</code> | First Deaths: <code>{first_deaths}</code>")
    lines.append(f"Opening Diff: <code>{opening_diff:+d}</code> | Trade %: <code>{trade_pct:.1f}%</code>")
    lines.append("")
    
    if ct_rating > t_rating + 0.1:
        role = "🛡️ CT Sided (Support/Anchor)"
        side_note = f"Strong CT side ({ct_rating:.2f} vs {t_rating:.2f} T-side)"
    elif t_rating > ct_rating + 0.1:
        role = "⚔️ T Sided (Entry/Aggressive)"
        side_note = f"Strong T side ({t_rating:.2f} vs {ct_rating:.2f} CT-side)"
    elif kd > 1.2 and adr > 85:
        role = "🎯 Entry Fragger"
        side_note = "High impact, takes duels"
    elif adr > 90:
        role = "💥 High Impact (Star)"
        side_note = "High damage dealer"
    elif utility_dmg > 60 and clutch_1v1 > 5:
        role = "🧨 Support/Utility"
        side_note = "Good utility, clutches"
    elif clutch_1v1 > 10 or clutch_1v2 > 5:
        role = "👻 Lurker"
        side_note = "Clutch ability"
    else:
        role = "⚖️ Hybrid"
        side_note = "Balanced playstyle"
    
    lines.append(f"<b>🏅 Suggested Role:</b> {role}")
    lines.append(f"<i>{side_note}</i>")
    lines.append("")
    
    strengths = []
    if kd >= 1.2:
        strengths.append("Strong aim")
    if adr >= 85:
        strengths.append("High damage")
    if hs_pct >= 35:
        strengths.append("Good headshot %")
    if spray >= 30:
        strengths.append("Spray control")
    if utility_dmg >= 50:
        strengths.append("Utility usage")
    if clutch_1v1 >= 5:
        strengths.append("Clutch ability")
    if t_rating > ct_rating + 0.05:
        strengths.append("T-side entry")
    if ct_rating > t_rating + 0.05:
        strengths.append("CT anchor")
    
    if strengths:
        lines.append("<b>✅ STRENGTHS:</b>")
        for s in strengths[:4]:
            lines.append(f"  • {s}")
        lines.append("")
    
    lines.append("<b>🔥 MULTI-KILLS:</b>")
    lines.append(f"  2K: <code>{multi_2k}</code> | 3K: <code>{multi_3k}</code> | 4K+: <code>{multi_4k}</code>")
    lines.append("")
    
    lines.append("<b>😱 CLUTCHES:</b>")
    lines.append(f"  1v1: <code>{clutch_1v1}</code> | 1v2: <code>{clutch_1v2}</code> | 1v3: <code>{clutch_1v3}</code>")
    lines.append(f"  Survival: <code>{rounds_survived:.1f}%</code>")
    lines.append("")
    
    lines.append("<b>💣 UTILITY:</b>")
    lines.append(f"  Utility Dmg: <code>{utility_dmg:.1f}</code>/round")
    lines.append(f"  Flash: <code>{flash_thrown}</code> | Smoke: <code>{smoke_thrown}</code> | HE: <code>{he_thrown}</code>")
    lines.append("")
    
    weak = []
    if kd < 0.9:
        weak.append("Aim consistency")
    if adr < 75:
        weak.append("Damage output")
    if hs_pct < 25:
        weak.append("Headshot accuracy")
    if spray < 20:
        weak.append("Spray control")
    if utility_dmg < 40:
        weak.append("Utility damage")
    if clutch_1v1 < 3:
        weak.append("Clutch ability")
    if ct_rating < t_rating - 0.1:
        weak.append("CT side")
    if t_rating < ct_rating - 0.1:
        weak.append("T side")
    
    if weak:
        lines.append("<b>❌ IMPROVE:</b>")
        for w in weak[:3]:
            lines.append(f"  • {w}")
    
    return "\n".join(lines)
