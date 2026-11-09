from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .config import settings


class PredictIn(BaseModel):
    race_id: str | None = None
    sims: int = Field(3000, ge=100, le=settings.max_sims)
    session: Literal["practice", "qualifying", "sprint_qualifying", "sprint", "race"] = "race"
    sub: Literal["", "FP1", "FP2", "FP3"] = ""  # practice only; "" means FP2
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
    # --- new in v2 ---
    grid_known_min: float = Field(0.50, ge=0.5, le=0.9)
    rating_sd: float = Field(0.20, ge=0.0, le=0.6)
    team_share: float = Field(0.35, ge=0.0, le=0.8)

    @model_validator(mode="after")
    def _validate_session_sub(self) -> "PredictIn":
        # practice sub must be offered by the race; sprint/sprint_qualifying require a sprint weekend
        # (checked against snap data in service.run_prediction where the race is known)
        return self


class H2HIn(PredictIn):
    a: str
    b: str


class FantasyEvaluateIn(PredictIn):
    picks: list[str] = Field(default_factory=list, max_length=20)
    budget: float | None = None


class ConfigPatch(BaseModel):
    cache_ttl: int | None = None
    live_interval: int | None = None
    source_priority: str | None = None
    model_type: str | None = None
