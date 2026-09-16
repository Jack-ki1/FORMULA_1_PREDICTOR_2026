"""
StandingsService — live-source + local-fallback pattern preserved.
"""
import logging
from typing import Dict
from backend.app.data.season_2026 import get_driver_standings, get_constructor_standings
from backend.app.data.jolpica_client import JolpicaClient
from backend.app.config.settings import settings
from backend.app.cache.redis import get_cache
logger = logging.getLogger(__name__)

DRIVER_STANDINGS_KEY = "standings:drivers:2026"
CONSTRUCTOR_STANDINGS_KEY = "standings:constructors:2026"

class StandingsService:
    """Standings with a read-through cache.

    NOTE on ordering: this used to hit the network FIRST and only consult the
    cache on the failure path, so a successful live result was re-fetched from
    upstream on every single request (~0.45s each, plus a ~4s JolpicaClient
    construction). The cache was written but never read on the happy path.
    Now the cache is checked first, so a repeat visit is instant, and the
    client is only constructed when a refresh is actually needed.
    """

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
        hit = self._from_cache(DRIVER_STANDINGS_KEY)
        if hit:
            return {**hit, "cache": "hit"}
        try:
            result = JolpicaClient().get_driver_standings(settings.SEASON_YEAR)
            if result.get("source") in ("live", "cached") and (result.get("standings") or result.get("data")):
                self._to_cache(DRIVER_STANDINGS_KEY, result)
                return result
        except Exception as e:
            logger.warning("Live driver standings failed, fallback: %s", e)
        standings = get_driver_standings()
        return {"standings": standings, "data": standings, "source": "local"}

    def get_constructor_standings(self) -> Dict:
        hit = self._from_cache(CONSTRUCTOR_STANDINGS_KEY)
        if hit:
            return {**hit, "cache": "hit"}
        try:
            result = JolpicaClient().get_constructor_standings()
            if result.get("source") in ("live", "cached") and (result.get("standings") or result.get("data")):
                self._to_cache(CONSTRUCTOR_STANDINGS_KEY, result)
                return result
        except Exception as e:
            logger.warning("Live constructor standings failed, fallback: %s", e)
        standings = get_constructor_standings()
        return {"standings": standings, "data": standings, "source": "local"}


standings_service = StandingsService()
