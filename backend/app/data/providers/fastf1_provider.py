"""
FastF1 Provider — historical telemetry, session results, lap data.
"""
import time
from typing import Any, Dict, List
from .base import F1DataProvider, DataProvenance, hash_response

class FastF1Provider(F1DataProvider):
    provider_name = "fastf1"
    def __init__(self):
        try:
            from backend.app.data.fastf1_integration import FastF1Integration
            self.client = FastF1Integration()
        except Exception:
            self.client = None

    async def get_calendar(self, season: int):
        return [], DataProvenance(source="fastf1_no_calendar", provider=self.provider_name, endpoint="get_calendar", cache_status="fallback")

    async def get_sessions(self, race_id: str, season: int):
        return [], DataProvenance(source="fastf1_no_sessions", provider=self.provider_name, endpoint="get_sessions", cache_status="fallback")

    async def get_results(self, race_id: str, session: str):
        t0=time.time()
        if not self.client:
            return {}, DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_results", cache_status="fallback")
        try:
            data = self.client.get_session_results(race_id, session)  # type: ignore
            prov = DataProvenance(source="fastf1", provider=self.provider_name, endpoint=f"get_results:{race_id}:{session}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data, prov
        except Exception:
            return {}, DataProvenance(source="fastf1_error", provider=self.provider_name, endpoint="get_results", cache_status="fallback")

    async def get_driver_standings(self, season: int):
        return [], DataProvenance(source="fastf1_no_standings", provider=self.provider_name, endpoint="get_driver_standings", cache_status="fallback")

    async def get_constructor_standings(self, season: int):
        return [], DataProvenance(source="fastf1_no_standings", provider=self.provider_name, endpoint="get_constructor_standings", cache_status="fallback")

    async def get_qualifying(self, race_id: str):
        t0=time.time()
        if not self.client:
            return {}, DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_qualifying", cache_status="fallback")
        try:
            data = self.client.get_qualifying_results(race_id)  # type: ignore
            prov = DataProvenance(source="fastf1", provider=self.provider_name, endpoint=f"get_qualifying:{race_id}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data, prov
        except Exception:
            return {}, DataProvenance(source="fastf1_error", provider=self.provider_name, endpoint="get_qualifying", cache_status="fallback")

    async def get_weather(self, race_id: str, session: str):
        return {}, DataProvenance(source="fastf1_no_weather", provider=self.provider_name, endpoint="get_weather", cache_status="fallback")

    async def get_telemetry(self, session_key: str, driver: str):
        t0=time.time()
        if not self.client:
            return {}, DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_telemetry", cache_status="fallback")
        try:
            data = self.client.get_telemetry(session_key, driver)  # type: ignore
            prov = DataProvenance(source="fastf1", provider=self.provider_name, endpoint=f"get_telemetry:{session_key}:{driver}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data, prov
        except Exception:
            return {}, DataProvenance(source="fastf1_error", provider=self.provider_name, endpoint="get_telemetry", cache_status="fallback")

    async def get_pit_stops(self, session_key: str):
        return [], DataProvenance(source="fastf1_no_pit", provider=self.provider_name, endpoint="get_pit_stops", cache_status="fallback")

    async def get_race_control(self, session_key: str):
        return [], DataProvenance(source="fastf1_no_rc", provider=self.provider_name, endpoint="get_race_control", cache_status="fallback")

    async def health(self):
        if not self.client:
            return {"provider": self.provider_name, "status": "unavailable", "note": "fastf1 not installed or cache missing"}
        return {"provider": self.provider_name, "status": "available"}
