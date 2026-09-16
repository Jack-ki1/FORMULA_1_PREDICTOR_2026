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
        # Serve directly from memory - calendar is static and small
        # Skip cache layer entirely for this to avoid Redis timeout delays
        return CALENDAR_2026

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
