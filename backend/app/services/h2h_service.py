import logging
from backend.app.config.team_driver_lineup_2026 import get_all_drivers, get_driver_by_code
from backend.app.engine.elo_calculator import elo_calculator
from backend.app.cache.redis import get_cache
logger = logging.getLogger(__name__)

class H2HService:
    def list_drivers(self):
        return get_all_drivers()

    def compare(self, driver_a: str, driver_b: str) -> dict:
        a = (driver_a or "").upper()
        b = (driver_b or "").upper()
        if not a or not b:
            raise ValueError("driver_a and driver_b are both required")
        info_a = get_driver_by_code(a)
        info_b = get_driver_by_code(b)
        if not info_a or not info_b:
            raise LookupError("Unknown driver code")
        # cache H2H
        key = f"h2h:{a}:{b}"
        cache = get_cache()
        cached = cache.get(key)
        if cached:
            import json
            try:
                return json.loads(cached) if isinstance(cached, str) else cached
            except Exception: pass
        prob = elo_calculator.get_h2h_probability(a,b)
        result = {"driver_a": info_a, "driver_b": info_b, "win_probability": prob, "reverse_probability": 1-prob}
        try: cache.set(key, result, ttl=3600)
        except Exception: pass
        return result

h2h_service = H2HService()
