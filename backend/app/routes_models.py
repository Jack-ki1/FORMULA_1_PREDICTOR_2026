from typing import Literal

from pydantic import BaseModel, Field

from .config import settings


class PredictIn(BaseModel):
    race_id: str | None = None
    sims: int = Field(3000, ge=100, le=settings.max_sims)
    session: Literal["practice", "qualifying", "race", "sprint"] = "race"
    weather: Literal["auto", "dry", "mixed", "wet"] = "auto"
    mechanical_failures: bool = True
    safety_car: bool = True
    enhanced: bool | None = None  # None -> server default (model_type)
    chaos: float = Field(0.5, ge=0, le=1)
    seed: int | None = None
    grid_mode: Literal["auto", "manual"] = "auto"
    grid: list[str] = Field(default_factory=list, max_length=30)  # slot P1..Pn -> driver code ("" = empty)
    # engine weights (defaults reproduce the base model)
    grid_weight: float = Field(0.55, ge=0, le=1)
    wet_influence: float = Field(0.6, ge=0, le=1)
    reliability: float = Field(0.4, ge=0, le=1)
    strategy_aggr: float = Field(0.5, ge=0, le=1)
    sc_weight: float = Field(0.3, ge=0, le=1)
    team_w: float = Field(0.6, ge=0, le=1)
    driver_w: float = Field(0.4, ge=0, le=1)
    track_w: float = Field(1.0, ge=0, le=2)
    weather_w: float = Field(1.0, ge=0, le=2)
    deg_w: float = Field(1.0, ge=0, le=2)
    form_k: float = Field(32.0, ge=8, le=64)
    ci: Literal[0.9, 0.95, 0.99] = 0.95


class ConfigPatch(BaseModel):
    cache_ttl: int | None = None
    live_interval: int | None = None
    source_priority: str | None = None
    model_type: str | None = None
