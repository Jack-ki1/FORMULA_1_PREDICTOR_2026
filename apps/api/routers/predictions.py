"""
Predictions router.

Two read paths on purpose (see PLAN.md §3):

  - `GET /api/predictions/{race_id}` is the "normal" path a page load
    hits. It reads whatever `apps/ingest` most recently computed and
    stored in Postgres. If nothing's been ingested yet for this race
    (e.g. running fully locally without ever having run the ingest
    script), it transparently falls back to computing once, on demand,
    and persists the result — so the API is still fully functional
    standalone, it's just not the steady-state behavior in production.

  - `POST /api/predictions/{race_id}/recompute` is the explicit
    "what-if" path: always runs a fresh Monte Carlo simulation with
    whatever weights/grid/weather the caller passes, never reads or
    writes the shared cached row. This is what the frontend's what-if
    slider panel calls.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.settings import settings
from database.db import get_db
from data.calendar_2026 import CALENDAR_2026, get_race_by_id
from engine.predictor import generate_prediction
from models.prediction import Prediction

logger = logging.getLogger(__name__)
router = APIRouter()


class AIConfig(BaseModel):
    ai_mode: str = "normal"
    ai_model: str = "gemini-2.0-flash-exp"
    ai_api_key: str = ""
    ai_weight: float = 0.3
    ai_temperature: float = 0.7


class RecomputeRequest(BaseModel):
    session_type: str = "race"
    sub_session: str | None = None
    weather: str = "dry"
    grid_positions: dict[str, int] | None = None
    feature_weights: dict[str, float] | None = None
    simulation_count: int = Field(default=10000, ge=settings.SIMULATION_MIN_COUNT, le=settings.SIMULATION_MAX_COUNT)
    ai: AIConfig = AIConfig()


class ChatRequest(BaseModel):
    message: str
    model: str = "gemini-2.0-flash-exp"
    api_key: str = ""
    temperature: float = 0.7


@router.get("/races")
def list_races():
    """Full 2026 calendar, cancelled events excluded."""
    return [race for race in CALENDAR_2026 if race.get("status") != "cancelled"]


@router.get("/race-result/{race_id}")
def race_result(race_id: str):
    race = get_race_by_id(race_id)
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    if race.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Race not yet completed")
    return race


def _rows_to_response(rows: list[Prediction]) -> dict[str, Any]:
    probabilities = {row.driver_code: row.probability for row in rows}
    confidence_intervals = {row.driver_code: row.confidence_interval for row in rows if row.confidence_interval}
    return {
        "race_id": rows[0].race_id,
        "session_type": rows[0].session_type,
        "model_version": rows[0].model_version,
        "generated_at": rows[0].created_at.isoformat() if rows[0].created_at else None,
        "source": "precomputed",
        "winner_probabilities": probabilities,
        "confidence_intervals": confidence_intervals,
    }


@router.get("/predictions/{race_id}")
def get_predictions(race_id: str, session_type: str = "race", db: Session = Depends(get_db)):
    if not get_race_by_id(race_id):
        raise HTTPException(status_code=404, detail="Race not found")

    # Most recent batch: same race_id/session_type, most recent created_at.
    latest = (
        db.query(Prediction)
        .filter(Prediction.race_id == race_id, Prediction.session_type == session_type)
        .order_by(desc(Prediction.created_at))
        .first()
    )
    if latest:
        rows = (
            db.query(Prediction)
            .filter(
                Prediction.race_id == race_id,
                Prediction.session_type == session_type,
                Prediction.created_at == latest.created_at,
            )
            .all()
        )
        return _rows_to_response(rows)

    # Nothing precomputed yet (apps/ingest hasn't run for this race) —
    # compute once, on demand, so the API still works standalone.
    logger.info(f"No precomputed prediction for {race_id}/{session_type}; computing on demand")
    try:
        result = generate_prediction(race_id=race_id, session_type=session_type)
        result["source"] = "computed_on_demand"
        return result
    except Exception as e:
        logger.error(f"Prediction error for race {race_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions/{race_id}/recompute")
def recompute_prediction(race_id: str, body: RecomputeRequest):
    if not get_race_by_id(race_id):
        raise HTTPException(status_code=404, detail="Race not found")
    try:
        result = generate_prediction(
            race_id=race_id,
            session_type=body.session_type,
            sub_session=body.sub_session,
            weather=body.weather,
            grid_positions=body.grid_positions,
            feature_weights=body.feature_weights,
            simulation_count=body.simulation_count,
            ai_config=body.ai.model_dump(),
        )
        result["source"] = "what_if"
        return result
    except Exception as e:
        logger.error(f"Recompute error for race {race_id}: {e}")
        if settings.DEBUG:
            import traceback
            logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-chat")
def ai_chat(body: ChatRequest):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    system_prompt = (
        "You are an expert Formula 1 analyst and racing strategist. You have deep "
        "knowledge of current F1 regulations, driver performance histories, team "
        "strategies, circuit layouts, weather impacts, and tyre strategies. Provide "
        "detailed, accurate, and insightful responses about F1 racing. When discussing "
        "predictions or probabilities, always acknowledge uncertainty. Be specific but "
        "cautious about definitive predictions."
    )
    enhanced_message = f"{system_prompt}\n\nUser question: {body.message}"

    try:
        from engine.ai_client import ai_client

        if body.api_key:
            res = ai_client.call_ai(
                model=body.model, api_key=body.api_key, prompt=enhanced_message,
                temperature=body.temperature, max_tokens=1500,
            )
            if res and "text" in res:
                return {"response": res["text"], "provider": res.get("provider"), "model": body.model}
            fallback = (
                "I'm having trouble connecting to the AI service right now. You can still "
                "get predictions from the traditional ML models on the predictions page, "
                "or try again with a valid API key for AI-enhanced responses."
            )
            return {"response": fallback, "provider": "fallback", "model": body.model}

        from ai.provider import AIProviderManager
        manager = AIProviderManager()
        result = manager.predict(prompt=enhanced_message)
        return {"response": result.get("text", str(result)), "provider": "fallback", "model": body.model}
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return {
            "response": f"I encountered an error processing your request: {e}. Please check your API key and try again.",
            "provider": "error",
            "model": body.model,
        }
