"""
F1 Data Provider abstraction — the application never calls Jolpica/OpenF1/FastF1 directly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import hashlib
import json
from datetime import datetime, timezone

@dataclass
class DataProvenance:
    source: str
    provider: str
    endpoint: str
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    effective_at: Optional[str] = None
    response_hash: str = ""
    schema_version: str = "1.0"
    cache_status: str = "miss"  # hit/miss/fallback
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def hash_response(data: Any) -> str:
    try:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
    except Exception:
        return ""

class F1DataProvider(ABC):
    """Abstract provider — all data access goes through this interface."""

    provider_name: str = "base"

    # Some providers render their own fallback inside an except block and return
    # a `local_seed` provenance with HTTP 200, so `health()` used to report
    # "healthy" even when zero live data was reachable — the health check only
    # asked "did the call throw?", not "did we get live data?" (modify.md s2).
    last_call_used_fallback: bool = False
    def health_from_provenance(self, prov: "DataProvenance", error: str | None = None) -> Dict[str, Any]:
        """Build a health dict that tells the truth about data freshness.

        `degraded` means the provider answered, but the answer came from a
        fallback/seed path rather than the upstream source.
        """
        used_fallback = prov.cache_status == "fallback"
        self.last_call_used_fallback = used_fallback
        status = "degraded" if (used_fallback or error) else "healthy"
        out: Dict[str, Any] = {
            "provider": self.provider_name,
            "status": status,
            "source": prov.source,
            "cache_status": prov.cache_status,
        }
        if prov.latency_ms is not None:
            out["latency_ms"] = round(prov.latency_ms, 1)
        if used_fallback:
            out["reason"] = "serving fallback/seed data — upstream source not returning live results"
        if error:
            out["error"] = error
        return out
    @abstractmethod
    async def get_calendar(self, season: int) -> tuple[List[Dict[str, Any]], DataProvenance]:
        ...

    @abstractmethod
    async def get_sessions(self, race_id: str, season: int) -> tuple[List[Dict[str, Any]], DataProvenance]:
        ...

    @abstractmethod
    async def get_results(self, race_id: str, session: str) -> tuple[Dict[str, Any], DataProvenance]:
        ...

    @abstractmethod
    async def get_driver_standings(self, season: int) -> tuple[List[Dict[str, Any]], DataProvenance]:
        ...

    @abstractmethod
    async def get_constructor_standings(self, season: int) -> tuple[List[Dict[str, Any]], DataProvenance]:
        ...

    @abstractmethod
    async def get_qualifying(self, race_id: str) -> tuple[Dict[str, Any], DataProvenance]:
        ...

    @abstractmethod
    async def get_weather(self, race_id: str, session: str) -> tuple[Dict[str, Any], DataProvenance]:
        ...

    @abstractmethod
    async def get_telemetry(self, session_key: str, driver: str) -> tuple[Dict[str, Any], DataProvenance]:
        ...

    @abstractmethod
    async def get_pit_stops(self, session_key: str) -> tuple[List[Dict[str, Any]], DataProvenance]:
        ...

    @abstractmethod
    async def get_race_control(self, session_key: str) -> tuple[List[Dict[str, Any]], DataProvenance]:
        ...

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        ...
