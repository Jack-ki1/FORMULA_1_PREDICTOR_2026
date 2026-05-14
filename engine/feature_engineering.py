"""
Feature Engineering Pipeline for F1 Race Prediction.

Computes all input features for each driver at a given circuit,
using only pre-race data (no leakage).

Features produced per driver:
  - elo_score
  - constructor_strength_score
  - recent_form_score        (recency-weighted finishing positions)
  - track_fit_score          (circuit-type historical performance)
  - reliability_score        (inverse DNF risk)
  - weather_score            (wet skill * rain probability)
  - safety_car_upside        (benefit to lower-grid drivers under SC)
  - teammate_delta           (qualifying gap to teammate)
  - composite_score          (weighted blend → input to probability model)
"""

import math
from typing import Optional, Dict, List

from config.settings import FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW
from data.driver_data import get_driver, get_all_drivers, get_drivers_for_team
from data.circuit_data import get_circuit, circuit_favors_team
from data.season_2026 import get_driver_last_n_results, DRIVER_STANDINGS_AFTER_R4


# ── ELO ───────────────────────────────────────────────────────────────────────

def compute_elo_score(driver_id: str) -> float:
    """
    Normalise raw ELO to a 0–1 score relative to field.
    ELO range in current dataset: ~1460 – 1645.
    """
    try:
        driver = get_driver(driver_id)
        raw_elo = driver["elo"]
        field = get_all_drivers()
        
        if not field:
            raise ValueError("No driver data available")
            
        min_elo = min(d["elo"] for d in field)
        max_elo = max(d["elo"] for d in field)
        
        if max_elo == min_elo:
            return 0.5  # All drivers have same elo
        
        return (raw_elo - min_elo) / (max_elo - min_elo + 1e-9)
    except KeyError:
        # If driver_id doesn't exist, return a neutral value
        return 0.5
    except Exception:
        # For any other error, return a neutral value
        return 0.5


# ── Constructor Strength ───────────────────────────────────────────────────────

_CONSTRUCTOR_STRENGTH: dict = {
    "mercedes":     0.96,
    "mclaren":      0.82,
    "ferrari":      0.78,
    "red_bull":     0.60,
    "alpine":       0.42,
    "haas":         0.38,
    "racing_bulls": 0.35,
    "williams":     0.28,
    "audi":         0.22,
    "aston_martin": 0.15,
    "cadillac":     0.10,
}

def compute_constructor_strength(team_id: str, circuit_id: str) -> float:
    """
    Blend base constructor strength with circuit-specific win history.
    """
    base = _CONSTRUCTOR_STRENGTH.get(team_id, 0.25)
    try:
        circuit_mult = circuit_favors_team(circuit_id, team_id)
    except Exception:
        # If circuit lookup fails, use multiplier of 1.0
        circuit_mult = 1.0
    
    # Cap between 0.05 and 1.0
    return min(1.0, max(0.05, base * circuit_mult))


# ── Recent Form ────────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str, n: int = RECENCY_WINDOW) -> float:
    """
    Exponentially weighted average of recent finishing positions.
    Lower finishing position = better. Returns 0–1 (1 = best).
    """
    try:
        results = get_driver_last_n_results(driver_id, n=n)
    except Exception:
        # If unable to get results, return neutral score
        return 0.5
        
    if not results:
        return 0.5  # No data → neutral

    total_weight = 0.0
    weighted_pos = 0.0
    n_drivers = 20  # field size

    for i, r in enumerate(results):
        weight = RECENCY_DECAY ** i  # most recent race gets weight 1.0
        pos = r["position"] if r["position"] is not None else n_drivers + 1  # DNF → last
        weighted_pos += weight * pos
        total_weight += weight

    if total_weight == 0:
        return 0.5  # Prevent division by zero
        
    avg_pos = weighted_pos / total_weight
    # Invert so P1 → 1.0, P20 → 0.0
    return 1.0 - ((avg_pos - 1) / (n_drivers - 1))


# ── Track Type Fit ─────────────────────────────────────────────────────────────

def compute_track_fit_score(driver_id: str, circuit_id: str) -> float:
    """
    Score how well a driver's historical performance maps to this circuit type.
    Multiple circuit types are blended if the circuit has more than one.
    """
    try:
        driver = get_driver(driver_id)
        circuit = get_circuit(circuit_id)
        circuit_types = circuit.get("circuit_type", ["balanced"])
    except Exception:
        # If lookup fails, return neutral value
        return 0.5

    fit_values = []
    for ctype in circuit_types:
        fit = driver["track_type_fit"].get(ctype, 1.0)
        fit_values.append(fit)

    if not fit_values:
        return 0.5  # Neutral if no fit data
        
    avg_fit = sum(fit_values) / len(fit_values)
    # Normalise to 0–1 (typical range 0.90–1.20)
    return max(0.0, min(1.0, (avg_fit - 0.85) / 0.40))


# ── Reliability ────────────────────────────────────────────────────────────────

def compute_reliability_score(driver_id: str) -> float:
    """
    Returns a 0–1 reliability score. Higher = less likely to DNF.
    Blends career DNF rate with recent 3-season rate.
    """
    try:
        driver = get_driver(driver_id)
        career_dnf = driver["dnf_rate_career"]
        recent_dnf = driver["dnf_rate_recent"]
    except Exception:
        # If data unavailable, return neutral reliability
        return 0.7  # Standard reliability
        
    # Weight recent more heavily
    blended_dnf = 0.35 * career_dnf + 0.65 * recent_dnf
    # Smooth with constructor DNF context
    return 1.0 - min(blended_dnf, 1.0)


def estimate_dnf_probability(driver_id: str) -> float:
    """
    Forward-looking DNF probability for this race.
    Adds a small base rate for mechanical failures.
    """
    try:
        driver = get_driver(driver_id)
        recent_dnf = driver["dnf_rate_recent"]
        career_dnf = driver["dnf_rate_career"]
        experience = driver["experience_races"]
    except Exception:
        # If data unavailable, return moderate DNF probability
        return 0.05  # 5% baseline DNF rate

    # Low experience → higher mechanical risk (car not yet optimised for driver)
    exp_factor = max(0.0, 0.05 * math.exp(-experience / 40))
    blended = 0.4 * career_dnf + 0.6 * recent_dnf + exp_factor
    return min(blended, 0.45)  # cap at 45%


# ── Weather ────────────────────────────────────────────────────────────────────

def compute_weather_score(driver_id: str, circuit_id: str, rain_probability: Optional[float] = None) -> float:
    """
    Wet-weather performance adjustment.
    If rain_probability is None, uses circuit's typical value.
    """
    try:
        driver = get_driver(driver_id)
        circuit = get_circuit(circuit_id)
    except Exception:
        # If lookup fails, return neutral score
        return 0.5

    rain_prob = rain_probability if rain_probability is not None else circuit.get("rain_probability_typical", 0.2)
    wet_skill = driver["wet_skill"] / 10.0  # normalise to 0–1

    # Score = rain probability * wet_skill delta from average (0.75 normalised average)
    delta_from_avg = wet_skill - 0.75
    return 0.5 + (rain_prob * delta_from_avg * 2.0)  # centred at 0.5


# ── Safety Car Upside ──────────────────────────────────────────────────────────

def compute_safety_car_upside(driver_id: str, circuit_id: str, estimated_grid_pos: Optional[int] = None) -> float:
    """
    Drivers starting further back benefit disproportionately from safety cars
    at high-SC-probability circuits (free pit stops, compression of gaps).
    """
    try:
        circuit = get_circuit(circuit_id)
        sc_prob = circuit.get("safety_car_probability", 0.50)
    except Exception:
        # If lookup fails, use default SC probability
        sc_prob = 0.50

    try:
        driver = get_driver(driver_id)
    except Exception:
        # If driver lookup fails, return neutral value
        return 0.25

    # Use championship position as proxy for expected grid
    try:
        standings = {s["driver"]: s["position"] for s in DRIVER_STANDINGS_AFTER_R4}
        champ_pos = standings.get(driver_id, 15)
        grid_proxy = estimated_grid_pos or min(champ_pos + 2, 20)  # rough estimate

        # Higher grid number = more SC upside
        sc_upside = sc_prob * ((grid_proxy - 1) / 19.0)
        return min(sc_upside, 0.8)
    except Exception:
        # If calculation fails, return neutral value
        return 0.25


# ── Teammate Delta ─────────────────────────────────────────────────────────────

def compute_teammate_beat_probability(driver_id: str) -> float:
    """
    Probability that this driver beats their teammate on race day.
    Based on qualifying delta and recent form comparison.
    """
    try:
        driver = get_driver(driver_id)
        team_id = driver["team"]
        teammates = [d for d in get_drivers_for_team(team_id) if d["id"] != driver_id]
    except Exception:
        # If unable to find teammates, return 50/50
        return 0.5

    if not teammates:
        return 0.5

    teammate = teammates[0]
    self_quali_delta = driver.get("qualifying_delta_avg", 0)
    mate_quali_delta = teammate.get("qualifying_delta_avg", 0)

    # Negative = faster
    delta_advantage = mate_quali_delta - self_quali_delta  # positive = this driver is faster

    # Form-based component
    self_form = compute_recent_form_score(driver_id)
    mate_form = compute_recent_form_score(teammate["id"])
    form_advantage = self_form - mate_form

    # Blend: 60% qualifying, 40% recent form
    raw_advantage = 0.60 * (delta_advantage / 200.0) + 0.40 * form_advantage
    probability = 0.5 + raw_advantage * 0.5
    return max(0.05, min(0.95, probability))


# ── Composite Score ────────────────────────────────────────────────────────────

def compute_composite_score(
    driver_id: str,
    circuit_id: str,
    rain_probability: Optional[float] = None,
    estimated_grid_pos: Optional[int] = None,
) -> dict:
    """
    Compute all features and return a weighted composite score (0–1).
    Higher composite score = better predicted performance.
    """
    driver = get_driver(driver_id)

    features = {
        "elo_rating":           compute_elo_score(driver_id),
        "constructor_strength": compute_constructor_strength(driver["team"], circuit_id),
        "recent_form":          compute_recent_form_score(driver_id),
        "track_type_fit":       compute_track_fit_score(driver_id, circuit_id),
        "reliability":          compute_reliability_score(driver_id),
        "weather_adjustment":   compute_weather_score(driver_id, circuit_id, rain_probability),
        "safety_car_upside":    compute_safety_car_upside(driver_id, circuit_id, estimated_grid_pos),
        # Grid position handled separately via conversion model
        "grid_position":        0.5,  # Placeholder; updated when grid is known
    }

    composite = sum(
        FEATURE_WEIGHTS.get(k, 0.0) * v
        for k, v in features.items()
    )

    return {
        "driver_id": driver_id,
        "features": features,
        "composite_score": round(composite, 6),
        "dnf_probability": round(estimate_dnf_probability(driver_id), 4),
        "teammate_beat_probability": round(compute_teammate_beat_probability(driver_id), 4),
    }


def compute_all_drivers(circuit_id: str, rain_probability: Optional[float] = None) -> list:
    """
    Run the full feature pipeline for every driver on the grid.
    Returns a list sorted by composite_score descending.
    """
    all_drivers = get_all_drivers()
    results = [
        compute_composite_score(d["id"], circuit_id, rain_probability)
        for d in all_drivers
    ]
    return sorted(results, key=lambda x: x["composite_score"], reverse=True)
