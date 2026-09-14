"""
RaceService — calendar/races abstraction with explicit cache keys.
"""
import logging
from typing import Dict, List
from backend.app.data.calendar_2026 import CALENDAR_2026, get_race_by_id
from backend.app.cache.redis import get_cache
logger = logging.getLogger(__name__)

CACHE_KEY_RACES = "races:2026"

class RaceService:
    def list_races(self) -> List[Dict]:
        cache = get_cache()
        cached = cache.get(CACHE_KEY_RACES)
        if cached:
            import json
            try:
                return json.loads(cached) if isinstance(cached, str) else cached
            except Exception:
                pass
        # serve full calendar (including status) — frontend filters cancelled
        data = CALENDAR_2026
        try:
            cache.set(CACHE_KEY_RACES, data, ttl=3600)
        except Exception:
            pass
        return data

    def get_race(self, race_id: str) -> Dict | None:
        return get_race_by_id(race_id)

    def get_race_result(self, race_id: str) -> Dict:
        race = get_race_by_id(race_id)
        if not race:
            raise LookupError("Race not found")
        if race.get("status") != "completed":
            raise ValueError("Race not yet completed")
        return race

race_service = RaceService()
