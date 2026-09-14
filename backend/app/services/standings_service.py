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
    def get_driver_standings(self) -> Dict:
        cache = get_cache()
        try:
            client = JolpicaClient()
            result = client.get_driver_standings(settings.SEASON_YEAR)
            if result.get("source") == "live":
                try: cache.set(DRIVER_STANDINGS_KEY, result, ttl=300)
                except Exception: pass
                return result
        except Exception as e:
            logger.warning("Live driver standings failed, fallback: %s", e)
        # fallback
        cached = cache.get(DRIVER_STANDINGS_KEY)
        if cached:
            import json
            try:
                return json.loads(cached) if isinstance(cached, str) else cached
            except Exception: pass
        standings = get_driver_standings()
        return {"data": standings, "source": "local"}

    def get_constructor_standings(self) -> Dict:
        cache = get_cache()
        try:
            client = JolpicaClient()
            result = client.get_constructor_standings()
            if result.get("source") == "live":
                try: cache.set(CONSTRUCTOR_STANDINGS_KEY, result, ttl=300)
                except Exception: pass
                return result
        except Exception as e:
            logger.warning("Live constructor standings failed, fallback: %s", e)
        cached = cache.get(CONSTRUCTOR_STANDINGS_KEY)
        if cached:
            import json
            try:
                return json.loads(cached) if isinstance(cached, str) else cached
            except Exception: pass
        standings = get_constructor_standings()
        return {"data": standings, "source": "local"}

standings_service = StandingsService()
