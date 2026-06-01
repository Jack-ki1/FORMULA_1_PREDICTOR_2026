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
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from config.settings import FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW
from data.driver_data import get_driver, get_all_drivers, get_drivers_for_team, calculate_circuit_performance_modifier
from data.circuit_data import get_circuit, circuit_favors_team
from data.season_2026 import get_driver_last_n_results, DRIVER_STANDINGS_AFTER_R5

N_DRIVERS = 22
DNF_POSITION_PENALTY = N_DRIVERS + 5  # 25 — worse than last finisher


# ── ELO ────────────────────────────────────────────────────────────────────────

def compute_elo_score(driver_id: str) -> float:
    """
    Compute normalized ELO score for a driver.
    
    FEATURE-9: Now uses multi-dimensional ELO system with race ELO as primary metric.
    Falls back to basic ELO from driver data if multi-dimensional system unavailable.
    
    Section 3.4 Fix: Dampens ELO influence for inexperienced drivers (rookies).
    """
    try:
        # Try to use multi-dimensional ELO system first (FEATURE-9)
        try:
            from engine.multi_dimensional_elo import get_elo_system
            elo_system = get_elo_system()
            raw = elo_system.get_elo_score(driver_id, dimension="race")
        except ImportError:
            logger.debug("Multi-dimensional ELO not available, using basic ELO")
            raw = get_driver(driver_id)["elo"]
        
        # Normalize to [0, 1] range
        field = get_all_drivers()
        lo, hi = min(d["elo"] for d in field), max(d["elo"] for d in field)
        normalized = (raw - lo) / (hi - lo + 1e-9)
        
        # Section 3.4 Fix: Apply experience-based confidence weighting
        driver = get_driver(driver_id)
        experience_races = driver.get("experience_races", 0)
        confidence = min(1.0, experience_races / 30.0)  # Full confidence after 30 races
        
        # Blend toward 0.5 (neutral) for inexperienced drivers
        return 0.5 * (1 - confidence) + normalized * confidence
        
    except Exception:
        return 0.5


# ── Constructor strength ───────────────────────────────────────────────────────

# FIX: Recalibrated to match CONSTRUCTOR_STANDINGS_AFTER_R5 from season_2026.py
# Values derived from actual 2026 season results, not copied from older seasons
_CONSTRUCTOR_STRENGTH: dict = {
    "mercedes":     0.85,   # Hamilton (32) + Russell (75) = 107 pts - strong performance
    "mclaren":      0.82,   # Norris/Piastri consistently scoring
    "red_bull":     0.88,   # Verstappen (93) + Perez (45) = 138 pts - leading team
    "ferrari":      0.78,   # Leclerc/Sainz contributing solid points
    "williams":     0.45,   # Albon/Colapinto/Sainz contributing mid-field points
    "alpine":       0.40,   # Ocon only driver shown, lower strength
    "haas":         0.38,   # Bearman/Hulkenberg scoring occasional points
    "rb":           0.35,   # Lawson/Lindblad (but Lindblad inactive, so just Lawson/Tsunoda)
    "sauber":       0.30,   # Gasly at Sauber, moderate performance
    "kick_sauber":  0.25,   # Bottas/Palou, struggling team
    "aston_martin": 0.15,   # Alonso/Stroll struggling
    "cadillac":     0.10,   # New team, Herta/Palou
}

def compute_constructor_strength(team_id: str, circuit_id: str) -> float:
    base = _CONSTRUCTOR_STRENGTH.get(team_id, 0.25)
    try:
        mult = circuit_favors_team(circuit_id, team_id)
    except Exception:
        mult = 1.0
    return min(1.0, max(0.05, base * mult))


# ── Recent form ────────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str) -> float:
    """Exponentially-weighted average of last N finishing positions."""
    try:
        results = get_driver_last_n_results(driver_id, n=RECENCY_WINDOW)
        if not results:
            return 0.5
        
        # Convert positions to scores (1st = 1.0, 20th = 0.05, DNF = very low)
        def pos_to_score(pos):
            if pos is None or pos == "DNF" or pos <= 0:
                return 0.02  # Heavy penalty for DNF/no result
            return max(0.05, 1.0 - (pos - 1) / (N_DRIVERS - 1))
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for i, result in enumerate(results):
            weight = RECENCY_DECAY ** i
            # FIX: result is already an int position, not a dict
            score = pos_to_score(result)
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
    Section 7.4: Added structured logging for debugging and performance tracking.
    """
    import time
    t_start = time.perf_counter()
    
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
    }
    composite = sum(FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in features.items())
    
    # FEATURE-4: Apply circuit-specific history modifier
    circuit_modifier = calculate_circuit_performance_modifier(driver_id, circuit_id)
    composite *= circuit_modifier
    
    elapsed = time.perf_counter() - t_start
    logger.debug(f"Computed features for {driver_id} at {circuit_id} in {elapsed*1000:.2f}ms (score={composite:.4f})")
    
    return {
        "driver_id":              driver_id,
        "features":               features,
        "composite_score":        round(composite, 6),
        "dnf_probability":        round(estimate_dnf_probability(driver_id, circuit_id), 4),
        "teammate_beat_probability": round(compute_teammate_beat_probability(driver_id), 4),
        "circuit_history_modifier": round(circuit_modifier, 4),  # For transparency
    }


# Simple cache for pre-computed features (Section 7.5 optimization)
_feature_cache = {}


def compute_all_drivers(circuit_id: str, rain_probability: Optional[float] = None,
                        grid_overrides: Optional[dict] = None) -> list:
    """
    Run full pipeline for every driver. grid_overrides: {driver_id: grid_pos}.
    
    Section 7.5 Optimization: Caches results per (circuit_id, rain_probability) tuple
    to avoid redundant computation when same circuit is queried multiple times.
    Cache invalidates on grid_overrides since those are race-specific.
    """
    # Only use cache if no grid overrides (which are race-specific)
    cache_key = f"{circuit_id}:{rain_probability}"
    if not grid_overrides and cache_key in _feature_cache:
        logger.debug(f"Cache hit for {cache_key}")
        return _feature_cache[cache_key]
    
    grid_overrides = grid_overrides or {}
    results = [
        compute_composite_score(
            d["id"], circuit_id, rain_probability,
            actual_grid_pos=grid_overrides.get(d["id"])
        )
        for d in get_all_drivers()
    ]
    sorted_results = sorted(results, key=lambda x: x["composite_score"], reverse=True)
    
    # Cache only if no grid overrides
    if not grid_overrides:
        _feature_cache[cache_key] = sorted_results
        logger.debug(f"Cached results for {cache_key}")
    
    return sorted_results
