"""
Feature Engineering Pipeline — v3.2 (SOTA Upgrade).

SOTA Enhancements:
  1. Lag features: last 3/5 race rolling metrics, form trend
  2. Qualifying-to-race pace ratio
  3. DRS efficiency index
  4. Telemetry-derived long-run deltas
  5. Pit strategy features (team tire strategy score)
  6. Ensemble prediction integration hooks
  7. All features now include SOTA feature set for ML training
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Persistent disk-cache directory for API responses
_DISK_CACHE_DIR = Path(__file__).resolve().parents[1] / "cache" / "api_responses"

from config.settings import (
    CONSTRUCTOR_STRENGTH, FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW,
    LIVE_DATA_ENABLED, LIVE_OPENF1_ENABLED,
)
from data.driver_data import get_driver, get_all_drivers, get_drivers_for_team, calculate_circuit_performance_modifier
from data.circuit_data import get_circuit, circuit_favors_team
from data.calendar_2026 import get_race_by_circuit
from data.season_2026 import get_driver_last_n_results, DRIVER_STANDINGS_AFTER_R5

N_DRIVERS = 22
DNF_POSITION_PENALTY = N_DRIVERS + 5  # 27 — beyond last-place finish

# ── Live Data Cache ────────────────────────────────────────────────────────────
# Caches live API data in memory to avoid repeated API calls during a prediction run.
# Populated lazily on first access; cleared between prediction runs.
_LIVE_DATA_CACHE: Dict[str, Any] = {
    "driver_standings": None,
    "constructor_standings": None,
    "recent_results": None,
    "initialized": False,
}


def _ensure_live_data():
    """
    Lazily fetch live data from Jolpica API on first access.
    
    Populates the in-memory cache with:
    - Driver standings (position, points, wins)
    - Constructor standings (position, points, wins)
    - Recent race results (driver form, DNF rates)
    
    Falls back gracefully if the API is unavailable.
    """
    if _LIVE_DATA_CACHE["initialized"]:
        return

    if not LIVE_DATA_ENABLED:
        _LIVE_DATA_CACHE["initialized"] = True
        return

    try:
        from data.jolpica_client import get_jolpica_client
        client = get_jolpica_client()

        # Fetch driver standings
        standings = client.get_standings_mapped()
        if standings:
            _LIVE_DATA_CACHE["driver_standings"] = standings
            logger.info(f"Live data: loaded {len(standings)} driver standings from Jolpica")

        # Fetch constructor standings
        constructor = client.get_constructor_standings_mapped()
        if constructor:
            _LIVE_DATA_CACHE["constructor_standings"] = constructor
            logger.info(f"Live data: loaded {len(constructor)} constructor standings from Jolpica")

        # Fetch recent results for form/DNF
        schedule = client.get_current_schedule()
        if schedule:
            from datetime import datetime
            today = datetime.now().date()
            completed = []
            for race in schedule:
                try:
                    race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                    if race_date <= today:
                        completed.append(race)
                except (ValueError, KeyError):
                    continue

            # Get last 6 races for form calculation
            recent = completed[-6:] if len(completed) >= 6 else completed
            driver_form = {}
            driver_starts = {}
            driver_dnfs = {}

            for race in recent:
                try:
                    season = datetime.strptime(race["date"], "%Y-%m-%d").year
                except ValueError:
                    season = datetime.now().year
                result = client.get_race_results(season, race["round"])
                if result and result.get("results"):
                    # Map Ergast codes to our IDs
                    from data.live_updater import _ERGAST_CODE_TO_OUR_ID
                    for r in result["results"]:
                        code = r.get("driver_code", "")
                        our_id = _ERGAST_CODE_TO_OUR_ID.get(code, code.lower())
                        pos = r.get("position", 0)
                        status = r.get("status", "")

                        if pos > 0:
                            driver_form.setdefault(our_id, []).append(pos)
                        driver_starts[our_id] = driver_starts.get(our_id, 0) + 1
                        if "finished" not in status.lower() and pos == 0:
                            driver_dnfs[our_id] = driver_dnfs.get(our_id, 0) + 1

            _LIVE_DATA_CACHE["recent_results"] = {
                "driver_form": {k: v[-6:] for k, v in driver_form.items()},
                "driver_dnf": {
                    did: {"dnf_rate": round(dnfs / driver_starts[did], 3) if driver_starts[did] > 0 else 0.0}
                    for did, dnfs in driver_dnfs.items()
                },
            }
            logger.info(f"Live data: loaded form for {len(driver_form)} drivers from {len(recent)} races")

    except Exception as e:
        logger.warning(f"Live data fetch failed (falling back to hardcoded data): {e}")

    _LIVE_DATA_CACHE["initialized"] = True


def get_live_driver_standings() -> Optional[Dict[str, Dict]]:
    """Get live driver standings, or None if unavailable."""
    _ensure_live_data()
    return _LIVE_DATA_CACHE.get("driver_standings")


def get_live_constructor_standings() -> Optional[Dict[str, Dict]]:
    """Get live constructor standings, or None if unavailable."""
    _ensure_live_data()
    return _LIVE_DATA_CACHE.get("constructor_standings")


def get_live_recent_results() -> Optional[Dict[str, Any]]:
    """Get live recent results (form + DNF), or None if unavailable."""
    _ensure_live_data()
    return _LIVE_DATA_CACHE.get("recent_results")


def clear_live_data_cache():
    """Clear the in-memory live data cache (forces re-fetch on next access)."""
    _LIVE_DATA_CACHE.update({
        "driver_standings": None,
        "constructor_standings": None,
        "recent_results": None,
        "initialized": False,
    })


# ── ELO ────────────────────────────────────────────────────────────────────────

def _elo_confidence_weight(experience_races: int) -> float:
    """
    Dampen ELO influence for inexperienced drivers.
    
    Rookies and drivers with few races have higher uncertainty in their ELO ratings.
    This function returns a confidence weight that blends the normalized ELO toward
    0.5 (neutral) for drivers with limited experience.
    
    Args:
        experience_races: Number of races the driver has completed
        
    Returns:
        Confidence weight in [0, 1], reaching 1.0 after 30 races
    """
    return min(1.0, experience_races / 30.0)


def compute_elo_score(driver_id: str) -> float:
    """
    Compute normalized ELO score for a driver.
    
    FEATURE-9: Now uses multi-dimensional ELO system with race ELO as primary metric.
    Falls back to basic ELO from driver data if multi-dimensional system unavailable.
    
    IMPROVEMENT 3.4: ELO scores are now dampened toward 0.5 for inexperienced
    drivers (experience_races < 30) to reflect higher uncertainty.
    
    BUG FIX: Normalizes ELO within the ELO system's own rating population to avoid
    cross-contamination between MultiDimensionalELO and DRIVERS dict scales.
    """
    try:
        # Try to use multi-dimensional ELO system first (FEATURE-9)
        try:
            from engine.multi_dimensional_elo import get_elo_system
            elo_system = get_elo_system()
            # Get raw rating from the ELO system itself
            raw_elo = elo_system.drivers.get(driver_id, {}).get("race", {}).get("rating", 1500.0)
            
            # Normalize within the ELO system's own rating population
            all_race_ratings = [
                data.get("race", {}).get("rating", 1500.0)
                for data in elo_system.drivers.values()
            ]
            lo, hi = min(all_race_ratings), max(all_race_ratings)
            normalized_elo = (raw_elo - lo) / (hi - lo + 1e-9)
        except ImportError:
            logger.debug("Multi-dimensional ELO not available, using basic ELO")
            # Fallback to basic ELO from driver data
            field = get_all_drivers()
            lo, hi = min(d["elo"] for d in field), max(d["elo"] for d in field)
            raw_elo = get_driver(driver_id)["elo"]
            normalized_elo = (raw_elo - lo) / (hi - lo + 1e-9)
        
        # Apply confidence weighting for inexperienced drivers
        driver = get_driver(driver_id)
        experience = driver.get("experience_races", 0)
        confidence = _elo_confidence_weight(experience)
        
        # Blend toward 0.5 (neutral) based on confidence
        # Low confidence → score closer to 0.5, high confidence → use normalized ELO
        return 0.5 * (1 - confidence) + normalized_elo * confidence
        
    except Exception:
        return 0.5


# ── Constructor strength ───────────────────────────────────────────────────────

def get_dynamic_constructor_strength() -> Dict[str, float]:
    """A-3 FIX: Blend static pre-season estimates with actual 2026 constructor points.
    
    Blends 40% static (pre-season expertise) + 60% actual results.
    Normalizes 2026 points to [0.10, 0.96] range.
    
    LIVE DATA (v3.1): When live constructor standings are available from Jolpica,
    uses those instead of hardcoded CONSTRUCTOR_STANDINGS_AFTER_R5.
    """
    # Try live data first
    live_constructors = get_live_constructor_standings()
    if live_constructors:
        try:
            max_pts = max(v["points"] for v in live_constructors.values() if v["points"] > 0)
            if max_pts > 0:
                points_strength = {}
                for team, data in live_constructors.items():
                    if data["points"] > 0:
                        points_strength[team] = 0.10 + (data["points"] / max_pts) * 0.86
                    else:
                        points_strength[team] = 0.10

                blended = {}
                for team, static_val in CONSTRUCTOR_STRENGTH.items():
                    actual_val = points_strength.get(team, static_val)
                    blended[team] = round(0.40 * static_val + 0.60 * actual_val, 3)
                return blended
        except Exception as e:
            logger.debug(f"Live constructor strength failed, falling back: {e}")

    # Fallback to hardcoded data
    try:
        from data.season_2026 import CONSTRUCTOR_STANDINGS_AFTER_R5
        
        # Normalize 2026 points to [0.10, 0.96] range
        max_pts = max(s['points'] for s in CONSTRUCTOR_STANDINGS_AFTER_R5)
        if max_pts <= 0:
            return dict(CONSTRUCTOR_STRENGTH)
        
        points_strength = {
            s['team']: 0.10 + (s['points'] / max_pts) * 0.86
            for s in CONSTRUCTOR_STANDINGS_AFTER_R5
        }
        
        # Blend: 40% static (pre-season expertise) + 60% actual results
        blended = {}
        for team, static_val in CONSTRUCTOR_STRENGTH.items():
            actual_val = points_strength.get(team, static_val)
            blended[team] = round(0.40 * static_val + 0.60 * actual_val, 3)
        
        return blended
    except Exception:
        return dict(CONSTRUCTOR_STRENGTH)


def compute_constructor_strength(team_id: str, circuit_id: str) -> float:
    # A-3 FIX: Use dynamic constructor strength blended with actual 2026 results
    dynamic_strength = get_dynamic_constructor_strength()
    base = dynamic_strength.get(team_id, CONSTRUCTOR_STRENGTH.get(team_id, 0.25))
    try:
        mult = circuit_favors_team(circuit_id, team_id)
    except Exception:
        mult = 1.0
    return min(1.0, max(0.05, base * mult))


# ── Recent form ────────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str) -> float:
    """Exponentially-weighted average of last N finishing positions.
    
    C-4 FIX: get_driver_last_n_results now returns List[dict] with {position, status}.
    DNF/DNS/DSQ drivers are correctly identified via status field, not just position.
    A-4 FIX: Filter out DNS padding — only use actual race results.
    
    LIVE DATA (v3.1): When live data is available, uses actual recent race results
    from Jolpica API instead of hardcoded season_2026.py data.
    """
    # Try live data first
    live_results = get_live_recent_results()
    if live_results and live_results.get("driver_form", {}).get(driver_id):
        form_positions = live_results["driver_form"][driver_id]
        if form_positions:
            def pos_to_score_live(pos):
                if pos <= 0:
                    return 0.02
                return max(0.05, 1.0 - (pos - 1) / (N_DRIVERS - 1))

            weighted_sum = 0.0
            weight_total = 0.0
            for i, pos in enumerate(form_positions):
                weight = RECENCY_DECAY ** i
                score = pos_to_score_live(pos)
                weighted_sum += weight * score
                weight_total += weight

            if weight_total > 0:
                return weighted_sum / weight_total

    # Fallback to hardcoded data
    try:
        results = get_driver_last_n_results(driver_id, n=RECENCY_WINDOW)
        
        # A-4 FIX: Filter out DNS padding (no data yet) — only use actual results
        actual_results = [
            r for r in results
            if r.get("status", "Finished") not in ("DNS",) or r.get("position", 0) > 0
        ]
        if not actual_results:
            return 0.5  # Neutral for no data
        
        # C-4 FIX: pos_to_score now uses status field to detect DNF/DNS/DSQ
        def pos_to_score(result_dict):
            pos = result_dict.get("position", 0)
            status = result_dict.get("status", "Finished")
            # C-4 FIX: DNF/DNS/DSQ are identified by status, not just position <= 0
            if status in ("DNF", "DNS", "DSQ") or pos <= 0:
                return 0.02  # Heavy penalty for non-finish
            return max(0.05, 1.0 - (pos - 1) / (N_DRIVERS - 1))
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for i, result in enumerate(actual_results):
            weight = RECENCY_DECAY ** i
            score = pos_to_score(result)
            weighted_sum += weight * score
            weight_total += weight
        
        return weighted_sum / weight_total if weight_total > 0 else 0.5
    except Exception:
        return 0.5


# ── Track type fit ─────────────────────────────────────────────────────────────

def compute_track_fit_score(driver_id: str, circuit_id: str) -> float:
    """Match driver's strengths to circuit characteristics.
    
    A-5 FIX: Include tire management bonus at high-degradation circuits.
    """
    try:
        driver = get_driver(driver_id)
        circuit = get_circuit(circuit_id)
        
        track_types = circuit.get("circuit_type", ["balanced"])
        fits = driver.get("track_type_fit", {})
        
        # Average fit across all circuit types
        total_fit = sum(fits.get(t, 1.0) for t in track_types)
        avg_fit = total_fit / len(track_types)
        
        # A-5 FIX: Tire management bonus at high-degradation circuits
        tire_deg_rate = circuit.get("tire_deg_rate", 0.6)
        if tire_deg_rate > 0.65:  # High-deg circuit
            tire_mgmt = driver.get("tire_management", 7.0) / 10.0
            tire_bonus = (tire_mgmt - 0.7) * (tire_deg_rate - 0.65) * 0.5
            avg_fit += tire_bonus
        
        # Normalize to 0-1 range (typical range is 0.8-1.2)
        return min(1.0, max(0.0, (avg_fit - 0.8) / 0.4))
    except Exception:
        return 0.5


# ── Reliability ────────────────────────────────────────────────────────────────

def compute_reliability_score(driver_id: str) -> float:
    """Inverse of DNF rate — blend of career and recent."""
    try:
        driver = get_driver(driver_id)
        career_dnf = driver.get("dnf_rate_career", 0.15)
        recent_dnf = driver.get("dnf_rate_recent", 0.15)
        
        # Weighted blend: 40% career, 60% recent
        blended_dnf = 0.4 * career_dnf + 0.6 * recent_dnf
        
        # Convert to reliability score (lower DNF = higher reliability)
        return max(0.0, min(1.0, 1.0 - blended_dnf))
    except Exception:
        return 0.5


# ── Weather adjustment ─────────────────────────────────────────────────────────

def compute_weather_score(driver_id: str, circuit_id: str, 
                         rain_probability: Optional[float] = None) -> float:
    """Wet skill × rain probability interaction.
    
    A-7 FIX: When rain_probability > 0.5, wet skill becomes the primary differentiator.
    """
    try:
        driver = get_driver(driver_id)
        wet_skill = driver.get("wet_skill", 5.0) / 10.0  # Normalize to 0-1
        
        rain_prob = rain_probability if rain_probability is not None else 0.2
        
        # A-7 FIX: Enhanced wet weather differentiation
        if rain_prob > 0.5:
            # Heavy rain: wet skill is the primary differentiator
            # Hamilton (9.0), Verstappen (9.2) vs Lindblad (6.8)
            return 0.3 + wet_skill * 0.7   # Range: [0.51, 0.93]
        elif rain_prob > 0.3:
            base_score = 0.5
            wet_bonus = (wet_skill - 0.5) * rain_prob * 0.8
            return max(0.0, min(1.0, base_score + wet_bonus))
        else:
            base_score = 0.5
            wet_bonus = (wet_skill - 0.5) * rain_prob * 0.6
            return max(0.0, min(1.0, base_score + wet_bonus))
    except Exception:
        return 0.5


# ── Safety car upside ──────────────────────────────────────────────────────────

def compute_safety_car_upside(driver_id: str, circuit_id: str, 
                             estimated_grid_pos: Optional[int] = None) -> float:
    """
    Drivers starting further back benefit more from safety cars.
    SC probability comes from circuit data.
    
    M-2 FIX: Widened range from [0, 0.8] to [0, 1.0] and removed the 0.8 scale factor
    that was making the max contribution only 0.05 × 0.36 = 0.018 (below float noise).
    """
    try:
        circuit = get_circuit(circuit_id)
        sc_prob = circuit.get("safety_car_probability", 0.5)
        
        # Use grid position if provided, otherwise estimate from championship
        if estimated_grid_pos is None:
            # Estimate from championship standings (higher points = better grid)
            driver = get_driver(driver_id)
            points = driver.get("championship_points_2026", 50)
            # Rough mapping: leader ~P2, backmarker ~P18
            estimated_grid_pos = max(1, min(20, 2 + int((100 - points) / 5)))
        
        # Upside increases with grid position (backmarkers gain more)
        # Formula: higher grid pos → more opportunity to gain positions
        grid_factor = (estimated_grid_pos - 1) / (N_DRIVERS - 1)  # 0 to 1
        
        # M-2 FIX: Combine with circuit SC probability — widened to full [0, 1.0] range
        # Removed the 0.8 scale factor that was compressing the signal
        upside = sc_prob * grid_factor
        
        return max(0.0, min(1.0, upside))
    except Exception:
        return 0.25


# ── Grid position score ────────────────────────────────────────────────────────

def compute_grid_position_score(driver_id: str, actual_grid_pos: Optional[int] = None) -> float:
    """
    Compute grid position score.
    
    If actual_grid_pos is provided (post-qualifying), use it directly.
    Otherwise, estimate from championship position and qualifying delta.
    
    FIX: v1 had this hardcoded to 0.5 — now properly computed.
    """
    try:
        if actual_grid_pos is not None:
            # Direct mapping: P1 = 1.0, P20 = 0.05
            return max(0.05, 1.0 - (actual_grid_pos - 1) / (N_DRIVERS - 1))
        
        # Pre-qualifying proxy: use championship position
        driver = get_driver(driver_id)
        points = driver.get("championship_points_2026", 50)
        
        # Championship leader gets good proxy position (~P2 after accounting for variance)
        # Backmarker gets poor position (~P18)
        estimated_pos = max(1, min(20, 2 + int((100 - points) / 5)))
        
        # Apply same mapping
        return max(0.05, 1.0 - (estimated_pos - 1) / (N_DRIVERS - 1))
    except Exception:
        return 0.5


# ── Teammate beat probability ──────────────────────────────────────────────────

def compute_teammate_beat_probability(driver_id: str) -> float:
    """
    Probability of beating teammate based on ELO difference and recent form.
    
    For teammates, returns complementary probabilities that sum to ~1.0.
    """
    try:
        driver = get_driver(driver_id)
        team = driver.get("team", "")
        
        # Get both drivers from the team
        teammates = get_drivers_for_team(team)
        if len(teammates) < 2:
            return 0.5  # No teammate data
        
        other_driver = [t for t in teammates if t["id"] != driver_id][0]
        
        # Compare ELO ratings
        elo_diff = driver.get("elo", 1500) - other_driver.get("elo", 1500)
        
        # Convert ELO difference to win probability using logistic function
        # Typical ELO difference between teammates: 0-100 points
        # 50 point difference ≈ 57% win probability
        prob = 1.0 / (1.0 + math.exp(-elo_diff / 100))
        
        # Clamp to reasonable range
        return max(0.05, min(0.95, prob))
    except Exception:
        return 0.5


# ── DNF probability estimation ─────────────────────────────────────────────────

def estimate_dnf_probability(driver_id: str, circuit_id: Optional[str] = None) -> float:
    """
    Estimate probability of DNF based on driver reliability and circuit risk.
    """
    try:
        driver = get_driver(driver_id)
        
        # Base DNF rate from driver stats
        career_dnf = driver.get("dnf_rate_career", 0.15)
        recent_dnf = driver.get("dnf_rate_recent", 0.15)
        base_dnf = 0.4 * career_dnf + 0.6 * recent_dnf
        
        # Adjust for circuit risk if provided
        if circuit_id:
            try:
                circuit = get_circuit(circuit_id)
                wall_crash_prob = circuit.get("wall_crash_probability_per_lap", 0.002)
                lap_count = circuit.get("lap_count", 60)
                
                # Circuit-specific DNF risk
                circuit_risk = wall_crash_prob * lap_count * 3  # Multiplier for overall race
                
                # Blend driver and circuit factors
                base_dnf = 0.7 * base_dnf + 0.3 * min(0.3, circuit_risk)
            except Exception:
                pass
        
        # Clamp to reasonable range (typical DNF rates: 5-30%)
        return max(0.05, min(0.45, base_dnf))
    except Exception:
        return 0.15


# ── SOTA LAG FEATURES ─────────────────────────────────────────────────────────

def compute_lag_features(driver_id: str, n_last: int = 5) -> Dict[str, float]:
    """
    Compute rolling lag features from recent race results.
    
    SOTA: Last 3/5 race rolling metrics including:
    - Average finishing position over last 3/5 races
    - Form trend (improving/declining)
    - Consistency (std dev of positions)
    
    Args:
        driver_id: Driver identifier
        n_last: Number of recent races to consider
        
    Returns:
        Dict with lag feature scores
    """
    try:
        results = get_driver_last_n_results(driver_id, n=n_last)
        valid_results = [
            r for r in results
            if r.get("status", "Finished") not in ("DNS",)
            and r.get("position", 0) > 0
        ]
        
        if len(valid_results) < 2:
            return {
                "lag_avg_position_last_3": 0.5,
                "lag_avg_position_last_5": 0.5,
                "lag_form_trend": 0.0,
            }
        
        positions = [r["position"] for r in valid_results if r["position"] > 0]
        
        if len(positions) == 0:
            return {
                "lag_avg_position_last_3": 0.5,
                "lag_avg_position_last_5": 0.5,
                "lag_form_trend": 0.0,
            }
        
        # Last 3 average
        last_3 = positions[-3:] if len(positions) >= 3 else positions
        avg_3 = sum(last_3) / len(last_3)
        score_3 = max(0.05, 1.0 - (avg_3 - 1) / (N_DRIVERS - 1))
        
        # Last 5 average
        last_5 = positions[-5:] if len(positions) >= 5 else positions
        avg_5 = sum(last_5) / len(last_5)
        score_5 = max(0.05, 1.0 - (avg_5 - 1) / (N_DRIVERS - 1))
        
        # Form trend: recent half vs earlier half
        mid = len(positions) // 2
        recent_avg = sum(positions[mid:]) / max(len(positions[mid:]), 1)
        earlier_avg = sum(positions[:mid]) / max(len(positions[:mid]), 1)
        form_trend = (earlier_avg - recent_avg) / N_DRIVERS  # Positive = improving
        
        return {
            "lag_avg_position_last_3": round(score_3, 4),
            "lag_avg_position_last_5": round(score_5, 4),
            "lag_form_trend": round(form_trend, 4),
        }
    except Exception:
        return {
            "lag_avg_position_last_3": 0.5,
            "lag_avg_position_last_5": 0.5,
            "lag_form_trend": 0.0,
        }


def compute_quali_race_pace_ratio(driver_id: str) -> float:
    """
    Compute qualifying-to-race pace ratio.
    
    SOTA: Drivers with a higher quali-to-race ratio are stronger in race trim
    (better tire management, race craft). Lower ratio means one-lap specialists.
    
    Approximated from driver skills since exact data varies per circuit.
    
    Returns:
        Score near 1.0 = better race pace relative to qualifying
    """
    try:
        driver = get_driver(driver_id)
        tire_mgmt = driver.get("tire_management", 7.0) / 10.0
        brakezone = driver.get("brakezone_skill", 7.0) / 10.0
        experience = min(driver.get("experience_races", 0) / 100.0, 1.0)
        
        # Race pace = tire management + brake zone + experience bonus
        race_pace = tire_mgmt * 0.4 + brakezone * 0.4 + experience * 0.2
        
        # Quali pace = inverse of qualifying delta (lower delta = better quali)
        quali_delta = driver.get("qualifying_delta_avg", 0.25)
        quali_pace = max(0.1, 1.0 - quali_delta * 2)
        
        # Ratio: race pace / quali pace
        ratio = race_pace / max(quali_pace, 0.1)
        
        return min(1.5, max(0.5, ratio))
    except Exception:
        return 1.0


def compute_drs_efficiency(driver_id: str, circuit_id: str) -> float:
    """
    Compute DRS efficiency index.
    
    SOTA: How effectively a driver uses DRS. Influenced by:
    - Number of DRS zones on circuit
    - Driver's car characteristics (power unit demand)
    - Driver's qualifying delta (better qualifiers get more DRS benefit)
    
    Returns:
        DRS efficiency score (0-1)
    """
    try:
        circuit = get_circuit(circuit_id)
        drs_zones = circuit.get("drs_zones", 2)
        power_demand = circuit.get("power_unit_demand", 6.5)
        
        driver = get_driver(driver_id)
        quali_delta = driver.get("qualifying_delta_avg", 0.25)
        
        # More DRS zones = more overtaking opportunities
        drs_factor = drs_zones / 3.0  # Normalize to max ~0.67
        
        # Power demand: higher = bigger DRS effect (long straights)
        power_factor = power_demand / 10.0
        
        # Qualifying delta: better qualifiers are more likely to be ahead
        # and thus benefit from DRS less (they have DRS detection ahead)
        quali_factor = 1.0 - min(quali_delta * 2, 0.5)
        
        efficiency = drs_factor * 0.4 + power_factor * 0.4 + quali_factor * 0.2
        
        return min(1.0, max(0.1, efficiency))
    except Exception:
        return 0.5


def compute_team_tire_strategy_score(driver_id: str) -> float:
    """
    Compute team's tire strategy capability.
    
    SOTA: Combines driver tire management with team-level strategy quality.
    Top teams (Mercedes, Red Bull) have better strategy operations.
    
    Returns:
        Strategy score (0-1)
    """
    try:
        driver = get_driver(driver_id)
        team = driver.get("team", "")
        tire_mgmt = driver.get("tire_management", 7.0) / 10.0
        
        # Team strategy quality (estimated from constructor strength)
        team_strategy_quality = {
            "mercedes": 0.95, "red_bull": 0.92, "ferrari": 0.88,
            "mclaren": 0.85, "williams": 0.72, "alpine": 0.70,
            "haas": 0.65, "rb": 0.60, "aston_martin": 0.62,
            "audi": 0.50, "cadillac": 0.45,
        }
        strategy_quality = team_strategy_quality.get(team, 0.60)
        
        # Blend: 60% driver tire management, 40% team strategy
        score = tire_mgmt * 0.6 + strategy_quality * 0.4
        
        return min(1.0, max(0.1, score))
    except Exception:
        return 0.5


# ── SOTA Feature Enricher ────────────────────────────────────────────────────

def enrich_with_sota_features(
    base_features: Dict[str, float],
    driver_id: str,
    circuit_id: str,
) -> Dict[str, float]:
    """
    Enrich base feature dict with SOTA lag and advanced features.
    
    Args:
        base_features: Existing feature dict from composite score
        driver_id: Driver identifier
        circuit_id: Circuit identifier
        
    Returns:
        Enriched feature dict with all SOTA features
    """
    lag = compute_lag_features(driver_id)
    quali_race = compute_quali_race_pace_ratio(driver_id)
    drs = compute_drs_efficiency(driver_id, circuit_id)
    tire_strategy = compute_team_tire_strategy_score(driver_id)
    
    # Add SOTA features to base
    enriched = dict(base_features)
    enriched.update(lag)
    enriched["quali_to_race_pace_ratio"] = quali_race
    enriched["drs_efficiency"] = drs
    enriched["team_tire_strategy_score"] = tire_strategy
    
    return enriched


# ── Composite score ────────────────────────────────────────────────────────────

def compute_composite_score(driver_id: str, circuit_id: str,
                            rain_probability: Optional[float] = None,
                            actual_grid_pos: Optional[int] = None) -> dict:
    """Compute weighted composite performance score for a driver at a circuit."""
    driver = get_driver(driver_id)
    team_id = driver.get("team", "")
    
    base_features = {
        "elo_rating":           compute_elo_score(driver_id),
        "constructor_strength": compute_constructor_strength(team_id, circuit_id),
        "recent_form":          compute_recent_form_score(driver_id),
        "track_type_fit":       compute_track_fit_score(driver_id, circuit_id),
        "reliability":          compute_reliability_score(driver_id),
        "weather_adjustment":   compute_weather_score(driver_id, circuit_id, rain_probability),
        "safety_car_upside":    compute_safety_car_upside(driver_id, circuit_id),
        "grid_position":        compute_grid_position_score(driver_id, actual_grid_pos),
    }
    
    # SOTA: Enrich with lag, DRS, quali-race ratio, and tire strategy features
    features = enrich_with_sota_features(base_features, driver_id, circuit_id)
    
    # Use original FEATURE_WEIGHTS for composite (SOTA features are for ML models)
    composite = sum(FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in base_features.items())
    
    # FEATURE-4: Apply circuit-specific history modifier
    circuit_modifier = calculate_circuit_performance_modifier(driver_id, circuit_id)
    composite *= circuit_modifier
    
    return {
        "driver_id":              driver_id,
        "features":               features,
        "composite_score":        round(composite, 6),
        "dnf_probability":        round(estimate_dnf_probability(driver_id, circuit_id), 4),
        "teammate_beat_probability": round(compute_teammate_beat_probability(driver_id), 4),
        "circuit_history_modifier": round(circuit_modifier, 4),  # For transparency
        "sota_features": {k: features[k] for k in [
            "lag_avg_position_last_3", "lag_avg_position_last_5", "lag_form_trend",
            "quali_to_race_pace_ratio", "drs_efficiency", "team_tire_strategy_score",
        ]},
    }


def compute_all_drivers(circuit_id: str, rain_probability: Optional[float] = None,
                        grid_overrides: Optional[dict] = None) -> list:
    """Run full pipeline for every driver. grid_overrides: {driver_id: grid_pos}."""
    grid_overrides = grid_overrides or {}
    results = [
        compute_composite_score(
            d["id"], circuit_id, rain_probability,
            actual_grid_pos=grid_overrides.get(d["id"])
        )
        for d in get_all_drivers()
    ]
    return sorted(results, key=lambda x: x["composite_score"], reverse=True)
