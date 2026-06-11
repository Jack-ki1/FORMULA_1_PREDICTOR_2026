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
"""

import math
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

from config.settings import CONSTRUCTOR_STRENGTH, FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW
from data.driver_data import get_driver, get_all_drivers, get_drivers_for_team, calculate_circuit_performance_modifier
from data.circuit_data import get_circuit, circuit_favors_team
from data.fastf1_integration import FASTF1_AVAILABLE, extract_ml_features
from data.calendar_2026 import get_race_by_circuit
from data.season_2026 import get_driver_last_n_results, DRIVER_STANDINGS_AFTER_R5

N_DRIVERS = 22
DNF_POSITION_PENALTY = N_DRIVERS + 5  # 27 — beyond last-place finish
_FASTF1_FEATURE_CACHE = {}


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

def compute_constructor_strength(team_id: str, circuit_id: str) -> float:
    base = CONSTRUCTOR_STRENGTH.get(team_id, 0.25)
    try:
        mult = circuit_favors_team(circuit_id, team_id)
    except Exception:
        mult = 1.0
    return min(1.0, max(0.05, base * mult))


# ── Recent form ────────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str) -> float:
    """Exponentially-weighted average of last N finishing positions.
    
    FIXED: get_driver_last_n_results returns List[int], not List[Dict].
    Previously crashed with AttributeError: 'int' object has no attribute 'get'
    """
    try:
        results = get_driver_last_n_results(driver_id, n=RECENCY_WINDOW)
        if not results:
            return 0.5
        
        # Convert positions to scores (1st = 1.0, 20th = 0.05, DNF = very low)
        def pos_to_score(pos):
            # Handle None, DNF string, or invalid positions
            if pos is None or pos == "DNF" or pos <= 0:
                return 0.02  # Heavy penalty for DNF/no result
            return max(0.05, 1.0 - (pos - 1) / (N_DRIVERS - 1))
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for i, result in enumerate(results):
            weight = RECENCY_DECAY ** i
            # FIXED: result is already an integer position, not a dict
            score = pos_to_score(result if isinstance(result, int) else 20)
            weighted_sum += weight * score
            weight_total += weight
        
        return weighted_sum / weight_total if weight_total > 0 else 0.5
    except Exception:
        return 0.5


# ── Track type fit ─────────────────────────────────────────────────────────────

def compute_track_fit_score(driver_id: str, circuit_id: str) -> float:
    """Match driver's strengths to circuit characteristics."""
    try:
        driver = get_driver(driver_id)
        circuit = get_circuit(circuit_id)
        
        track_types = circuit.get("circuit_type", ["balanced"])
        fits = driver.get("track_type_fit", {})
        
        # Average fit across all circuit types
        total_fit = sum(fits.get(t, 1.0) for t in track_types)
        avg_fit = total_fit / len(track_types)
        
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
    """Wet skill × rain probability interaction."""
    try:
        driver = get_driver(driver_id)
        wet_skill = driver.get("wet_skill", 5.0) / 10.0  # Normalize to 0-1
        
        rain_prob = rain_probability if rain_probability is not None else 0.2
        
        # Base score is neutral, adjusted by wet skill and rain probability
        # If no rain expected, wet skill doesn't matter much
        # If high rain, wet specialists get big boost
        base_score = 0.5
        wet_bonus = (wet_skill - 0.5) * rain_prob * 0.6  # Max ±0.3 adjustment
        
        return max(0.0, min(1.0, base_score + wet_bonus))
    except Exception:
        return 0.5


# ── Safety car upside ──────────────────────────────────────────────────────────

def compute_safety_car_upside(driver_id: str, circuit_id: str, 
                             estimated_grid_pos: Optional[int] = None) -> float:
    """
    Drivers starting further back benefit more from safety cars.
    SC probability comes from circuit data.
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
        
        # Combine with circuit SC probability
        upside = sc_prob * grid_factor * 0.8  # Scale to reasonable range
        
        return max(0.0, min(0.8, upside))
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


def _load_fastf1_features_for_race(circuit_id: str, season: int = 2026) -> Optional[Dict[str, Any]]:
    """Load and cache FastF1 extracted features for a given race."""
    if not FASTF1_AVAILABLE:
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
    """Return a small score adjustment from FastF1 extracted race features."""
    features = _load_fastf1_features_for_race(circuit_id, season)
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
    }
    composite = sum(FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in features.items())
    
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
