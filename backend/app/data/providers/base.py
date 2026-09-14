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
