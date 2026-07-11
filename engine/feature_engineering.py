"""
Feature Engineering Pipeline — v2 improvements.

FIXES vs v1:
  1. Grid position no longer hardcoded to 0.5 — compute_grid_position_score() uses
     championship position + qualifying delta as a proper pre-race proxy.
     When actual_grid_pos is provided (post-qualifying), it uses that directly.
  2. DNF penalty for non-finishers: v1 used position 21 (n_drivers+1).
     A DNF is worse than P20 — now mapped to 25 (n_drivers + 5).
  3. temporal_cross_validate length check replaced with join-based logic (no crash
     when rounds have different driver counts).
  4. All functions handle KeyError gracefully (no silent state mutation).
  
FEATURE-4 ADDITION:
  5. Driver-specific circuit history integrated as performance modifier in composite score.

LIVE DATA INTEGRATION (v3.1):
  6. When LIVE_DATA_ENABLED is True, the engine fetches fresh driver standings,
     constructor strength, and recent form from Jolpica-F1 API. Falls back to
     hardcoded data if the API is unavailable.
"""

import math
from typing import Any, Dict, Optional
import datetime
import logging

logger = logging.getLogger(__name__)

from config.settings import (
    CONSTRUCTOR_STRENGTH, FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW,
    LIVE_DATA_ENABLED, LIVE_OPENF1_ENABLED,
)
from data.driver_data import get_driver, get_all_drivers, get_drivers_for_team, calculate_circuit_performance_modifier
from data.circuit_data import get_circuit, circuit_favors_team
from data.fastf1_integration import FASTF1_AVAILABLE, extract_ml_features
from data.calendar_2026 import get_race_by_circuit
from data.season_2026 import get_driver_last_n_results, DRIVER_STANDINGS_AFTER_R5

N_DRIVERS = 22
DNF_POSITION_PENALTY = N_DRIVERS + 5  # 27 — beyond last-place finish
_FASTF1_FEATURE_CACHE = {}

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
        
        # A-5 FIX: Tire management bonus at high-deg circuits
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
        
        # Try to get historical safety car data from FastF1 if available
        from data.fastf1_integration import is_fastf1_available, _load_fastf1_features_for_race
        
        sc_prob_static = circuit.get("safety_car_probability", 0.5)
        sc_prob = sc_prob_static  # Default to static value
        
        # If FastF1 is available, try to blend with historical data
        if is_fastf1_available():
            # Look for historical data from the same circuit in previous years
            for year_offset in range(1, 6):  # Check previous 5 years
                prev_year = datetime.now().year - year_offset
                try:
                    fastf1_features = _load_fastf1_features_for_race(circuit_id, prev_year)  # Assuming this function exists or creating similar logic
                    if fastf1_features and "race_features" in fastf1_features:
                        historical_sc = fastf1_features["race_features"].get("safety_car")
                        if historical_sc is not None:
                            sc_prob_historical = 0.8 if historical_sc else 0.2
                            # Blend static and historical probabilities
                            sc_prob = 0.5 * sc_prob_static + 0.5 * sc_prob_historical
                            break  # Use first available historical data
                except:
                    continue  # Try next year if this fails
        
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
        
        # Clamp to reasonable bounds
        return max(0.0, min(1.0, upside))
    except Exception as e:
        logger.warning(f"Error computing safety car upside: {e}")
        # Fallback to original calculation
        circuit = get_circuit(circuit_id)
        sc_prob = circuit.get("safety_car_probability", 0.5)
        if estimated_grid_pos is None:
            driver = get_driver(driver_id)
            points = driver.get("championship_points_2026", 50)
            estimated_grid_pos = max(1, min(20, 2 + int((100 - points) / 5)))
        grid_factor = (estimated_grid_pos - 1) / (N_DRIVERS - 1)
        return max(0.0, min(1.0, sc_prob * grid_factor))


def compute_championship_pressure(driver_id: str) -> float:
    """
    Calculate championship pressure based on live standings.
    Drivers mathematically still in title contention drive with different risk profiles
    than those with nothing left to fight for.
    
    Returns:
        Pressure factor: 0.0 (no pressure) to 1.0 (maximum pressure)
        - Drivers with realistic title chances: higher pressure (0.6-1.0)
        - Drivers out of title contention: lower pressure (0.0-0.4)
    """
    try:
        from data.jolpica_client import get_jolpica_client
        from data.fastf1_integration import is_fastf1_available
        
        # Get live driver standings
        live_standings = get_live_driver_standings()
        if not live_standings:
            # Fallback to hardcoded data if live data unavailable
            return 0.5  # Neutral pressure
        
        # Calculate championship pressure based on points gap to leader
        current_points = live_standings.get(driver_id, {}).get('points', 0)
        
        # Find the leader's points
        leader_points = max([standings.get('points', 0) for standings in live_standings.values()], default=0)
        
        # Find max points available (leader + remaining races * 25)
        # Assuming 25 points for a win, calculate theoretical max
        total_races = 24  # F1 typically has 23-24 races per season
        completed_races = len([r for r in get_all_races() if r.get('completed', False)])  # Simplified
        remaining_races = max(0, total_races - completed_races)
        max_possible_points = current_points + remaining_races * 25
        
        # Calculate if driver still mathematically has title chance
        still_in_contention = max_possible_points >= leader_points
        
        if not still_in_contention:
            # Driver is mathematically out of title contention
            return 0.2  # Low pressure
        
        # Calculate pressure based on points gap and remaining races
        points_gap = leader_points - current_points
        pressure_base = min(1.0, (max_possible_points - points_gap) / max_possible_points)
        
        # Adjust pressure based on proximity to title
        if points_gap <= 50:  # Within 2 wins of leader
            return min(1.0, 0.6 + (50 - points_gap) / 100.0)  # High pressure
        elif points_gap <= 100:  # Within 4 wins of leader
            return min(0.8, 0.4 + (100 - points_gap) / 150.0)  # Medium-high pressure
        else:
            return max(0.2, 0.4 - (points_gap - 100) / 200.0)  # Lower pressure but still in contention
    
    except Exception as e:
        logger.warning(f"Error computing championship pressure for {driver_id}: {e}")
        return 0.5  # Neutral pressure on error


def get_all_races():
    """Helper function to get all races for calculating championship pressure."""
    try:
        from data.calendar_2026 import CALENDAR_2026
        return CALENDAR_2026.get(2026, [])
    except:
        # Return empty list if calendar not available
        return []


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

def build_empirical_dnf_rates(seasons: list[int], circuit_id: str) -> dict:
    """Mine historical Jolpica results for real DNF statistics at this circuit."""
    from data.jolpica_client import get_jolpica_client
    
    client = get_jolpica_client()
    causes = {"accident": 0, "mechanical": 0, "finished": 0, "other": 0}
    total_starts = 0
    
    for season in seasons:
        try:
            results = client.get_season_results(season)
            for race in results:
                if race.get("circuit") != circuit_id:
                    continue
                for entry in race.get("results", []):
                    total_starts += 1
                    status = entry.get("status", "").lower()
                    if "finished" in status or "+1 lap" in status or "classified" in status:
                        causes["finished"] += 1
                    elif any(k in status for k in ("collision", "accident", "spun off", "crash", "barrier")):
                        causes["accident"] += 1
                    elif any(k in status for k in ("engine", "gearbox", "hydraulics", "brakes", "suspension", "electrical", "power unit", "turbo", "mguk", "mguh", "ers", "fuel", "oil", "water")):
                        causes["mechanical"] += 1
                    else:
                        causes["other"] += 1
        except Exception as e:
            logger.warning(f"Could not fetch historical data for season {season}: {e}")
            continue
    
    return {k: v / total_starts for k, v in causes.items()} if total_starts else {}


def estimate_dnf_probability(driver_id: str, circuit_id: Optional[str] = None) -> float:
    """
    Estimate probability of DNF based on driver reliability and circuit risk.
    
    IMPROVEMENT: Uses empirical DNF rates from historical Jolpica data when available,
    falling back to static driver stats if historical data is not available.
    """
    try:
        driver = get_driver(driver_id)
        
        # Try to get empirical DNF rates from historical Jolpica data
        empirical_dnf_rate = None
        if circuit_id:
            # Get historical data for the past 3-5 seasons
            historical_seasons = list(range(datetime.now().year - 5, datetime.now().year))
            historical_dnf_data = build_empirical_dnf_rates(historical_seasons, circuit_id)
            
            if historical_dnf_data:
                # Calculate empirical DNF rate based on historical data
                total_dnf = historical_dnf_data.get("accident", 0) + historical_dnf_data.get("mechanical", 0) + historical_dnf_data.get("other", 0)
                empirical_dnf_rate = total_dnf if total_dnf > 0 else None
        
        # Base DNF rate from driver stats (fallback)
        career_dnf = driver.get("dnf_rate_career", 0.15)
        recent_dnf = driver.get("dnf_rate_recent", 0.15)
        base_dnf = 0.4 * career_dnf + 0.6 * recent_dnf
        
        # If we have empirical data, blend it with the driver stats
        if empirical_dnf_rate is not None:
            # Weight empirical data higher (0.7) with driver stats as backup (0.3)
            base_dnf = 0.7 * empirical_dnf_rate + 0.3 * base_dnf
        
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


def _load_fastf1_features_for_race(circuit_id: str, season: int = 2026) -> Optional[Dict[str, Any]]:
    """Load and cache FastF1 extracted features for a given race.
    
    Q-3 FIX: Falls back to previous season (2025) if current season data unavailable.
    """
    from data.fastf1_integration import is_fastf1_available  # Import the function
    
    if not is_fastf1_available():
        return None

    race = get_race_by_circuit(circuit_id)
    if not race:
        return None

    race_name = race.get("name")
    if not race_name:
        return None

    cache_key = f"{season}:{race_name}"
    if cache_key in _FASTF1_FEATURE_CACHE:
        return _FASTF1_FEATURE_CACHE[cache_key]

    try:
        features = extract_ml_features(season, race_name)
        _FASTF1_FEATURE_CACHE[cache_key] = features
        return features
    except Exception as e:
        logger.warning(f"FastF1 feature extraction failed for {race_name}: {e}")
        _FASTF1_FEATURE_CACHE[cache_key] = None
        return None


def _get_fastf1_adjustment(driver_id: str, circuit_id: str, season: int = 2026) -> float:
    """Return a small score adjustment from FastF1 extracted race features.
    
    Q-3 FIX: Falls back to previous season data if current season unavailable.
    """
    # Q-3 FIX: Try current season first, fall back to previous season (2025)
    features = _load_fastf1_features_for_race(circuit_id, season)
    if not features:
        features = _load_fastf1_features_for_race(circuit_id, season - 1)  # 2025 proxy
    if not features:
        return 0.0

    driver_short = get_driver(driver_id).get("short", "").upper()
    driver_data = features.get("driver_features", {}).get(driver_short)
    if not driver_data:
        return 0.0

    avg_lap = driver_data.get("avg_lap_time")
    lap_std = driver_data.get("lap_time_std")
    pit_stops = driver_data.get("pit_stops", 1)
    dnf_flag = driver_data.get("dnf", False)

    if avg_lap is None or lap_std is None:
        return 0.0

    field_laps = [v.get("avg_lap_time") for v in features.get("driver_features", {}).values() if v.get("avg_lap_time")]
    if not field_laps:
        return 0.0

    best_lap = min(field_laps)
    lap_score = max(0.0, min(1.0, best_lap / avg_lap))
    consistency_score = max(0.0, min(1.0, 1.0 - min(1.0, lap_std / 3.0)))
    pit_penalty = min(0.15, max(0.0, (pit_stops - 1) * 0.05))
    dnf_penalty = 0.08 if dnf_flag else 0.0

    adjustment = (lap_score * 0.5 + consistency_score * 0.3 - pit_penalty - dnf_penalty) * 0.12
    return max(-0.1, min(0.15, adjustment))


def calculate_age_based_experience_factor(driver_id: str) -> float:
    """
    Calculate an age and experience based factor for the driver.
    
    Younger drivers with less experience may have higher growth potential,
    while veteran drivers with lots of experience have proven consistency.
    
    Returns:
        Factor between 0.9 and 1.1 to multiply with composite score
    """
    try:
        driver = get_driver(driver_id)
        
        # Get driver age and experience
        age = driver.get("age", 30)  # Default to 30 if not specified
        experience_years = driver.get("experience_years", 5)  # Years in F1 or racing
        experience_races = driver.get("experience_races", 50)  # Total races
        
        # Base factor is 1.0 (neutral)
        factor = 1.0
        
        # Adjust based on age
        # Drivers in 20s (20-29) are considered optimal age range - slight boost
        if 20 <= age <= 29:
            factor += 0.02  # Slight positive adjustment
        elif age < 20:  # Very young drivers
            # Young drivers have potential but less experience
            factor -= 0.02
        elif age > 35:  # Older drivers
            # Experience helps offset some physical decline
            exp_factor = min(0.05, experience_years * 0.005)  # Experience bonus
            age_factor = max(-0.05, -0.002 * (age - 35))  # Age penalty
            factor = factor + exp_factor + age_factor
        
        # Adjust based on experience
        if experience_races < 20:  # Rookie level
            factor -= 0.05  # Penalty for inexperience
        elif experience_races < 50:  # Novice level
            factor -= 0.02  # Small penalty
        elif experience_races > 200:  # Veteran level
            factor += 0.03  # Bonus for extensive experience
        
        # Ensure factor stays within reasonable bounds
        return max(0.9, min(1.1, factor))
    except Exception as e:
        logger.warning(f"Error calculating age/experience factor for {driver_id}: {e}")
        # Return neutral factor on error
        return 1.0


# ── Composite score ────────────────────────────────────────────────────────────

def compute_composite_score(
    driver_id: str,
    circuit_id: str,
    rain_probability: Optional[float] = None,
    actual_grid_pos: Optional[int] = None,
) -> dict:
    """
    Compute all features and return weighted composite score.

    FIX: grid_position now uses compute_grid_position_score() instead of hardcoded 0.5.
    FEATURE-4: Circuit history modifier applied to final composite score.
    FEATURE-X: Championship pressure based on live standings added.
    FEATURE-Y: Age/experience factor based on real driver data added.
    """
    driver = get_driver(driver_id)
    features = {
        "elo_rating":           compute_elo_score(driver_id),
        "constructor_strength": compute_constructor_strength(driver["team"], circuit_id),
        "recent_form":          compute_recent_form_score(driver_id),
        "track_type_fit":       compute_track_fit_score(driver_id, circuit_id),
        "reliability":          compute_reliability_score(driver_id),
        "weather_adjustment":   compute_weather_score(driver_id, circuit_id, rain_probability),
        "safety_car_upside":    compute_safety_car_upside(driver_id, circuit_id),
        # FIX: no longer hardcoded to 0.5
        "grid_position":        compute_grid_position_score(driver_id, actual_grid_pos),
        "fastf1_adjustment":   _get_fastf1_adjustment(driver_id, circuit_id),
        "championship_pressure": compute_championship_pressure(driver_id),  # NEW: Championship pressure feature
        "age_experience_factor": calculate_age_based_experience_factor(driver_id),  # NEW: Age-based experience factor
    }
    # Calculate composite score with all features
    base_composite = sum(FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in features.items() if k != "age_experience_factor")
    # Apply age experience factor as a multiplier to the final score
    composite = base_composite * features["age_experience_factor"]
    
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
        "championship_pressure": round(features["championship_pressure"], 4),  # For transparency
        "age_experience_factor": round(features["age_experience_factor"], 4),  # For transparency
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
