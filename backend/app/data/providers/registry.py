"""
Provider Registry — priority rules + provenance aggregation + health.

Priority (per spec §26):
  live telemetry      → OpenF1
  historical telemetry→ OpenF1 / FastF1
  official results/standings → Jolpica
  static metadata     → local DB / fallback
  fallback            → cached previous successful response (file cache)

Application layer calls registry, not concrete clients.
"""
from typing import Any, Dict, List, Optional
from .base import DataProvenance
from .jolpica_provider import JolpicaProvider
from .openf1_provider import OpenF1Provider
from .fastf1_provider import FastF1Provider
from .fallback_provider import FallbackProvider

class ProviderRegistry:
    def __init__(self):
        self.jolpica = JolpicaProvider()
        self.openf1 = OpenF1Provider()
        self.fastf1 = FastF1Provider()
        self.fallback = FallbackProvider()

    # ---------- high-level federated methods ----------
    async def get_driver_standings(self, season: int):
        # try Jolpica live → fallback
        data, prov = await self.jolpica.get_driver_standings(season)
        # if fallback hash, it already fell back internally
        return data, prov

    async def get_constructor_standings(self, season: int):
        return await self.jolpica.get_constructor_standings(season)

    async def get_telemetry_federated(self, session_key: str, driver: str):
        # live → OpenF1; historical → FastF1; else fallback
        data, prov = await self.openf1.get_telemetry(session_key, driver)
        if data:
            return data, prov
        data2, prov2 = await self.fastf1.get_telemetry(session_key, driver)
        if data2:
            return data2, prov2
        return await self.fallback.get_telemetry(session_key, driver)

    async def get_weather_federated(self, race_id: str, session: str, session_key: Optional[str]=None):
        if session_key:
            data, prov = await self.openf1.get_weather(race_id, session_key)
            if data:
                return data, prov
        return await self.fallback.get_weather(race_id, session)

    async def get_pit_stops_federated(self, session_key: str):
        data, prov = await self.openf1.get_pit_stops(session_key)
        if data:
            return data, prov
        return await self.fallback.get_pit_stops(session_key)

    async def get_race_control_federated(self, session_key: str):
        data, prov = await self.openf1.get_race_control(session_key)
        if data:
            return data, prov
        return await self.fallback.get_race_control(session_key)

    async def health_all(self) -> Dict[str, Any]:
        return {
            "jolpica": await self.jolpica.health(),
            "openf1": await self.openf1.health(),
            "fastf1": await self.fastf1.health(),
            "fallback": await self.fallback.health(),
        }

registry = ProviderRegistry()
