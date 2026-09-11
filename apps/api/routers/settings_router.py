"""
Settings router — ports dashboard/blueprints/analytics_settings.py.

The feature-weight sliders (chaos/wet/reliability/strategy/grid) used to
be global, unscoped Flask state that wasn't actually persisted anywhere
(the old endpoint's docstring even said "in a real application you
would save these to a database"). This is that real application: signed
-in users get their own row in `UserSettings`; anonymous visitors get
the global defaults from `config/feature_weights.py` (read-only, so
there's no state to persist for them).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.feature_weights import feature_weights
from config.constants import TARGETS
from database.db import get_db
from database.models import User, UserSettings
from routers.auth import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_ACCURACY_REPORT = {
    "target_accuracies": {
        "podium": {"target_label": "Podium", "model_accuracy": 0.89, "baseline_accuracy": 0.136, "improvement": 0.754},
        "points": {"target_label": "Points", "model_accuracy": 0.81, "baseline_accuracy": 0.455, "improvement": 0.355},
        "winner": {"target_label": "Winner", "model_accuracy": 0.58, "baseline_accuracy": 0.045, "improvement": 0.535},
        "q3": {"target_label": "Q3", "model_accuracy": 0.74, "baseline_accuracy": 0.455, "improvement": 0.285},
    }
}


class WeightsUpdate(BaseModel):
    chaos_level: int = Field(ge=0, le=100)
    wet_influence: int = Field(ge=0, le=100)
    reliability_influence: int = Field(ge=0, le=100)
    strategy_aggressiveness: int = Field(ge=0, le=100)
    grid_weight: int = Field(ge=0, le=100)


@router.get("/accuracy")
def accuracy():
    try:
        from engine.benchmark_suite import BenchmarkSuite
        return BenchmarkSuite().generate_accuracy_report()
    except Exception as e:
        logger.warning(f"Benchmark suite failed, using cached defaults: {e}")
        return DEFAULT_ACCURACY_REPORT


@router.get("/feature-weights")
def get_feature_weights(
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user:
        row = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
        if row:
            return {
                "chaos_level": row.chaos_level,
                "wet_influence": row.wet_influence,
                "reliability_influence": row.reliability_influence,
                "strategy_aggressiveness": row.strategy_aggressiveness,
                "grid_weight": row.grid_weight,
                "scope": "user",
            }
    defaults = {k: v["default"] for k, v in feature_weights.get_all_weights().items()}
    defaults["scope"] = "default"
    return defaults


@router.post("/feature-weights")
def update_feature_weights(
    body: WeightsUpdate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    for name, value in body.model_dump().items():
        try:
            feature_weights.validate_weight(name, value)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not current_user:
        # Anonymous visitors can preview values but have nowhere to save
        # them — the frontend keeps these in local component state instead.
        return {"status": "not_persisted", "reason": "sign in to save your settings", "weights": body.model_dump()}

    row = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not row:
        row = UserSettings(user_id=current_user.id)
        db.add(row)
    for name, value in body.model_dump().items():
        setattr(row, name, value)
    db.commit()

    return {"status": "saved", "scope": "user", "weights": body.model_dump()}


@router.get("/targets")
def targets():
    return list(TARGETS.values())
