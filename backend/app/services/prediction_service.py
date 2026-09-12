"""
PredictionService — thin orchestration layer over engine.predictor.generate_prediction.
Preserves 1:1 input->engine->output parity; adds validation, logging, authorization boundary.
"""
import logging
import hashlib
import json
from typing import Any, Dict, Optional
from engine.predictor import generate_prediction

logger = logging.getLogger(__name__)

class PredictionService:
    """Service boundary for all prediction generation."""

    @staticmethod
    def _grid_hash(grid: Optional[Dict[str,int]]) -> str:
        if not grid:
            return "nogrid"
        s = json.dumps(grid, sort_keys=True)
        return hashlib.md5(s.encode()).hexdigest()[:8]

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        race_id = payload.get("race_id")
        if not race_id or not isinstance(race_id, str):
            raise ValueError("race_id is required and must be a string")
        session_type = payload.get("session_type", "race")
        sub_session = payload.get("sub_session")
        weather = payload.get("weather", "dry")
        grid_positions = payload.get("grid_positions")
        feature_weights = payload.get("feature_weights")
        simulation_count = payload.get("simulation_count", 10000)
        ai_config = payload.get("ai_config") or {
            "ai_mode": payload.get("ai_mode", "normal"),
            "ai_model": payload.get("ai_model", "gemini-2.0-flash-exp"),
            "ai_api_key": payload.get("ai_api_key", ""),
            "ai_weight": payload.get("ai_weight", 0.3),
            "ai_temperature": payload.get("ai_temperature", 0.7),
        }
        # normalize simulation_count bounds (authoritative source = settings + predictor clamping)
        try:
            simulation_count = int(simulation_count)
        except Exception:
            simulation_count = 10000
        logger.info("PredictionService.generate race=%s session=%s weather=%s sims=%s grid_hash=%s",
                    race_id, session_type, weather, simulation_count, self._grid_hash(grid_positions))
        result = generate_prediction(
            race_id=race_id,
            session_type=session_type,
            sub_session=sub_session,
            weather=weather,
            grid_positions=grid_positions,
            feature_weights=feature_weights,
            simulation_count=simulation_count,
            ai_config=ai_config,
        )
        return result

prediction_service = PredictionService()
