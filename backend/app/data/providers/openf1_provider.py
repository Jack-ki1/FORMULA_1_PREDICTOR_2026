"""
OpenF1 Provider — live telemetry, sessions, pit, race control, weather.
"""
import time
from typing import Any, Dict, List
from .base import F1DataProvider, DataProvenance, hash_response

class OpenF1Provider(F1DataProvider):
    provider_name = "openf1"
    def __init__(self):
        try:
            from backend.app.data.openf1_client import OpenF1Client
            self.client = OpenF1Client()
        except Exception:
            self.client = None

    async def get_calendar(self, season: int):
        prov = DataProvenance(source="openf1_no_calendar", provider=self.provider_name, endpoint="get_calendar", cache_status="fallback")
        return [], prov

    async def get_sessions(self, race_id: str, season: int):
        t0=time.time()
        if not self.client:
            return [], DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_sessions", cache_status="fallback")
        try:
            data = self.client.get_sessions(year=season)  # type: ignore
            prov = DataProvenance(source="openf1", provider=self.provider_name, endpoint="get_sessions", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data if isinstance(data, list) else [], prov
        except Exception as e:
            return [], DataProvenance(source="openf1_error", provider=self.provider_name, endpoint="get_sessions", cache_status="fallback")

    async def get_results(self, race_id: str, session: str):
        return {}, DataProvenance(source="openf1_no_results", provider=self.provider_name, endpoint="get_results", cache_status="fallback")

    async def get_driver_standings(self, season: int):
        return [], DataProvenance(source="openf1_no_standings", provider=self.provider_name, endpoint="get_driver_standings", cache_status="fallback")

    async def get_constructor_standings(self, season: int):
        return [], DataProvenance(source="openf1_no_standings", provider=self.provider_name, endpoint="get_constructor_standings", cache_status="fallback")

    async def get_qualifying(self, race_id: str):
        return {}, DataProvenance(source="openf1_no_qualifying", provider=self.provider_name, endpoint="get_qualifying", cache_status="fallback")

    async def get_weather(self, race_id: str, session: str):
        t0=time.time()
        if not self.client:
            return {}, DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_weather", cache_status="fallback")
        try:
            data = self.client.get_weather(session_key=session)  # type: ignore
            prov = DataProvenance(source="openf1", provider=self.provider_name, endpoint=f"get_weather:{session}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data, prov
        except Exception:
            return {}, DataProvenance(source="openf1_error", provider=self.provider_name, endpoint="get_weather", cache_status="fallback")

    async def get_telemetry(self, session_key: str, driver: str):
        t0=time.time()
        if not self.client:
            return {}, DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_telemetry", cache_status="fallback")
        try:
            data = self.client.get_car_data(session_key=session_key, driver_number=driver)  # type: ignore
            prov = DataProvenance(source="openf1", provider=self.provider_name, endpoint=f"get_telemetry:{session_key}:{driver}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data, prov
        except Exception:
            return {}, DataProvenance(source="openf1_error", provider=self.provider_name, endpoint="get_telemetry", cache_status="fallback")

    async def get_pit_stops(self, session_key: str):
        t0=time.time()
        if not self.client:
            return [], DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_pit_stops", cache_status="fallback")
        try:
            data = self.client.get_pit_stops(session_key=session_key)  # type: ignore
            prov = DataProvenance(source="openf1", provider=self.provider_name, endpoint=f"get_pit_stops:{session_key}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data if isinstance(data, list) else [], prov
        except Exception:
            return [], DataProvenance(source="openf1_error", provider=self.provider_name, endpoint="get_pit_stops", cache_status="fallback")

    async def get_race_control(self, session_key: str):
        t0=time.time()
        if not self.client:
            return [], DataProvenance(source="unavailable", provider=self.provider_name, endpoint="get_race_control", cache_status="fallback")
        try:
            data = self.client.get_race_control(session_key=session_key)  # type: ignore
            prov = DataProvenance(source="openf1", provider=self.provider_name, endpoint=f"get_race_control:{session_key}", response_hash=hash_response(data), latency_ms=(time.time()-t0)*1000)
            return data if isinstance(data, list) else [], prov
        except Exception:
            return [], DataProvenance(source="openf1_error", provider=self.provider_name, endpoint="get_race_control", cache_status="fallback")

    async def health(self):
        if not self.client:
            return {"provider": self.provider_name, "status": "unavailable"}
        try:
            await self.get_sessions("au", 2026)
            return {"provider": self.provider_name, "status": "healthy"}
        except Exception as e:
            return {"provider": self.provider_name, "status": "degraded", "error": str(e)}
