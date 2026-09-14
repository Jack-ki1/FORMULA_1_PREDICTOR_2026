"""
PredictionSnapshot — reproducible, auditable prediction context.
Every prediction traces exactly what it knew.
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import hashlib, json, uuid
from datetime import datetime, timezone
from backend.app.config.settings import settings

@dataclass
class PredictionSnapshot:
    snapshot_id: str = field(default_factory=lambda: f"snap_{uuid.uuid4().hex[:8]}")
    race_id: str = ""
    session: str = "race"
    sub_session: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data_cutoff: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    grid: Dict[str, int] = field(default_factory=dict)
    weather: Dict[str, Any] = field(default_factory=dict)  # rich: temp, humidity, rain_prob, wind...
    lineup: Dict[str, Any] = field(default_factory=dict)  # driver/constructor lineup at cutoff
    practice_data: Optional[Dict[str, Any]] = None
    qualifying_data: Optional[Dict[str, Any]] = None
    tyre_info: Optional[Dict[str, Any]] = None
    model_version: str = field(default_factory=lambda: getattr(settings, 'MODEL_VERSION', '12.4'))
    feature_version: str = field(default_factory=lambda: getattr(settings, 'FEATURE_VERSION', '8'))
    dataset_version: str = field(default_factory=lambda: getattr(settings, 'DATASET_VERSION', '14'))
    calibration_version: str = field(default_factory=lambda: getattr(settings, 'CALIBRATION_VERSION', '3.1'))
    simulation_count: int = 10000
    random_seed: int = 42
    config_hash: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        payload = {
            "race_id": self.race_id, "session": self.session, "sub_session": self.sub_session,
            "grid": self.grid, "weather": self.weather,
            "model_version": self.model_version, "feature_version": self.feature_version,
            "simulation_count": self.simulation_count, "random_seed": self.random_seed,
            "data_cutoff": self.data_cutoff,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        self.config_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self.config_hash

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["config_hash"] = self.compute_hash()
        return d

def build_snapshot(race_id: str, session_type: str, **kwargs) -> PredictionSnapshot:
    snap = PredictionSnapshot(
        race_id=race_id, session=session_type,
        sub_session=kwargs.get("sub_session",""),
        grid=kwargs.get("grid_positions",{}),
        weather=kwargs.get("weather", {"condition": kwargs.get("weather_condition","dry")}),
        simulation_count=kwargs.get("simulation_count",10000),
        random_seed=kwargs.get("random_seed",42),
    )
    if kwargs.get("provenance"):
        snap.provenance = kwargs["provenance"]
    snap.compute_hash()
    return snap
