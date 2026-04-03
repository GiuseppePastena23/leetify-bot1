import requests
import logging
import config

logger = logging.getLogger(__name__)

class DiscordClient:
    def __init__(self):
        self.webhook_url = config.DISCORD_WEBHOOK_URL
        self.enabled = config.DISCORD_ENABLED
    
    def _send_webhook(self, payload: dict) -> bool:
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            return response.status_code == 204 or response.status_code == 200
        except Exception as e:
            logger.error(f"Discord webhook failed: {e}")
            return False
    
    def send_match_alert(self, player_name: str, match_result: str, rating: float, rating_change: float, map_name: str, score: str) -> bool:
        emoji = "🟢" if rating_change > 0 else "🔴" if rating_change < 0 else "🟡"
        
        embed = {
            "title": f"🎮 Match Result - {player_name}",
            "color": 65280 if rating_change > 0 else 16711680 if rating_change < 0 else 16776960,
            "fields": [
                {"name": "Result", "value": match_result, "inline": True},
                {"name": "Map", "value": map_name, "inline": True},
                {"name": "Score", "value": score, "inline": True},
                {"name": "Rating", "value": f"{emoji} {rating:.2f} ({rating_change:+.2f})", "inline": False}
            ],
            "footer": {"text": "Leetify Bot"}
        }
        
        payload = {"embeds": [embed]}
        return self._send_webhook(payload)
    
    def send_leaderboard(self, title: str, players: list) -> bool:
        fields = []
        for p in players[:10]:
            fields.append({
                "name": f"{p.get('rank', '?')}. {p.get('name', 'Unknown')}",
                "value": f"Rating: {p.get('rating', 0):.2f} | Win Rate: {p.get('winrate', 0):.1f}%",
                "inline": False
            })
        
        embed = {
            "title": f"🏆 {title}",
            "color": 16772160,
            "fields": fields,
            "footer": {"text": "Leetify Bot"}
        }
        
        payload = {"embeds": [embed]}
        return self._send_webhook(payload)
    
    def send_player_added(self, player_name: str, added_by: str) -> bool:
        embed = {
            "title": "➕ Player Added",
            "color": 65535,
            "fields": [
                {"name": "Player", "value": player_name, "inline": True},
                {"name": "Added by", "value": f"@{added_by}", "inline": True}
            ],
            "footer": {"text": "Leetify Bot"}
        }
        
        payload = {"embeds": [embed]}
        return self._send_webhook(payload)
    
    def send_player_of_week(self, player_name: str, stats: dict) -> bool:
        embed = {
            "title": "⭐ Player of the Week",
            "color": 16766720,
            "fields": [
                {"name": "Player", "value": player_name, "inline": True},
                {"name": "Matches", "value": str(stats.get('matches', 0)), "inline": True},
                {"name": "Win Rate", "value": f"{stats.get('winrate', 0):.1f}%", "inline": True},
                {"name": "Avg Rating", "value": f"{stats.get('avg_rating', 0):.2f}", "inline": True},
                {"name": "K/D", "value": f"{stats.get('kd', 0):.2f}", "inline": True}
            ],
            "footer": {"text": "Leetify Bot"}
        }
        
        payload = {"embeds": [embed]}
        return self._send_webhook(payload)
    
    def send_weekly_digest(self, week_stats: list) -> bool:
        fields = []
        for p in week_stats[:5]:
            fields.append({
                "name": f"{p.get('rank', '?')}. {p.get('name', 'Unknown')}",
                "value": f"Matches: {p.get('matches', 0)} | WR: {p.get('winrate', 0):.1f}% | Avg Rating: {p.get('avg_rating', 0):.2f}",
                "inline": False
            })
        
        embed = {
            "title": "📊 Weekly Digest",
            "color": 65280,
            "fields": fields,
            "footer": {"text": "Leetify Bot"}
        }
        
        payload = {"embeds": [embed]}
        return self._send_webhook(payload)

discord_client = DiscordClient()
