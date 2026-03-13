import requests
from typing import Optional
import time
import config

class LeetifyClient:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.base_url = config.BASE_URL
        self.headers = config.HEADERS
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, headers=self.headers, **kwargs)
                
                if response.status_code == 429:
                    wait_time = self.retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                
                if response.status_code == 401:
                    return {"error": "invalid_api_key"}
                
                if response.status_code == 404:
                    return {"error": "not_found", "message": "Player not found or API endpoint changed"}
                
                response.raise_for_status()
                data = response.json()
                
                if "message" in data and "not found" in data["message"].lower():
                    return {"error": "not_found"}
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    return {"error": str(e)}
                time.sleep(self.retry_delay)
        
        return {"error": "max_retries_exceeded"}
    
    def get(self, endpoint: str, **kwargs) -> Optional[dict]:
        return self._request("GET", endpoint, **kwargs)
    
    def validate_api_key(self) -> bool:
        result = self.get("/api-key/validate")
        return result is not None and "error" not in result
    
    def get_player_profile(self, leetify_id: str) -> Optional[dict]:
        result = self.get(f"/v3/profile?id={leetify_id}")
        if result:
            print(f"[DEBUG] Leetify profile response: {result}")
        return result
    
    def get_player_matches(self, leetify_id: str, limit: int = 20) -> Optional[dict]:
        return self.get(f"/v3/profile/matches?id={leetify_id}&limit={limit}")
    
    def get_match_details(self, game_id: str) -> Optional[dict]:
        result = self.get(f"/v2/matches/{game_id}")
        if result and "error" not in result:
            print(f"[DEBUG] === MATCH DETAILS ===")
            print(f"[DEBUG] Keys: {list(result.keys())}")
            print(f"[DEBUG] team_scores: {result.get('team_scores')}")
            stats = result.get("stats", [])
            print(f"[DEBUG] stats count: {len(stats) if stats else 0}")
            if stats:
                print(f"[DEBUG] First stat keys: {list(stats[0].keys()) if stats else 'None'}")
                print(f"[DEBUG] First stat: {stats[0]}")
        return result
    
    def get_match_details_by_source(self, data_source: str, data_source_id: str) -> Optional[dict]:
        return self.get(f"/v2/matches/{data_source}/{data_source_id}")
    
    def search_player(self, query: str) -> Optional[dict]:
        result = self.get(f"/v3/profile?id={query}")
        if result and "error" not in result:
            return result
        return None
    
    def extract_leetify_id(self, input_str: str) -> Optional[str]:
        if not input_str:
            return None
        
        input_str = input_str.strip()
        
        if input_str.startswith("7656119"):
            return input_str
        
        if "leetify.com/profile/" in input_str:
            parts = input_str.split("leetify.com/profile/")
            if len(parts) > 1:
                return parts[1].strip("/")
        
        if "leetify.com/app/profile/" in input_str:
            parts = input_str.split("leetify.com/app/profile/")
            if len(parts) > 1:
                return parts[1].strip("/")
        
        return input_str

client = LeetifyClient()


class CSStatsClient:
    def __init__(self):
        self.base_url = "https://csstats.gg"
    
    def get_player(self, steam_id: str) -> Optional[dict]:
        try:
            # Try using the web API with proper headers
            url = f"{self.base_url}/api/player/{steam_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://csstats.gg/'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 403:
                return {"error": "blocked", "message": "CSStats is blocking automated requests (Cloudflare protection)"}
            return None
        except Exception as e:
            print(f"[ERROR] CSStats fetch failed: {e}")
            return {"error": str(e)}
    
    def get_player_by_name(self, name: str) -> Optional[dict]:
        try:
            url = f"{self.base_url}/api/search"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://csstats.gg/'
            }
            response = requests.get(url, params={"q": name}, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
            return None
        except Exception as e:
            print(f"[ERROR] CSStats search failed: {e}")
            return None

csstats_client = CSStatsClient()


class CSGrindClient:
    def __init__(self):
        self.base_url = "https://csgrind.com"
    
    def get_player(self, player_id: str) -> Optional[dict]:
        try:
            url = f"{self.base_url}/api/player/{player_id}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] CSGrind fetch failed: {e}")
            return None
    
    def get_player_by_name(self, name: str) -> Optional[dict]:
        try:
            url = f"{self.base_url}/api/search"
            response = requests.get(url, params={"q": name}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
            return None
        except Exception as e:
            print(f"[ERROR] CSGrind search failed: {e}")
            return None

csgrind_client = CSGrindClient()


class FACEITClient:
    def __init__(self):
        self.base_url = "https://open.faceit.com/data/v1"
        self.headers = {
            "Authorization": f"Bearer {config.FACEIT_API_KEY}",
            "Accept": "application/json"
        } if config.FACEIT_API_KEY else {}
    
    def _request(self, endpoint: str) -> Optional[dict]:
        if not config.FACEIT_API_KEY:
            return {"error": "no_api_key"}
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 401:
                return {"error": "invalid_api_key"}
            if response.status_code == 404:
                return None
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] FACEIT fetch failed: {e}")
            return None
    
    def get_player_by_nickname(self, nickname: str) -> Optional[dict]:
        result = self._request(f"/players?nickname={nickname}")
        if result and "error" not in result and result.get("items"):
            return result["items"][0]
        return None
    
    def get_player_by_steam(self, steam_id: str) -> Optional[dict]:
        result = self._request(f"/players?game=cs2&steam_id_64={steam_id}")
        if result and "error" not in result and result.get("items"):
            return result["items"][0]
        return None
    
    def get_player_stats(self, player_id: str) -> Optional[dict]:
        return self._request(f"/players/{player_id}/stats/cs2")
    
    def get_player_matches(self, player_id: str, limit: int = 10) -> Optional[dict]:
        return self._request(f"/players/{player_id}/history?game=cs2&limit={limit}")

faceit_client = FACEITClient()
