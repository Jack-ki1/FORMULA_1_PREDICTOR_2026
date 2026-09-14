"""
Jolpica Provider — official-style results/standings, qualifying.
Wraps backend.app.data.jolpica_client.JolpicaClient.
"""
import time
from typing import Any, Dict, List
from .base import F1DataProvider, DataProvenance, hash_response

class JolpicaProvider(F1DataProvider):
    provider_name = "jolpica"
    def __init__(self):
        from backend.app.data.jolpica_client import JolpicaClient
        self.client = JolpicaClient()

    async def get_calendar(self, season: int):
        from backend.app.data.calendar_2026 import CALENDAR_2026
        prov = DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_calendar", response_hash=hash_response(CALENDAR_2026), cache_status="fallback")
        return CALENDAR_2026, prov

    async def get_sessions(self, race_id: str, season: int):
        # Jolpica has no sessions; return calendar entry
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id) or {}
        prov = DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_sessions", response_hash=hash_response(race), cache_status="fallback")
        return [race] if race else [], prov

    async def get_results(self, race_id: str, session: str):
        t0=time.time()
        try:
            data = self.client.get_race_result(race_id)  # sync call
            prov = DataProvenance(source="jolpica", provider=self.provider_name, endpoint=f"get_results:{race_id}:{session}", response_hash=hash_response(data), cache_status="miss", latency_ms=(time.time()-t0)*1000)
            return data if isinstance(data, dict) else {"data": data}, prov
        except Exception as e:
            prov = DataProvenance(source="jolpica_fallback", provider=self.provider_name, endpoint=f"get_results:{race_id}", response_hash="", cache_status="fallback", latency_ms=(time.time()-t0)*1000)
            return {"error": str(e), "fallback": True}, prov

    async def get_driver_standings(self, season: int):
        t0=time.time()
        try:
            data = self.client.get_driver_standings(season)
            prov = DataProvenance(source="jolpica", provider=self.provider_name, endpoint="get_driver_standings", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data if isinstance(data, list) else data.get("data", []), prov
        except Exception as e:
            from backend.app.data.season_2026 import DRIVER_STANDINGS_2026
            prov = DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_driver_standings", response_hash=hash_response(DRIVER_STANDINGS_2026), cache_status="fallback")
            return DRIVER_STANDINGS_2026, prov

    async def get_constructor_standings(self, season: int):
        t0=time.time()
        try:
            data = self.client.get_constructor_standings(season)
            prov = DataProvenance(source="jolpica", provider=self.provider_name, endpoint="get_constructor_standings", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data if isinstance(data, list) else data.get("data", []), prov
        except Exception:
            from backend.app.data.season_2026 import CONSTRUCTOR_STANDINGS_2026
            prov = DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_constructor_standings", response_hash=hash_response(CONSTRUCTOR_STANDINGS_2026), cache_status="fallback")
            return CONSTRUCTOR_STANDINGS_2026, prov

    async def get_qualifying(self, race_id: str):
        t0=time.time()
        try:
            data = self.client.get_qualifying_result(race_id)
            prov = DataProvenance(source="jolpica", provider=self.provider_name, endpoint=f"get_qualifying:{race_id}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data, prov
        except Exception as e:
            prov = DataProvenance(source="jolpica_fallback", provider=self.provider_name, endpoint=f"get_qualifying:{race_id}", cache_status="fallback")
            return {"fallback": True, "error": str(e)}, prov

    async def get_weather(self, race_id: str, session: str):
        prov = DataProvenance(source="local_seed", provider=self.provider_name, endpoint="get_weather", response_hash="", cache_status="fallback")
        return {"source": "jolpica_no_weather"}, prov

    async def get_telemetry(self, session_key: str, driver: str):
        prov = DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_telemetry", cache_status="fallback")
        return {}, prov

    async def get_pit_stops(self, session_key: str):
        prov = DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_pit_stops", cache_status="fallback")
        return [], prov

    async def get_race_control(self, session_key: str):
        prov = DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_race_control", cache_status="fallback")
        return [], prov

    async def health(self):
        try:
            # cheap check: driver standings fetch with timeout already handled by client retries
            await self.get_driver_standings(2026)
            return {"provider": self.provider_name, "status": "healthy"}
        except Exception as e:
            return {"provider": self.provider_name, "status": "degraded", "error": str(e)}
