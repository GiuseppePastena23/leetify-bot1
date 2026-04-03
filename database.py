import sqlite3
from datetime import datetime
from typing import Optional
import json

DATABASE_PATH = "leetify_bot.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leetify_id TEXT UNIQUE NOT NULL,
            steam_id TEXT,
            faceit_id TEXT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by_user_id INTEGER,
            added_by_username TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches_reported (
            game_id TEXT PRIMARY KEY,
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats_cache (
            player_id INTEGER,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stats_json TEXT,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_stats (
            player_id INTEGER,
            week_start DATE,
            matches_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            total_kills INTEGER DEFAULT 0,
            total_deaths INTEGER DEFAULT 0,
            mvp_count INTEGER DEFAULT 0,
            rating_sum REAL DEFAULT 0,
            PRIMARY KEY (player_id, week_start),
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    """)
    
    conn.commit()
    conn.close()

def add_player(leetify_id: str, steam_id: str, name: str, faceit_id: str = "", added_by_user_id: int = None, added_by_username: str = "") -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO players (leetify_id, steam_id, faceit_id, name, added_by_user_id, added_by_username) VALUES (?, ?, ?, ?, ?, ?)",
            (leetify_id, steam_id, faceit_id, name, added_by_user_id, added_by_username)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_player(leetify_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE leetify_id = ?", (leetify_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_player_by_name(name: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE name = ? COLLATE NOCASE", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_player_by_id(leetify_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE leetify_id = ?", (leetify_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_player_by_internal_id(internal_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE id = ?", (internal_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_player_added_by(leetify_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT added_by_user_id, added_by_username, created_at FROM players WHERE leetify_id = ?", (leetify_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_players() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_player_name(leetify_id: str, new_name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET name = ? WHERE leetify_id = ?", (new_name, leetify_id))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def player_exists(leetify_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM players WHERE leetify_id = ?", (leetify_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def is_match_reported(game_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM matches_reported WHERE game_id = ?", (game_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def mark_match_reported(game_id: str, score: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO matches_reported (game_id, reported_at, score) VALUES (?, CURRENT_TIMESTAMP, ?)",
        (game_id, score)
    )
    conn.commit()
    conn.close()

def get_all_reported_match_ids() -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT game_id FROM matches_reported")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def cache_player_stats(player_id: int, stats: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO player_stats_cache (player_id, cached_at, stats_json) VALUES (?, CURRENT_TIMESTAMP, ?)",
        (player_id, json.dumps(stats))
    )
    conn.commit()
    conn.close()

def get_cached_stats(player_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT stats_json, cached_at FROM player_stats_cache WHERE player_id = ? ORDER BY cached_at DESC LIMIT 1",
        (player_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def update_weekly_stats(player_id: int, week_start: str, is_win: bool, kills: int, deaths: int, rating: float, mvp: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_win:
        cursor.execute("""
            INSERT INTO weekly_stats (player_id, week_start, matches_played, wins, losses, total_kills, total_deaths, mvp_count, rating_sum)
            VALUES (?, ?, 1, 1, 0, ?, ?, ?, ?)
            ON CONFLICT(player_id, week_start) DO UPDATE SET
                matches_played = matches_played + 1,
                wins = wins + 1,
                total_kills = total_kills + ?,
                total_deaths = total_deaths + ?,
                mvp_count = mvp_count + ?,
                rating_sum = rating_sum + ?
        """, (player_id, week_start, kills, deaths, mvp, rating, kills, deaths, mvp, rating))
    else:
        cursor.execute("""
            INSERT INTO weekly_stats (player_id, week_start, matches_played, wins, losses, total_kills, total_deaths, mvp_count, rating_sum)
            VALUES (?, ?, 1, 0, 1, ?, ?, ?, ?)
            ON CONFLICT(player_id, week_start) DO UPDATE SET
                matches_played = matches_played + 1,
                losses = losses + 1,
                total_kills = total_kills + ?,
                total_deaths = total_deaths + ?,
                mvp_count = mvp_count + ?,
                rating_sum = rating_sum + ?
        """, (player_id, week_start, kills, deaths, mvp, rating, kills, deaths, mvp, rating))
    
    conn.commit()
    conn.close()

def get_weekly_stats(week_start: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.name, ws.* 
        FROM weekly_stats ws
        JOIN players p ON ws.player_id = p.id
        WHERE ws.week_start = ?
        ORDER BY ws.rating_sum / ws.matches_played DESC
    """, (week_start,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_week_start(date: datetime = None) -> str:
    if date is None:
        date = datetime.now()
    return date.strftime("%Y-%m-%d")
