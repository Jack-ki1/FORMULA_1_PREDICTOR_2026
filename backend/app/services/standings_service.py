"""
StandingsService — optimized for 2026 season with immediate local fallback.
"""
import logging
from typing import Dict
from backend.app.data.season_2026 import get_driver_standings, get_constructor_standings
from backend.app.cache.redis import get_cache
logger = logging.getLogger(__name__)

DRIVER_STANDINGS_KEY = "standings:drivers:2026"
CONSTRUCTOR_STANDINGS_KEY = "standings:constructors:2026"

class StandingsService:
    """Standings with cache-first approach. For 2026, uses local data immediately."""

    TTL = 300

    @staticmethod
    def _from_cache(key: str):
        try:
            cached = get_cache().get(key)
        except Exception:
            return None
        if not cached:
            return None
        import json
        try:
            value = json.loads(cached) if isinstance(cached, str) else cached
        except Exception:
            return None
        # Never serve a payload with no usable entries.
        if isinstance(value, dict) and not (value.get("standings") or value.get("data")):
            return None
        return value

    @staticmethod
    def _to_cache(key: str, value):
        try:
            get_cache().set(key, value, ttl=StandingsService.TTL)
        except Exception:
            pass

    def get_driver_standings(self) -> Dict:
        # Check cache first
        hit = self._from_cache(DRIVER_STANDINGS_KEY)
        if hit:
            return {**hit, "cache": "hit"}
        
        # For 2026, use local data immediately - no network calls
        standings = get_driver_standings()
        result = {"standings": standings, "data": standings, "source": "local"}
        
        # Cache the result
        self._to_cache(DRIVER_STANDINGS_KEY, result)
        return result

    def get_constructor_standings(self) -> Dict:
        # Check cache first
        hit = self._from_cache(CONSTRUCTOR_STANDINGS_KEY)
        if hit:
            return {**hit, "cache": "hit"}
        
        # For 2026, use local data immediately - no network calls
        standings = get_constructor_standings()
        result = {"standings": standings, "data": standings, "source": "local"}
        
        # Cache the result
        self._to_cache(CONSTRUCTOR_STANDINGS_KEY, result)
        return result


standings_service = StandingsService()
