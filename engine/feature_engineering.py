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
"""

import math
from typing import Optional

from config.settings import FEATURE_WEIGHTS, RECENCY_DECAY, RECENCY_WINDOW
from data.driver_data import get_driver, get_all_drivers, get_drivers_for_team
from data.circuit_data import get_circuit, circuit_favors_team
from data.season_2026 import get_driver_last_n_results, DRIVER_STANDINGS_AFTER_R4

N_DRIVERS = 22
DNF_POSITION_PENALTY = N_DRIVERS + 5  # 25 — worse than last finisher


# ── ELO ────────────────────────────────────────────────────────────────────────

def compute_elo_score(driver_id: str) -> float:
    try:
        raw = get_driver(driver_id)["elo"]
        field = get_all_drivers()
        lo, hi = min(d["elo"] for d in field), max(d["elo"] for d in field)
        return (raw - lo) / (hi - lo + 1e-9)
    except Exception:
        return 0.5


# ── Constructor strength ───────────────────────────────────────────────────────

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
    base = _CONSTRUCTOR_STRENGTH.get(team_id, 0.25)
    try:
        mult = circuit_favors_team(circuit_id, team_id)
    except Exception:
        mult = 1.0
    return min(1.0, max(0.05, base * mult))


# ── Recent form ────────────────────────────────────────────────────────────────

def compute_recent_form_score(driver_id: str, n: int = RECENCY_WINDOW) -> float:
    try:
        results = get_driver_last_n_results(driver_id, n=n)
    except Exception:
        return 0.5
    if not results:
        return 0.5

    total_w, weighted_pos = 0.0, 0.0
    for i, r in enumerate(results):
        w = RECENCY_DECAY ** i
        # FIX: DNF → 25 (worse than last finisher), not 21
        pos = r["position"] if r["position"] is not None else DNF_POSITION_PENALTY
        weighted_pos += w * pos
        total_w += w

    if total_w == 0:
        return 0.5
    avg_pos = weighted_pos / total_w
    return max(0.0, 1.0 - ((avg_pos - 1) / (N_DRIVERS - 1)))


# ── Grid position ──────────────────────────────────────────────────────────────

def compute_grid_position_score(
    driver_id: str,
    actual_grid_pos: Optional[int] = None,
) -> float:
    # NOTE: grid overrides are expected to map P1→1.0 and P20→0.0.
    # Keep this function deterministic for tests and callers.

    
    """
    FIX: v1 always returned 0.5 (neutral), wasting the grid_position feature slot.

    Pre-race mode (no actual_grid_pos):
      Use championship position + qualifying_delta_avg as a proxy.
      Championship leader starts from ~P1, backmarker from ~P18.

    Post-qualifying mode (actual_grid_pos provided):
      Direct inverse mapping: P1 → 1.0, P20 → 0.0.
    """
    if actual_grid_pos is not None:
        # Actual qualifying result — most accurate
        # Treat grid positions as 1..N where 1 is best.
        pos = max(1, min(N_DRIVERS, int(actual_grid_pos)))
        return max(0.0, 1.0 - (pos - 1) / (N_DRIVERS - 1))

    # Pre-race proxy: use championship position + qualifying pace delta
    try:

        driver = get_driver(driver_id)
        standings = {s["driver"]: s["position"] for s in DRIVER_STANDINGS_AFTER_R4}
        # driver_id is expected to match the ids used in standings.
        champ_pos = standings.get(driver_id)
        # If driver data is missing or unusable, fall back to neutral.
        if champ_pos is None:
            champ_pos = 15

        # Guard: if champ_pos becomes non-numeric, fall back.
        try:
            champ_pos = float(champ_pos)
        except Exception:
            champ_pos = 15

        # Quality of grid proxy should be monotonic with championship position.
        # Convert championship position into a baseline grid score.
        # (Lower champ position → higher score)
        base_score = max(0.0, min(1.0, 1.0 - (float(champ_pos) - 1) / (N_DRIVERS - 1)) )



        # Qualifying delta: negative = faster than teammate (in ms)

        # Typical range: -100ms to +100ms. Normalise to [-0.5, +0.5] shift in grid positions
        q_delta = driver.get("qualifying_delta_avg", 0)
        q_shift = q_delta / 200.0  # ±100ms → ±0.5 grid places adjustment (normalised)

        # Use baseline grid score from championship position,
        # then apply a small perturbation based on qualifying delta.
        # Qualifying delta sign convention: negative = faster than teammate.
        # So smaller (more negative) q_delta should increase grid score.

        # Apply modest qualifying influence so the proxy remains stable.
        q_influence = (-q_shift) * 0.15
        score = base_score + q_influence
        return max(0.0, min(1.0, float(score)))


    except Exception:
        return 0.5


# ── Track fit ──────────────────────────────────────────────────────────────────

def compute_track_fit_score(driver_id: str, circuit_id: str) -> float:
    try:
        driver = get_driver(driver_id)
        circuit = get_circuit(circuit_id)
        ctypes = circuit.get("circuit_type", ["balanced"])
        fits = [driver["track_type_fit"].get(ct, 1.0) for ct in ctypes]
        avg = sum(fits) / len(fits)
        return max(0.0, min(1.0, (avg - 0.85) / 0.40))
    except Exception:
        return 0.5


# ── Reliability ────────────────────────────────────────────────────────────────

def compute_reliability_score(driver_id: str) -> float:
    try:
        d = get_driver(driver_id)
        blended = 0.35 * d["dnf_rate_career"] + 0.65 * d["dnf_rate_recent"]
        return 1.0 - min(blended, 1.0)
    except Exception:
        return 0.75


def estimate_dnf_probability(driver_id: str, circuit_id: Optional[str] = None) -> float:
    """
    FIX: Now accepts optional circuit_id for distance-adjusted DNF probability.
    The probability_model applies the distance multiplier on top of this base rate.
    """
    try:
        d = get_driver(driver_id)
        exp = d["experience_races"]
        exp_factor = max(0.0, 0.05 * math.exp(-exp / 40))
        base = 0.4 * d["dnf_rate_career"] + 0.6 * d["dnf_rate_recent"] + exp_factor
        return min(base, 0.45)
    except Exception:
        return 0.05


# ── Weather ────────────────────────────────────────────────────────────────────

def compute_weather_score(driver_id: str, circuit_id: str,
                          rain_probability: Optional[float] = None) -> float:
    try:
        d = get_circuit(circuit_id) if circuit_id else {}
        rain_prob = rain_probability if rain_probability is not None else d.get("rain_probability_typical", 0.2)
        drv = get_driver(driver_id)
        wet_skill = drv["wet_skill"] / 10.0
        delta = wet_skill - 0.75
        raw = 0.5 + (rain_prob * delta * 4.0)
        return max(0.0, min(1.0, raw))
    except Exception:
        return 0.5


# ── Safety car upside ──────────────────────────────────────────────────────────

def compute_safety_car_upside(driver_id: str, circuit_id: str,
                              estimated_grid_pos: Optional[int] = None) -> float:
    try:
        sc_prob = get_circuit(circuit_id).get("safety_car_probability", 0.5)
    except Exception:
        sc_prob = 0.5
    try:
        standings = {s["driver"]: s["position"] for s in DRIVER_STANDINGS_AFTER_R4}
        champ_pos = standings.get(driver_id, 15)
        grid = estimated_grid_pos or min(champ_pos + 2, 20)
        return min(sc_prob * ((grid - 1) / 19.0), 0.8)
    except Exception:
        return 0.25


# ── Teammate delta ─────────────────────────────────────────────────────────────

def compute_teammate_beat_probability(driver_id: str) -> float:
    try:
        d = get_driver(driver_id)
        mates = [x for x in get_drivers_for_team(d["team"]) if x["id"] != driver_id]
    except Exception:
        return 0.5
    if not mates:
        return 0.5

    mate = mates[0]
    q_adv = mate.get("qualifying_delta_avg", 0) - d.get("qualifying_delta_avg", 0)
    f_adv = compute_recent_form_score(driver_id) - compute_recent_form_score(mate["id"])
    raw = 0.5 + (0.60 * q_adv / 200.0 + 0.40 * f_adv) * 0.5
    return max(0.05, min(0.95, raw))


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
    }
    composite = sum(FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in features.items())
    return {
        "driver_id":              driver_id,
        "features":               features,
        "composite_score":        round(composite, 6),
        "dnf_probability":        round(estimate_dnf_probability(driver_id, circuit_id), 4),
        "teammate_beat_probability": round(compute_teammate_beat_probability(driver_id), 4),
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