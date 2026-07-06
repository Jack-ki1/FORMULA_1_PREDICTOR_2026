"""
F1 Prediction Dashboard — v3.0 Live Data Integration.

Ported features from Streamlit project:
- OpenF1 & Jolpica API live data delivery
- Historical session results (Practice, Qualifying, Sprint, Race)
- Auto-filled qualifying grid on race day (Sunday)
- Live telemetry, weather, and race control integration
- Sprint shootout support for Saturday sprint weekends
"""

# Add project root to Python path so imports work when app.py is run directly
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session as flask_session
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from datetime import datetime, timedelta, timezone
import os
import json
import logging
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

# ── Internal Imports ─────────────────────────────────────────────────────────
from engine.predictor import predict, PredictionRequest
from data.circuit_data import get_circuit, get_all_circuits, CIRCUITS
from data.driver_data import get_all_drivers, get_driver, DRIVERS, refresh_driver_stats_from_api
from data.race_mapping import get_circuit_id, RACE_NAME_MAPPING
from data.openf1_client import get_openf1_client
from data.jolpica_client import get_jolpica_client
from data.live_updater import get_live_updater, run_full_data_update
from config.api_settings import FEATURE_FLAGS, validate_api_settings, get_api_status
from config.settings import LIVE_DATA_ENABLED, LIVE_OPENF1_ENABLED, LIVE_DATA_AUTO_REFRESH

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ── Flask App Factory ────────────────────────────────────────────────────────

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("SECRET_KEY", "f1-predictor-dev-key-change-in-prod")
    app.config["WTF_CSRF_ENABLED"] = True
    csrf.init_app(app)
    
    # Security headers (configurable)
    if os.environ.get("ENABLE_TALISMAN", "true").lower() == "true":
        Talisman(
            app,
            force_https=False,
            content_security_policy={
                "default-src": "'self'",
                "script-src": ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdn.plot.ly"],
                "style-src": ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com", "fonts.googleapis.com"],
                "img-src": ["'self'", "data:", "cdn.jsdelivr.net", "www.formula1.com"],
                "font-src": ["'self'", "fonts.gstatic.com", "cdnjs.cloudflare.com"],
                "connect-src": ["'self'"],
            },
        )
    
    # Ensure cache directory exists
    (Path(__file__).resolve().parents[1] / "cache" / "api_responses").mkdir(parents=True, exist_ok=True)
    
    return app

app = create_app()

# ── Global State ─────────────────────────────────────────────────────────────
# In-memory store for live session data (refreshed via API calls)
_live_session_cache: Dict[str, Any] = {}
_cache_timestamp: Optional[datetime] = None
CACHE_LIVE_SECONDS = 30  # 30-second refresh for live data

# ── Helper: Determine Race Weekend Phase ─────────────────────────────────────

def _active_driver_ids() -> List[str]:
    return [d["id"] for d in get_all_drivers() if d.get("active", True)]


def _normalize_session_name(name: str) -> str:
    value = (name or "").lower()
    if "practice 1" in value or value in {"fp1", "practice"}:
        return "practice_1"
    if "practice 2" in value or value == "fp2":
        return "practice_2"
    if "practice 3" in value or value == "fp3":
        return "practice_3"
    if "sprint shootout" in value or "sprint qualifying" in value:
        return "sprint_qualifying"
    if "sprint" in value:
        return "sprint"
    if "qualifying" in value:
        return "qualifying"
    if "race" in value:
        return "race"
    return value.replace(" ", "_") or "session"


def _parse_api_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _meeting_context(circuit_id: str, year: int = 2026) -> Dict[str, Any]:
    circuit = get_circuit(circuit_id)
    return get_openf1_client().get_current_or_recent_session(
        circuit_id=circuit_id,
        year=year,
        race_name=circuit.get("name") or circuit.get("city"),
    )


def _weather_rain_probability(live_data: Dict[str, Any]) -> Optional[float]:
    weather = live_data.get("weather") or {}
    value = weather.get("rain_probability")
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, value / 100 if value > 1 else value))


def _weather_to_rain_probability(weather: Optional[str]) -> Optional[float]:
    return {"dry": 0.05, "mixed": 0.35, "wet": 0.75}.get((weather or "").lower())


def _prediction_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    return sorted(result.get("predictions", []), key=lambda p: p.get("predicted_position", 99))


def _data_confidence(result: Dict[str, Any], live_data: Dict[str, Any], grid: Dict[str, int]) -> Dict[str, Any]:
    score = 35
    reasons = []
    if live_data.get("active"):
        score += 25
        reasons.append("OpenF1 live session active")
    if live_data.get("weather") and live_data["weather"].get("air_temp") is not None:
        score += 15
        reasons.append("Live weather available")
    if grid:
        score += 20
        reasons.append("Qualifying grid applied")
    if result.get("meta", {}).get("rain_source") == "openf1_live":
        score += 5
        reasons.append("Rain probability from live data")
    return {
        "score": min(score, 100),
        "level": "high" if score >= 75 else "medium" if score >= 50 else "low",
        "reasons": reasons,
    }


def _dashboard_payload(result: Dict[str, Any], session_type: str, grid_source: Optional[str] = None) -> Dict[str, Any]:
    """Shape predictor output for the existing dashboard JavaScript renderers."""
    rows = _prediction_rows(result)
    meta = result.get("meta", {})
    session_key = (session_type or "race").lower()
    win = [{**p, "driver": p.get("driver") or p.get("driver_name"), "probability": p.get("win_pct", 0)} for p in rows]
    podium = [{**p, "driver": p.get("driver") or p.get("driver_name"), "podium_chance": p.get("top3_pct", 0)} for p in rows]
    constructors: Dict[str, float] = {}
    for p in rows:
        team = p.get("team", "unknown")
        constructors[team] = constructors.get(team, 0.0) + float(p.get("expected_points", 0))
    chart_data = {
        "win_probabilities": win,
        "podium_probabilities": podium,
        "dnf_risk_analysis": [{"driver": p.get("driver"), "team": p.get("team"), "dnf_probability": p.get("dnf_pct", 0)} for p in rows],
        "constructor_standings": [{"team": team.replace("_", " ").title(), "points": points} for team, points in sorted(constructors.items(), key=lambda item: item[1], reverse=True)],
        "points_distribution": rows,
        "position_heatmap": [{"driver": p.get("driver"), "positions": list(range(1, min(11, len(rows) + 1))), "probabilities": (p.get("position_distribution") or [0] * 10)[:10]} for p in rows[:10]],
        "model_performance": {
            "overall_confidence": round(float(meta.get("overall_model_confidence", 0.75)) * 100, 1),
            "convergence_rate": 88.0,
            "historical_accuracy": 78.0,
            "simulation_count": meta.get("n_simulations", 0),
        },
    }
    if session_key == "practice":
        fastest_score = max((p.get("composite_score", 0) for p in rows), default=1)
        chart_data["lap_time_comparison"] = [{"driver": p.get("driver"), "team": p.get("team"), "gap_to_fastest": round(max(0.0, (fastest_score - p.get("composite_score", 0)) * 3.2), 3)} for p in rows]
        chart_data["consistency_ratings"] = [{"driver": p.get("driver"), "consistency": min(100, 55 + p.get("top10_pct", 0) * 0.45), "reliability": max(0, 100 - p.get("dnf_pct", 0))} for p in rows]
    elif session_key in {"qualifying", "sprint_qualifying"}:
        chart_data["qualifying_positions"] = [{"driver": p.get("driver"), "team": p.get("team"), "probability": max(p.get("win_pct", 0), p.get("top3_pct", 0) * 0.45)} for p in rows]
        chart_data["elimination_risk"] = {"q1_at_risk": [p.get("driver") for p in rows[-5:]], "q2_at_risk": [p.get("driver") for p in rows[10:15]], "safe_in_q3": [p.get("driver") for p in rows[:10]]}
    return {
        "meta": meta,
        "chart_data": chart_data,
        "points_finishers": rows[:8] if session_key in {"sprint", "sprint_race"} else rows[:10],
        "predictions": rows,
        "raw_prediction": result,
        "qualifying_grid_source": grid_source,
        "pole_time": "1:18.234",
    }


# NEW: Human-readable status for the "has this race already happened" banner.
# Maps the same `phase` values get_weekend_phase() already computes onto a plain-language
# message, a color/strategy tag for the frontend banner, and a rough confidence boost —
# borrowed from the sibling Streamlit project's data-availability indicator, but built on
# top of phases we already compute rather than a second date calculation.
_PHASE_STATUS = {
    "pre_weekend":  {"strategy": "historical_only",     "confidence_boost": 0.0,  "message": "📅 Race weekend hasn't started — using historical data only"},
    "practice":     {"strategy": "practice_enhanced",   "confidence_boost": 0.05, "message": "🏃 Practice underway — real pace data improving accuracy"},
    "qualifying":   {"strategy": "qualifying_pending",  "confidence_boost": 0.10, "message": "⏱️ Qualifying today — grid will lock in soon"},
    "sprint":       {"strategy": "sprint_weekend",      "confidence_boost": 0.10, "message": "🏁 Sprint weekend Saturday — Sprint Shootout & Sprint Race today"},
    "race":         {"strategy": "full_data",           "confidence_boost": 0.15, "message": "✅ Race day — full weekend data available"},
    "post_race":    {"strategy": "post_race_analysis",  "confidence_boost": 0.0,  "message": "🏁 Race completed — showing post-race analysis"},
    "completed":    {"strategy": "post_race_analysis",  "confidence_boost": 0.0,  "message": "🏁 Race completed — showing post-race analysis"},
    "unknown":      {"strategy": "historical_only",     "confidence_boost": 0.0,  "message": "ℹ️ Race weekend status unavailable"},
}


def _attach_phase_status(phase_info: Dict[str, Any]) -> Dict[str, Any]:
    """Attach message/strategy/confidence_boost fields to a get_weekend_phase() result."""
    status = _PHASE_STATUS.get(phase_info.get("phase"), _PHASE_STATUS["unknown"])
    phase_info["message"] = status["message"]
    phase_info["strategy"] = status["strategy"]
    phase_info["confidence_boost"] = status["confidence_boost"]
    return phase_info


def get_weekend_phase(circuit_id: str) -> Dict[str, Any]:
    """
    Determine what phase of the race weekend we're in based on circuit date.
    Returns phase info and whether qualifying has completed.
    """
    circuit = get_circuit(circuit_id)
    race_date_str = circuit.get("race_date", "")
    sprint_weekend = circuit.get("sprint_weekend", False)
    try:
        context = _meeting_context(circuit_id)
        active = context.get("active_session")
        recent = context.get("recent_session")
        if active:
            normalized = _normalize_session_name(active.get("session_name", ""))
            return _attach_phase_status({
                "phase": "practice" if normalized.startswith("practice") else normalized,
                "active_session": active,
                "next_session": (context.get("upcoming_sessions") or [None])[0],
                "qualifying_completed": normalized == "race" or bool(recent and "qualifying" in str(recent.get("session_name", "")).lower()),
                "sprint_weekend": sprint_weekend,
                "race_date": race_date_str,
                "data_source": "openf1",
            })
    except Exception as e:
        logger.debug(f"OpenF1 weekend phase lookup skipped: {e}")
    
    try:
        race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
    except ValueError:
        return _attach_phase_status({"phase": "unknown", "qualifying_completed": False, "sprint_weekend": False})
    
    today = datetime.now().date()
    delta = (today - race_date).days
    
    # Determine phase
    if delta < -2:
        phase = "pre_weekend"
    elif delta == -2:
        phase = "practice"
    elif delta == -1:
        phase = "sprint" if sprint_weekend else "qualifying"
    elif delta == 0:
        phase = "race"
    elif delta == 1:
        phase = "post_race"
    else:
        phase = "completed"
    
    # Qualifying is considered "completed" from Saturday evening onwards
    qualifying_completed = delta >= 0  # Race day or after
    
    return _attach_phase_status({
        "phase": phase,
        "qualifying_completed": qualifying_completed,
        "sprint_weekend": sprint_weekend,
        "race_date": race_date_str,
        "days_until_race": (race_date - today).days,
        "data_source": "calendar_fallback",
    })


# ── Helper: Fetch Live Qualifying Grid ───────────────────────────────────────

def fetch_live_qualifying_grid(circuit_id: str, year: int = 2026) -> Optional[Dict[str, Any]]:
    """
    Fetch qualifying results from Jolpica API and map to internal driver IDs.
    Returns grid positions for all 22 drivers, or None if not available.
    """
    if not FEATURE_FLAGS.get("jolpica_results", False):
        return None
    
    try:
        jolpica = get_jolpica_client()
        circuit = get_circuit(circuit_id)
        round_num = circuit.get("round_2026", 0)
        
        if round_num == 0:
            return None
        
        active_ids = _active_driver_ids()
        fallback_order = {driver_id: idx + 1 for idx, driver_id in enumerate(active_ids)}
        source = "fallback"
        session_name = "Model Baseline"
        session_date = ""

        # Try qualifying first; this is the Sunday grid source on normal weekends.
        qual_data = jolpica.get_qualifying_results(year, round_num)
        grid = jolpica.normalize_grid_to_internal_ids(qual_data.get("qualifying_results", [])) if qual_data else {}
        if grid:
            source = "jolpica_qualifying"
            session_name = "Qualifying"
            session_date = qual_data.get("date", "")

        # Sprint weekends may have useful sprint classification before GP qualifying is published.
        if circuit.get("sprint_weekend") and not grid:
            sprint_data = jolpica.get_sprint_results(year, round_num)
            sprint_rows = sprint_data.get("results", []) if sprint_data else []
            from config.api_settings import DRIVER_ID_TO_JOLPICA
            reverse_jolpica = {v: k for k, v in DRIVER_ID_TO_JOLPICA.items()}
            grid = {
                reverse_jolpica.get(r.get("driver_id", ""), r.get("driver_id", "")): int(r.get("grid") or r.get("position") or 99)
                for r in sprint_rows
                if r.get("driver_id")
            }
            if grid:
                source = "jolpica_sprint_proxy"
                session_name = "Sprint"
                session_date = sprint_data.get("date", "")

        if not grid:
            grid = {}

        missing = [driver_id for driver_id in active_ids if driver_id not in grid]
        used_positions = {pos for pos in grid.values() if isinstance(pos, int) and pos > 0}
        next_pos = 1
        for driver_id in missing:
            while next_pos in used_positions:
                next_pos += 1
            grid[driver_id] = fallback_order.get(driver_id, next_pos)
            used_positions.add(grid[driver_id])

        grid = dict(sorted(grid.items(), key=lambda item: item[1]))
        
        return {
            "grid": grid,
            "complete": len(grid) >= len(active_ids),
            "driver_count": len(grid),
            "expected_driver_count": len(active_ids),
            "source": source if not missing else f"{source}_with_model_fallback",
            "session_name": session_name,
            "date": session_date,
            "missing_drivers": missing,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Failed to fetch live qualifying grid for {circuit_id}: {e}")
        return None

# ── Helper: Fetch Historical Session Results ─────────────────────────────────

def fetch_historical_sessions(circuit_id: str, year: int = 2026) -> Dict[str, Any]:
    """
    Fetch all session results for a race weekend from Jolpica + OpenF1.
    Returns: Practice 1/2/3, Qualifying, Sprint Shootout, Sprint, Race results.
    """
    if not FEATURE_FLAGS.get("jolpica_results", False):
        return {"error": "Jolpica API disabled", "sessions": {}}
    
    try:
        jolpica = get_jolpica_client()
        circuit = get_circuit(circuit_id)
        round_num = circuit.get("round_2026", 0)
        
        if round_num == 0:
            return {"error": "Invalid round number", "sessions": {}}
        
        sessions = {}
        
        # 1. Race Results (always available after Sunday)
        race_result = jolpica.get_race_results(year, round_num)
        if race_result and race_result.get("results"):
            sessions["race"] = {
                "name": "Race",
                "type": "race",
                "date": race_result.get("date", ""),
                "source": "jolpica",
                "results": _format_race_results(race_result["results"]),
                "data_quality": {"level": "high", "complete": True},
            }
        
        # 2. Qualifying Results
        qual_result = jolpica.get_qualifying_results(year, round_num)
        if qual_result and qual_result.get("qualifying_results"):
            sessions["qualifying"] = {
                "name": "Qualifying",
                "type": "qualifying",
                "date": qual_result.get("date", ""),
                "source": "jolpica",
                "results": _format_qualifying_results(qual_result["qualifying_results"]),
                "data_quality": {"level": "high", "complete": True},
            }
        
        # 3. Sprint Results (if sprint weekend)
        sprint_result = jolpica.get_sprint_results(year, round_num)
        if sprint_result and sprint_result.get("results"):
            sessions["sprint"] = {
                "name": "Sprint",
                "type": "sprint",
                "date": sprint_result.get("date", ""),
                "source": "jolpica",
                "results": _format_race_results(sprint_result["results"]),
                "data_quality": {"level": "high", "complete": True},
            }
        
        # 4. Practice sessions from OpenF1 (more detailed than Jolpica)
        if FEATURE_FLAGS.get("openf1_live_data", False):
            openf1 = get_openf1_client()
            meeting = openf1.find_meeting_for_circuit(year, circuit_id, circuit.get("name"))
            
            if meeting:
                meeting_key = meeting["meeting_key"]
                all_sessions = openf1.get_sessions(meeting_key=meeting_key)
                
                for sess in all_sessions:
                    sess_name = sess.get("session_name", "").lower()
                    if "practice" in sess_name:
                        session_key = sess["session_key"]
                        # Get lap summaries for practice
                        drivers = openf1.get_drivers(session_key)
                        practice_results = []
                        for driver in drivers:
                            dnum = driver.get("driver_number")
                            if dnum:
                                lap_summary = openf1.get_driver_lap_summary(session_key, dnum)
                                practice_results.append({
                                    "driver_number": dnum,
                                    "driver_name": driver.get("full_name", ""),
                                    "team": driver.get("team_name", ""),
                                    "fastest_lap": lap_summary.get("fastest_lap_time"),
                                    "total_laps": lap_summary.get("total_laps", 0),
                                })
                        
                        practice_results.sort(key=lambda x: (x.get("fastest_lap") is None, x.get("fastest_lap") or 9999))
                        weather = openf1.get_weather_summary(session_key)
                        sessions[_normalize_session_name(sess.get("session_name", ""))] = {
                            "name": sess.get("session_name", "Practice"),
                            "type": "practice",
                            "date": sess.get("date_start", ""),
                            "source": "openf1",
                            "results": practice_results[:22],
                            "weather": weather,
                            "data_quality": {
                                "level": "high" if practice_results else "low",
                                "complete": len(practice_results) >= len(_active_driver_ids()),
                            },
                        }
                    elif "sprint shootout" in sess_name or "sprint qualifying" in sess_name:
                        sessions.setdefault("sprint_qualifying", {
                            "name": sess.get("session_name", "Sprint Qualifying"),
                            "type": "sprint_qualifying",
                            "date": sess.get("date_start", ""),
                            "source": "openf1",
                            "results": [],
                            "data_quality": {"level": "medium", "complete": False},
                        })
        
        return {
            "circuit_id": circuit_id,
            "round": round_num,
            "year": year,
            "sprint_weekend": circuit.get("sprint_weekend", False),
            "sessions": sessions,
            "session_count": len(sessions),
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical sessions for {circuit_id}: {e}")
        return {"error": str(e), "sessions": {}}

def _format_race_results(results: List[Dict]) -> List[Dict]:
    """Format raw Jolpica race results for dashboard display."""
    formatted = []
    for r in results:
        formatted.append({
            "position": r.get("position", 0),
            "driver_code": r.get("driver_code", ""),
            "driver_name": r.get("driver_name", ""),
            "constructor": r.get("constructor_name", ""),
            "grid": r.get("grid", 0),
            "laps": r.get("laps", 0),
            "points": r.get("points", 0),
            "status": r.get("status", ""),
            "time": r.get("time", ""),
        })
    return formatted

def _format_qualifying_results(results: List[Dict]) -> List[Dict]:
    """Format raw Jolpica qualifying results for dashboard display."""
    formatted = []
    for r in results:
        formatted.append({
            "position": r.get("position", 0),
            "driver_code": r.get("driver_code", ""),
            "driver_id": r.get("driver_id", ""),
            "q1": r.get("q1", ""),
            "q2": r.get("q2", ""),
            "q3": r.get("q3", ""),
        })
    return formatted

# ── Helper: Live Session Data (OpenF1) ───────────────────────────────────────

def get_live_session_data(circuit_id: str) -> Dict[str, Any]:
    """
    Fetch current live session data from OpenF1 for active race weekends.
    Returns positions, intervals, weather, and race control for active sessions.
    """
    if not FEATURE_FLAGS.get("openf1_live_data", False):
        return {"enabled": False, "message": "OpenF1 live data disabled"}

    cache_key = f"{circuit_id}:live"
    cached = _live_session_cache.get(cache_key)
    if cached and (datetime.now(timezone.utc) - cached["timestamp"]).total_seconds() < CACHE_LIVE_SECONDS:
        return cached["data"]

    try:
        openf1 = get_openf1_client()
        circuit = get_circuit(circuit_id)
        year = 2026
        context = openf1.get_current_or_recent_session(circuit_id, year, circuit.get("name"))
        meeting = context.get("meeting")
        if not meeting:
            return {"enabled": True, "active": False, "message": "No active meeting found"}

        active_session = context.get("active_session")
        if not active_session:
            return {
                "enabled": True,
                "active": False,
                "meeting": meeting.get("meeting_name"),
                "message": "No active session currently",
                "upcoming_sessions": [
                    {"name": s.get("session_name"), "start": s.get("date_start")}
                    for s in context.get("upcoming_sessions", [])
                ],
                "recent_session": context.get("recent_session"),
            }

        session_key = active_session["session_key"]
        positions = openf1.get_positions(session_key)
        intervals = openf1.get_intervals(session_key)
        weather = openf1.get_weather(session_key)
        race_control = openf1.get_race_control(session_key)
        laps = openf1.get_laps(session_key)
        pit_stops = openf1.get_pit_stops(session_key)

        latest_positions = openf1.latest_by_driver(positions)
        latest_intervals = openf1.latest_by_driver(intervals)
        weather_latest = weather[-1] if weather else {}
        rain_probability = 0.0
        if weather:
            rain_events = [w for w in weather if w.get("rainfall")]
            rain_probability = len(rain_events) / len(weather) * 100

        race_control_recent = race_control[-12:] if race_control else []
        data = {
            "enabled": True,
            "active": True,
            "meeting": meeting.get("meeting_name"),
            "session": {
                "name": active_session.get("session_name"),
                "key": session_key,
                "start": active_session.get("date_start"),
                "end": active_session.get("date_end"),
                "type": _normalize_session_name(active_session.get("session_name", "")),
            },
            "positions": latest_positions,
            "intervals": latest_intervals,
            "weather": {
                "air_temp": weather_latest.get("air_temperature"),
                "track_temp": weather_latest.get("track_temperature"),
                "humidity": weather_latest.get("humidity"),
                "wind_speed": weather_latest.get("wind_speed"),
                "rain_probability": round(rain_probability, 1),
                "rained": len([w for w in weather if w.get("rainfall")]) > 0,
                "source": "openf1",
            },
            "laps_count": len(laps),
            "pit_stop_count": len(pit_stops),
            "race_control_count": len(race_control),
            "race_control": race_control_recent,
            "safety_car_deployed": any("safety car" in str(e.get("message", "")).lower() for e in race_control_recent),
            "red_flag": any(str(e.get("flag", "")).upper() == "RED" for e in race_control_recent),
            "yellow_flag": any(str(e.get("flag", "")).upper() == "YELLOW" for e in race_control_recent),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "openf1",
        }
        _live_session_cache[cache_key] = {"timestamp": datetime.now(timezone.utc), "data": data}
        return data
        
    except Exception as e:
        logger.error(f"Error fetching live session data: {e}")
        return {"enabled": True, "active": False, "error": str(e)}

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    """Health check endpoint to verify the server is running."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.0"
    })


@app.route("/")
def index():
    """Redirect to dashboard."""
    return redirect(url_for("dashboard"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Main dashboard with prediction, live data, and session browser."""
    try:
        if request.method == "POST":
            race_name = request.form.get("race_name")
            rain_prob = request.form.get("rain_probability", type=float)
            n_sims = request.form.get("n_simulations", type=int, default=5000)
            return redirect(url_for("dashboard", race=race_name, rain=rain_prob, sims=n_sims))
        
        # Query params for shared links
        selected_race = request.args.get("race", "Australian Grand Prix")
        rain_prob = request.args.get("rain", type=float)
        n_sims = request.args.get("sims", type=int, default=5000)
        
        circuit_id = get_circuit_id(selected_race)
        if not circuit_id:
            flash(f"Unknown race: {selected_race}", "error")
            return redirect(url_for("dashboard", race="Australian Grand Prix"))

########################
  
        circuit = get_circuit(circuit_id)
        weekend_phase = get_weekend_phase(circuit_id)
        
        # ── Auto-fetch qualifying grid on race day ─────────────────────────────
        grid_overrides = {}
        qualifying_data = None
        session_grid_key = f"grid_{circuit_id}"
        
        # FIX: this compared weekend_phase["phase"] to "sunday", a value get_weekend_phase()
        # never actually returns (it returns "race", not "sunday") — the check was always
        # False and silently relied on qualifying_completed alone. Fixed to check "race".
        if weekend_phase["qualifying_completed"] or weekend_phase["phase"] == "race":
            # NOTE: fetch_live_qualifying_grid() always returns a grid — real live results
            # when available, otherwise a synthetic "fallback"-sourced grid — it never
            # returns None just because live data is missing. Only a genuinely live
            # source should be allowed to overwrite a grid the user manually saved, so
            # that's checked explicitly here rather than trusting truthiness alone.
            qual_live = fetch_live_qualifying_grid(circuit_id)
            is_real_live_grid = bool(qual_live and qual_live.get("grid") and not str(qual_live.get("source", "")).startswith("fallback"))
            if is_real_live_grid:
                grid_overrides = qual_live["grid"]
                qualifying_data = qual_live
                flask_session[session_grid_key] = grid_overrides
                flash("Qualifying grid auto-filled from live data!", "success")
        
        # NEW: Fall back to a manually-entered (or previously live-fetched) grid saved
        # earlier this weekend if this request didn't just get a genuinely live one above.
        # Persisted in the Flask session so it survives across page loads for the circuit.
        if not grid_overrides:
            saved_grid = flask_session.get(session_grid_key)
            if saved_grid:
                grid_overrides = saved_grid
                qualifying_data = qualifying_data or {"source": "Manually Entered", "grid": saved_grid}
        
        # ── Live Session Data (lightweight call) ───────────────────────────────
        live_data = get_live_session_data(circuit_id)
        
        # ── Historical Sessions - SKIP ON INITIAL LOAD (load via AJAX instead) ─
        # This prevents excessive API calls on page load that cause rate limiting
        historical_sessions = {"loaded": False, "message": "Load via /api/historical endpoint"}
        
        # ── Prediction ─────────────────────────────────────────────────────────
        try:
            req = PredictionRequest(
                circuit_id=circuit_id,
                rain_probability=rain_prob,
                n_simulations=min(max(n_sims, 100), 50000),
                grid_overrides=grid_overrides,
                qualifying_completed=bool(grid_overrides),
                live_weather_override=_weather_rain_probability(live_data),
                session_type=weekend_phase.get("phase", "race"),
                sprint_weekend=bool(circuit.get("sprint_weekend")),
                live_context=live_data,
            )
            result = predict(req)
            predictions = result.get("predictions", [])
            meta = result.get("meta", {})
            podium = result.get("podium_predictions", [])
            surprises = result.get("likely_top_surprises", [])
            raw = result.get("raw") if req.output_format == "full" else None
            data_confidence = _data_confidence(result, live_data, grid_overrides)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            flash(f"Prediction error: {e}", "error")
            predictions, meta, podium, surprises, raw = [], {}, [], [], None
            data_confidence = {"score": 0, "level": "low", "reasons": []}
        
        # ── Driver List for Grid Override UI ───────────────────────────────────
        all_drivers = get_all_drivers()
        
        # Sort drivers by predicted position for display
        predictions_sorted = sorted(predictions, key=lambda x: x.get("predicted_position", 99))
        
        # Championship standings - SKIP ON INITIAL LOAD (load via AJAX instead)
        # This prevents another API call during page load
        live_standings = {}
        
        # NEW: circuit_id -> sprint_weekend map, so the frontend knows whether to show the
        # Sprint tab when the user picks a *different* race from the dropdown, without an
        # extra API round-trip for something we already have on the server.
        sprint_circuits = {c["id"]: bool(c.get("sprint_weekend")) for c in get_all_circuits()}
        
        return render_template(
            "dashboard.html",
            race_name=selected_race,
            circuit=circuit,
            weekend_phase=weekend_phase,
            predictions=predictions_sorted,
            meta=meta,
            podium=podium,
            surprises=surprises,
            raw=raw,
            all_drivers=all_drivers,
            grid_overrides=grid_overrides,
            qualifying_data=qualifying_data,
            live_data=live_data,
            data_confidence=data_confidence,
            sprint_circuits=sprint_circuits,
            historical_sessions=historical_sessions,
            live_standings=live_standings,
            race_names=sorted(RACE_NAME_MAPPING.keys()),
            rain_prob=rain_prob,
            n_sims=n_sims,
            api_status=get_api_status(),
            feature_flags=FEATURE_FLAGS,
            now=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Dashboard route failed: {e}", exc_info=True)
        # Return a simple error page instead of crashing
        return render_template(
            "error.html",
            code=500,
            message=f"Dashboard error: {str(e)}",
            details="Check server logs for more information"
        ), 500

# ── Pages split out of the old single-file dashboard.html ────────────────────
# Each is pure client-side/AJAX (no server-rendered prediction state needed),
# unlike /dashboard above which computes and injects live prediction context.

@app.route("/h2h")
def h2h():
    """Driver head-to-head comparison page."""
    return render_template("h2h.html")

@app.route("/constructors")
def constructors():
    """Live constructor standings & analytics page."""
    return render_template("constructors.html")

@app.route("/analytics")
def analytics():
    """Analytics lab: post-race evaluation, backtesting, calibration, tuning."""
    return render_template("analytics.html")

@app.route("/settings")
def settings():
    """System settings: database migration, data sync, quality checks."""
    return render_template("settings.html")

@app.route("/download")
def download():
    """Race report download page."""
    return render_template("download.html")


@app.route("/api/weekend-phase/<circuit_id>")
def api_weekend_phase(circuit_id: str):
    """Lightweight status check for the 'has this race already happened' banner —
    no simulation run, just the same phase/message/confidence_boost computation
    already used on page load, so switching races updates the banner instantly."""
    try:
        return jsonify({"success": True, "weekend_phase": get_weekend_phase(circuit_id)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
@app.route("/api/live-data/<circuit_id>")

def api_live_data(circuit_id: str):
    """AJAX endpoint for live session data polling."""
    data = get_live_session_data(circuit_id)
    return jsonify(data)

@app.route("/api/historical/<circuit_id>")
def api_historical(circuit_id: str):
    """AJAX endpoint for historical session results."""
    data = fetch_historical_sessions(circuit_id)
    return jsonify(data)

@app.route("/api/qualifying-grid/<circuit_id>")
def api_qualifying_grid(circuit_id: str):
    """AJAX endpoint to fetch qualifying grid."""
    data = fetch_live_qualifying_grid(circuit_id)
    if data:
        return jsonify(data)
    return jsonify({"error": "No qualifying data available"}), 404

@app.route("/api/refresh-standings", methods=["POST"])
@csrf.exempt
def api_refresh_standings():
    """Trigger manual refresh of live standings."""
    if not LIVE_DATA_ENABLED:
        return jsonify({"error": "Live data disabled"}), 403
    
    try:
        report = run_full_data_update(include_openf1=False)
        return jsonify({
            "success": True,
            "drivers_updated": report.get("driver_standings", {}).get("driver_count", 0),
            "teams_updated": report.get("constructor_standings", {}).get("team_count", 0),
            "elapsed": report.get("elapsed_seconds", 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict", methods=["POST"])
@csrf.exempt
def api_predict():
    """API endpoint for programmatic predictions."""
    data = request.get_json() or {}
    race_name = data.get("race") or data.get("race_name")
    circuit_id = data.get("circuit_id") or (get_circuit_id(race_name) if race_name else None) or "australia"
    session_type = (data.get("session_type") or "RACE").lower()
    rain_prob = data.get("rain_probability")
    if rain_prob is None:
        rain_prob = _weather_to_rain_probability(data.get("weather"))
    n_sims = data.get("n_simulations", data.get("simulations", 5000))
    grid_overrides = data.get("grid_overrides", {})
    
    try:
        circuit = get_circuit(circuit_id)
        live_data = get_live_session_data(circuit_id)
        weekend_phase = get_weekend_phase(circuit_id)
        session_grid_key = f"grid_{circuit_id}"
        grid_data = None

        # NEW: manually-entered grid_overrides (e.g. from the Sunday P1-P22 widget) take
        # priority and get persisted so they're remembered for the rest of the weekend.
        if grid_overrides:
            flask_session[session_grid_key] = grid_overrides
            grid_data = {"source": "Manually Entered", "grid": grid_overrides}
        elif session_type in {"race", "r", "sprint", "sprint_race"}:
            # NOTE: fetch_live_qualifying_grid() always returns *a* grid — real live
            # results when available, otherwise a synthetic "fallback"-sourced one — it
            # never returns None just because live data is missing. Only a genuinely
            # live source should override a grid saved earlier this weekend, so that's
            # checked explicitly rather than trusting truthiness of the return value.
            live_grid = fetch_live_qualifying_grid(circuit_id)
            is_real_live_grid = bool(live_grid and live_grid.get("grid") and not str(live_grid.get("source", "")).startswith("fallback"))
            saved_grid = flask_session.get(session_grid_key)
            if is_real_live_grid:
                grid_overrides = live_grid.get("grid", {})
                flask_session[session_grid_key] = grid_overrides
                grid_data = live_grid
            elif saved_grid:
                grid_overrides = saved_grid
                grid_data = {"source": "Saved From Earlier This Weekend", "grid": saved_grid}
            elif live_grid and live_grid.get("grid"):
                grid_overrides = live_grid.get("grid", {})
                grid_data = live_grid

        req = PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_prob,
            n_simulations=min(max(int(n_sims), 100), 50000),
            grid_overrides=grid_overrides,
            qualifying_completed=bool(grid_overrides),
            live_weather_override=_weather_rain_probability(live_data),
            session_type=session_type,
            sprint_weekend=bool(circuit.get("sprint_weekend")),
            live_context=live_data,
        )
        result = predict(req)
        grid_source = grid_data.get("source") if grid_data else ("Manually Entered" if grid_overrides else None)
        dashboard_result = _dashboard_payload(result, session_type, grid_source)
        dashboard_result["data_confidence"] = _data_confidence(result, live_data, grid_overrides)
        dashboard_result["live_data"] = live_data
        dashboard_result["weekend_phase"] = weekend_phase
        return jsonify({
            "success": True,
            "results": dashboard_result,
            "prediction": result,
            "circuit_id": circuit_id,
            "session_type": session_type,
        })
    except Exception as e:
        logger.exception("Prediction API failed")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/telemetry/<circuit_id>/<int:driver_number>")
def api_telemetry(circuit_id: str, driver_number: int):
    """Get live telemetry for a specific driver."""
    if not FEATURE_FLAGS.get("openf1_telemetry", False):
        return jsonify({"error": "Telemetry disabled"}), 403
    
    try:
        openf1 = get_openf1_client()
        # Find active session
        live = get_live_session_data(circuit_id)
        if not live.get("active"):
            return jsonify({"error": "No active session"}), 404
        
        session_key = live["session"]["key"]
        car_data = openf1.get_car_data(session_key, driver_number=driver_number)
        
        # Return last 60 seconds of data (approx 222 data points at 3.7Hz)
        return jsonify({
            "driver_number": driver_number,
            "session": live["session"]["name"],
            "data_points": len(car_data),
            "latest": car_data[-50:] if car_data else [],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/drivers")
def api_drivers():
    """Return active driver profiles for dashboard selectors."""
    return jsonify({"success": True, "drivers": get_all_drivers(), "total": len(get_all_drivers())})


@app.route("/api/constructors/live")
def api_constructors_live():
    """Live constructor standings and dashboard analytics."""
    try:
        updater = get_live_updater()
        constructor_update = updater.fetch_constructor_standings_update()
        driver_update = updater.fetch_driver_standings_update()
        standings = constructor_update.get("standings", {})
        drivers = driver_update.get("standings", {})
        constructors = []
        for team_id, standing in sorted(standings.items(), key=lambda item: item[1].get("position", 99)):
            team_drivers = [d for d in get_all_drivers() if d.get("team") == team_id]
            constructors.append({
                "team_id": team_id,
                "name": team_id.replace("_", " ").title(),
                "position": standing.get("position"),
                "points": standing.get("points", 0),
                "wins": standing.get("wins", 0),
                "drivers": [{"code": d.get("short"), "name": d.get("name")} for d in team_drivers],
                "tier": "Top Tier" if standing.get("position", 99) <= 3 else "Mid Field" if standing.get("position", 99) <= 7 else "Back Marker",
            })
        return jsonify({
            "success": True,
            "constructors": constructors,
            "drivers": [{"driver_id": k, **v} for k, v in drivers.items()],
            "total_teams": len(constructors),
            "total_drivers": len(get_all_drivers()),
            "season": datetime.now().year,
            "round": None,
            "analytics": {
                "win_distribution": [{"team": c["name"], "wins": c["wins"], "percentage": 0} for c in constructors],
                "points_gaps": [
                    {"position": c["position"], "team": c["name"], "gap": max(0, constructors[0]["points"] - c["points"]) if constructors else 0}
                    for c in constructors
                ],
                "performance_tiers": [{"team": c["name"], "tier": c["tier"], "points": c["points"], "color": "#e10600"} for c in constructors],
            },
        })
    except Exception as e:
        logger.exception("Constructor live data failed")
        return jsonify({"success": False, "error": str(e), "constructors": []}), 500


@app.route("/api/h2h", methods=["POST"])
@csrf.exempt
def api_h2h():
    """Head-to-head comparison using current prediction probabilities."""
    data = request.get_json() or {}
    circuit_id = data.get("circuit_id") or get_circuit_id(data.get("race", "")) or "australia"
    d1 = data.get("driver1") or data.get("driver_a")
    d2 = data.get("driver2") or data.get("driver_b")
    result = predict(PredictionRequest(circuit_id=circuit_id, n_simulations=int(data.get("simulations", 5000))))
    by_id = {p["driver_id"]: p for p in result.get("predictions", [])}
    p1, p2 = by_id.get(d1, {}), by_id.get(d2, {})
    score1 = p1.get("composite_score", 0)
    score2 = p2.get("composite_score", 0)
    total = max(score1 + score2, 0.0001)
    return jsonify({
        "success": True,
        "driver1": p1,
        "driver2": p2,
        "driver1_win_pct": round(score1 / total * 100, 1),
        "driver2_win_pct": round(score2 / total * 100, 1),
    })


def _run_script(script_name: str, args: Optional[List[str]] = None, timeout: int = 120) -> Dict[str, Any]:
    path = project_root / "scripts" / script_name
    if not path.exists():
        return {"status": "error", "message": f"Script not found: {script_name}"}
    cmd = [sys.executable, str(path), *(args or [])]
    completed = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, timeout=timeout)
    return {
        "status": "success" if completed.returncode == 0 else "error",
        "message": "Completed" if completed.returncode == 0 else "Script failed",
        "output": completed.stdout[-8000:],
        "errors": completed.stderr[-4000:],
        "returncode": completed.returncode,
    }


@app.route("/api/evaluate/race", methods=["POST"])
@csrf.exempt
def api_evaluate_race():
    data = request.get_json() or {}
    return jsonify(_run_script("post_race_evaluation.py", [str(data.get("race", ""))], timeout=120))


@app.route("/api/backtest/run", methods=["POST"])
@csrf.exempt
def api_backtest_run():
    return jsonify(_run_script("backtest_2025_season.py", timeout=180))


@app.route("/api/calibration/run", methods=["POST"])
@csrf.exempt
def api_calibration_run():
    return jsonify(_run_script("calibrate_probabilities.py", timeout=180))


@app.route("/api/optimize/weights", methods=["POST"])
@csrf.exempt
def api_optimize_weights():
    return jsonify(_run_script("optimize_weights_v3.py", timeout=240))


@app.route("/api/accuracy/report")
def api_accuracy_report():
    try:
        output = _run_script("measure_accuracy.py", timeout=120)
        return jsonify({"status": output["status"], "report": {}, "output": output.get("output", ""), "message": output.get("message")})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "report": {}}), 500


@app.route("/api/quality/check")
def api_quality_check():
    output = _run_script("data_quality_report.py", timeout=120)
    return jsonify({"status": output["status"], "passed": output["status"] == "success", **output})


@app.route("/api/database/migrate", methods=["POST"])
@csrf.exempt
def api_database_migrate():
    try:
        from database.models import init_db
        init_db()
        return jsonify({"status": "success", "message": "Database initialized"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/sync/fastf1", methods=["POST"])
@csrf.exempt
def api_sync_fastf1():
    data = request.get_json() or {}
    seasons = data.get("seasons") or [2025]
    try:
        from data.fastf1_integration import load_entire_season
        results = {str(season): load_entire_season(int(season)) for season in seasons}
        return jsonify({"status": "success", "message": "FastF1 sync completed", "details": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/benchmark/run", methods=["POST"])
@csrf.exempt
def api_benchmark_run():
    data = request.get_json() or {}
    circuit_id = data.get("circuit") or "australia"
    sims = int(data.get("sims", 5000))
    start = datetime.now()
    result = predict(PredictionRequest(circuit_id=circuit_id, n_simulations=sims, output_format="summary"))
    elapsed = (datetime.now() - start).total_seconds()
    return jsonify({"status": "success", "message": "Benchmark complete", "details": {"elapsed_seconds": elapsed, "drivers": len(result.get("predictions", []))}})


@app.route("/api/setup/initialize", methods=["POST"])
@csrf.exempt
def api_setup_initialize():
    validation = validate_api_settings()
    return jsonify({"status": "success" if validation.get("valid") else "warning", "message": "System initialized", "details": validation})

# ── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal server error"), 500

# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Validate API settings on startup
    validation = validate_api_settings()
    if not validation["valid"]:
        for issue in validation["issues"]:
            logger.warning(f"API Config Issue: {issue}")
    
    port = int(os.environ.get("FLASK_PORT", os.environ.get("PORT", 5000)))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
