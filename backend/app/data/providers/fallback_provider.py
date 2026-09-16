"""
Fallback Provider — always returns local seed/cache. Never fails.
"""
from .base import F1DataProvider, DataProvenance, hash_response

class FallbackProvider(F1DataProvider):
    provider_name = "fallback"
    async def get_calendar(self, season: int):
        from backend.app.data.calendar_2026 import CALENDAR_2026
        return CALENDAR_2026, DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_calendar", response_hash=hash_response(CALENDAR_2026), cache_status="fallback")

    async def get_sessions(self, race_id: str, season: int):
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id) or {}
        return [race] if race else [], DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_sessions", cache_status="fallback")

    async def get_results(self, race_id: str, session: str):
        return {"fallback": True}, DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_results", cache_status="fallback")

    async def get_driver_standings(self, season: int):
        from backend.app.data.season_2026 import DRIVER_STANDINGS_2026
        return DRIVER_STANDINGS_2026, DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_driver_standings", response_hash=hash_response(DRIVER_STANDINGS_2026), cache_status="fallback")

    async def get_constructor_standings(self, season: int):
        from backend.app.data.season_2026 import CONSTRUCTOR_STANDINGS_2026
        return CONSTRUCTOR_STANDINGS_2026, DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_constructor_standings", response_hash=hash_response(CONSTRUCTOR_STANDINGS_2026), cache_status="fallback")

    async def get_qualifying(self, race_id: str):
        return {"fallback": True}, DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_qualifying", cache_status="fallback")

    async def get_weather(self, race_id: str, session: str):
        return {"weather": "dry", "source": "fallback"}, DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_weather", cache_status="fallback")

    async def get_telemetry(self, session_key: str, driver: str):
        return {}, DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_telemetry", cache_status="fallback")

    async def get_pit_stops(self, session_key: str):
        return [], DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_pit_stops", cache_status="fallback")

    async def get_race_control(self, session_key: str):
        return [], DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_race_control", cache_status="fallback")

    async def health(self):
        # This provider IS the fallback — it must never claim to be live, or the
        # whole /system/data-sources panel reads green while serving seed data.
        return {"provider": self.provider_name, "status": "degraded",
                "cache_status": "fallback", "source": "local_seed",
                "note": "always available, but never live — indicates a fallback path"}
