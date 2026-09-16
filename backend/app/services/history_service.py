"""
HistoryService — recorded predictions vs actual results, and the last-race
backtest strip.

Backs:
  GET /api/v1/predictions/history/{race_id}
  GET /api/v1/predictions/history/last

Why this exists: the Dashboard's "Model vs Last Race" strip used to hardcode
`actualWinner = 'ANT'` / `actualPodium = ['ANT','RUS','HAM']` against a fixed
race id, so it displayed a fabricated check/cross. This service reads real
recorded results (season_2026) and real model output, and returns `actual: null`
when there is genuinely nothing to compare — never a fake verdict.
(modify.md section 5)
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _completed_race_ids() -> List[str]:
    """Race ids in calendar order that already have a recorded result."""
    try:
        from backend.app.data.calendar_2026 import CALENDAR_2026
        from backend.app.data.season_2026 import SEASON_2026_RESULTS
        done = set(SEASON_2026_RESULTS.get("results", {}).keys())
        out = []
        for race in CALENDAR_2026:
            if race.get("round") in done:
                out.append(race.get("id"))
        return out
    except Exception as e:
        logger.warning("completed race scan failed: %s", e)
        return []


def _result_for_round(round_number: int) -> Optional[Dict[str, Any]]:
    try:
        from backend.app.data.season_2026 import get_race_result
        return get_race_result(round_number)
    except Exception:
        return None


def _round_for_race(race_id: str) -> Optional[int]:
    try:
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id)
        return race.get("round") if race else None
    except Exception:
        return None


def _predicted_for_race(race_id: str, simulation_count: int = 2000) -> Optional[Dict[str, Any]]:
    """Run the model for a race and extract winner/podium.

    If generation fails we return None and the caller reports
    "no prediction available" — never a fabricated result.
    """
    try:
        from backend.app.engine.predictor import generate_prediction
        res = generate_prediction(race_id, "race", simulation_count=simulation_count)
        winner = (res.get("predictions", {}).get("winner", {}) or {}).get("predictions", [])
        podium = (res.get("predictions", {}).get("podium", {}) or {}).get("predictions", [])
        return {
            "winner": winner[0]["driver_code"] if winner else None,
            "podium": [p["driver_code"] for p in podium[:3]],
            "confidence": (res.get("predictions", {}).get("winner", {}) or {}).get("confidence"),
            "source": (res.get("predictions", {}).get("winner", {}) or {}).get("source", "model"),
        }
    except Exception as e:
        logger.warning("predicted_for_race(%s) failed: %s", race_id, e)
        return None


class HistoryService:
    """Recorded actual results joined against what the model said."""

    def race_history(self, race_id: str, simulation_count: int = 2000) -> Dict[str, Any]:
        md = _round_for_race(race_id)
        actual = _result_for_round(md) if md is not None else None
        predicted = _predicted_for_race(race_id, simulation_count)
        actual_norm = None
        if actual:
            actual_norm = {
                "winner": actual.get("winner"),
                "podium": list(actual.get("podium", [])),
                "fastest_lap": actual.get("fastest_lap"),
                "safety_cars": actual.get("safety_cars"),
                "retirements": actual.get("retirements"),
            }
        scorable = bool(actual_norm and predicted)
        winner_match = bool(scorable and actual_norm.get("winner") == predicted.get("winner"))
        podium_match = bool(scorable and list(actual_norm.get("podium", [])) == list(predicted.get("podium", [])))
        note = None
        if not actual_norm:
            note = ("no recorded result for this round yet — 2026 races in the future "
                    "have no actual classification to score against")
        elif not predicted:
            note = "prediction could not be generated for this race"
        return {
            "race_id": race_id,
            "round": md,
            "actual": actual_norm,
            "predicted": predicted,
            "winner_match": winner_match if scorable else None,
            "podium_match": podium_match if scorable else None,
            "source": "season_2026 + model",
            "note": note,
        }

    def last_race(self, simulation_count: int = 2000) -> Dict[str, Any]:
        """Most recent race that has a recorded result, scored against the model."""
        completed = _completed_race_ids()
        if not completed:
            return {
                "race_id": None, "actual": None, "predicted": None,
                "winner_match": None, "podium_match": None,
                "source": "season_2026 + model",
                "note": "no completed races recorded in season_2026 yet",
            }
        return self.race_history(completed[-1], simulation_count=simulation_count)


history_service = HistoryService()
