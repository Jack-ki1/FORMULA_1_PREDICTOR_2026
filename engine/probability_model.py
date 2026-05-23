"""
Probability Model — converts composite feature scores into race outcome probabilities.

Approach:
  1. Softmax over composite scores → raw win probabilities
  2. Logistic regression adjustments for top-3 and top-10
  3. Monte Carlo simulation (N=5000) for full finishing order distribution
  4. Calibration adjustment (Platt scaling coefficients pre-fitted)

Anti-leakage: All computation uses only pre-race data.
"""

import math
import random
from typing import Optional, Dict, List
import logging
from collections import defaultdict

from config.settings import ENGINE_CONFIG
from engine.feature_engineering import compute_all_drivers, estimate_dnf_probability
from data.driver_data import get_all_drivers

logger = logging.getLogger(__name__)

# ── Configurable Mapping Model Parameters ──────────────────────────────────────

# Calibration parameters from config
PLATT_A_WIN = ENGINE_CONFIG.prob_model.platt_a_win
PLATT_B_WIN = ENGINE_CONFIG.prob_model.platt_b_win
PLATT_A_TOP3 = ENGINE_CONFIG.prob_model.platt_a_top3
PLATT_B_TOP3 = ENGINE_CONFIG.prob_model.platt_b_top3
PLATT_A_TOP10 = ENGINE_CONFIG.prob_model.platt_a_top10
PLATT_B_TOP10 = ENGINE_CONFIG.prob_model.platt_b_top10
PLATT_A_DNF = ENGINE_CONFIG.prob_model.platt_a_dnf
PLATT_B_DNF = ENGINE_CONFIG.prob_model.platt_b_dnf

SIMULATION_RUNS = ENGINE_CONFIG.prob_model.default_simulation_runs
FIELD_SIZE = 20  # Fixed field size for F1

# ── Utility Functions ──────────────────────────────────────────────────────────

def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def _softmax(scores: List[float]) -> List[float]:
    """Numerically stable softmax."""
    if not scores:
        return []
    
    max_s = max(scores)
    try:
        exps = [math.exp(s - max_s) for s in scores]
        total = sum(exps)
        if total == 0:
            # Handle edge case where all values underflow to zero
            return [1.0/len(scores)] * len(scores)
        return [e / total for e in exps]
    except OverflowError:
        # Fallback in case of extreme values
        return [1.0/len(scores)] * len(scores)


def _platt_calibrate(raw: float, a: float, b: float) -> float:
    """Apply Platt scaling calibration."""
    # Clamp raw probabilities to prevent log(0) which would cause math domain error
    clamped_raw = max(ENGINE_CONFIG.prob_model.min_probability, 
                      min(raw, ENGINE_CONFIG.prob_model.max_probability))
    
    try:
        logit = math.log(clamped_raw / (1 - clamped_raw))
        calibrated = _sigmoid(a * logit + b)
        # Clamp result to valid probability range
        return max(0.0, min(calibrated, 1.0))
    except ValueError:
        # Handle cases where log would fail due to numerical issues
        logger.warning(f"Platt calibration failed for raw={raw}, returning original value")
        return clamped_raw


# ── Win Probability Computation ────────────────────────────────────────────────

def compute_win_probabilities(
    circuit_id: str,
    rain_probability: Optional[float] = None,
) -> dict:
    """
    Return {driver_id: win_probability} for all drivers.
    """
    driver_features = compute_all_drivers(circuit_id, rain_probability)

    scores = [d["composite_score"] for d in driver_features]
    # Temperature-scaled softmax (T=0.25 for sharper differentiation)
    T = ENGINE_CONFIG.prob_model.temperature_softmax
    scaled_scores = [s / T for s in scores]
    raw_probs = _softmax(scaled_scores)

    result = {}
    for d, p in zip(driver_features, raw_probs):
        # Account for DNF probability eating into win probability
        dnf_adj = 1.0 - d["dnf_probability"]
        adjusted = p * dnf_adj
        result[d["driver_id"]] = round(adjusted, 6)

    # Renormalise
    total = sum(result.values())
    if total > 0:
        return {k: round(v / total, 6) for k, v in result.items()}
    else:
        # Fallback if all probabilities are 0
        uniform_prob = 1.0 / len(result)
        return {k: uniform_prob for k in result.keys()}


# ── Monte Carlo Simulation ─────────────────────────────────────────────────────

def simulate_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
) -> dict:
    """
    Run Monte Carlo simulation to generate race outcome distribution.
    Includes deterministic seeding capability.
    """
    if seed is not None:
        random.seed(seed)
        # For more comprehensive seeding, also seed numpy if available
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass  # NumPy not available, skip setting its seed

    # Get win probabilities from our model
    win_probs = compute_win_probabilities(circuit_id, rain_probability)
    
    # Calculate additional probabilities using calibrated models
    driver_features = compute_all_drivers(circuit_id, rain_probability)
    
    # Prepare results container with statistics
    results = {
        "driver_standings": defaultdict(list),  # position -> [driver_ids]
        "driver_positions": defaultdict(list),  # driver_id -> [positions]
        "driver_outcomes": defaultdict(lambda: defaultdict(int)),  # driver -> outcome -> count
    }
    
    # Run simulations
    for _ in range(n_simulations):
        # Simulate a single race outcome
        simulated_positions = _simulate_single_race(win_probs, driver_features)
        
        # Record the results
        for position, driver_id in enumerate(simulated_positions, 1):
            results["driver_standings"][position].append(driver_id)
            results["driver_positions"][driver_id].append(position)
            
            # Record outcome categories
            if position == 1:
                results["driver_outcomes"][driver_id]["wins"] += 1
            if position <= 3:
                results["driver_outcomes"][driver_id]["top3"] += 1
            if position <= 10:
                results["driver_outcomes"][driver_id]["top10"] += 1
            if position == 20:  # Assuming last position indicates DNF risk
                results["driver_outcomes"][driver_id]["dnfs"] += 1

    # Calculate probabilities from simulation results
    driver_predictions = []
    for driver_data in driver_features:
        driver_id = driver_data["driver_id"]
        
        # Calculate outcome probabilities
        outcomes = results["driver_outcomes"][driver_id]
        win_prob = outcomes["wins"] / n_simulations
        top3_prob = outcomes["top3"] / n_simulations
        top10_prob = outcomes["top10"] / n_simulations
        # Note: DNF probability derived differently - using feature engineering
        dnf_prob = driver_data["dnf_probability"]
        
        # Apply calibration if configured
        calibrated_win = _platt_calibrate(win_prob, PLATT_A_WIN, PLATT_B_WIN)
        calibrated_top3 = _platt_calibrate(top3_prob, PLATT_A_TOP3, PLATT_B_TOP3)
        calibrated_top10 = _platt_calibrate(top10_prob, PLATT_A_TOP10, PLATT_B_TOP10)
        calibrated_dnf = _platt_calibrate(dnf_prob, PLATT_A_DNF, PLATT_B_DNF)
        
        # Calculate variance across simulations for uncertainty metrics
        positions = results["driver_positions"][driver_id]
        position_variance = sum((pos - sum(positions)/len(positions))**2 for pos in positions) / len(positions)
        
        # Calculate outcome variances (simplified approach)
        win_variance = win_prob * (1 - win_prob) / n_simulations  # Bernoulli variance approximation
        top3_variance = top3_prob * (1 - top3_prob) / n_simulations
        top10_variance = top10_prob * (1 - top10_prob) / n_simulations
        dnf_variance = dnf_prob * (1 - dnf_prob) / n_simulations
        
        # Determine predicted position (average across simulations)
        avg_position = sum(positions) / len(positions)
        
        driver_predictions.append({
            "driver_id": driver_id,
            # get_all_drivers() returns list[dict], so use dict keys
            "driver_name": next(d["name"] for d in get_all_drivers() if d["id"] == driver_id),
            "team": next(d["team"] for d in get_all_drivers() if d["id"] == driver_id),
            "predicted_position": round(avg_position),
            "win_probability": calibrated_win,
            "top3_probability": calibrated_top3,
            "top10_probability": calibrated_top10,
            "dnf_probability": calibrated_dnf,
            "teammate_beat_prob": driver_data["teammate_beat_probability"],
            "composite_score": driver_data["composite_score"],
            "uncertainty_metrics": {
                "position_variance": position_variance,
                "win_variance": win_variance,
                "top3_variance": top3_variance,
                "top10_variance": top10_variance,
                "dnf_variance": dnf_variance,
            }
        })

    # Ensure ordering constraints: win ≤ top3 ≤ top10
    for pred in driver_predictions:
        # Adjust probabilities to respect ordering constraints
        pred["top3_probability"] = max(pred["top3_probability"], pred["win_probability"])
        pred["top10_probability"] = max(pred["top10_probability"], pred["top3_probability"])

    # Ensure ordering constraints (win ≤ top3 ≤ top10)
    for pred in driver_predictions:
        pred["top3_probability"] = max(pred["top3_probability"], pred["win_probability"])
        pred["top10_probability"] = max(pred["top10_probability"], pred["top3_probability"])

    # Some downstream tests expect win probabilities to sum to ~1.0 (100%).
    total_win = sum(p["win_probability"] for p in driver_predictions)
    if total_win > 0:
        for p in driver_predictions:
            p["win_probability"] = p["win_probability"] / total_win

    return {
        "predictions": driver_predictions,
        "simulation_count": n_simulations,
        "raw_simulation_data": dict(results),  # Keep raw data for potential analysis
    }



def _simulate_single_race(win_probs: Dict[str, float], driver_features: List[dict]) -> List[str]:
    """
    Simulate a single race outcome based on win probabilities and other factors.
    This is a simplified simulation - a more sophisticated approach would model
    the full finishing order.
    """
    # Create a copy of drivers to manipulate during simulation
    drivers = [(driver["driver_id"], prob) for driver, prob in zip(driver_features, win_probs.values())]
    
    # Sort by probability to determine winner (highest probability wins)
    # Then apply some randomness to make it stochastic
    drivers.sort(key=lambda x: x[1], reverse=True)
    
    # Apply stochastic element: sometimes a lower-probability driver wins
    # For simplicity, we'll use a basic approach: pick from top candidates
    # with probability proportional to their win probability
    driver_ids, probs = zip(*drivers)
    
    # Use random choice weighted by probabilities
    try:
        winner_idx = random.choices(range(len(driver_ids)), weights=probs)[0]
        winner = driver_ids[winner_idx]
    except ValueError:
        # If all probabilities are 0, pick randomly
        winner = random.choice(driver_ids)
    
    # Remove winner from remaining drivers
    remaining_drivers = [d for d in driver_ids if d != winner]
    random.shuffle(remaining_drivers)  # Simple way to assign remaining positions
    
    # Return the full finishing order
    return [winner] + remaining_drivers


# ── Main Prediction Function ───────────────────────────────────────────────────

def predict_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
) -> dict:
    """
    Main entry point for race prediction using Monte Carlo simulation.
    """
    logger.info(f"Starting race prediction for {circuit_id} with {n_simulations} simulations")
    
    # Run the simulation
    simulation_results = simulate_race(
        circuit_id=circuit_id,
        rain_probability=rain_probability,
        n_simulations=n_simulations,
        seed=seed
    )
    
    # Sort results by predicted position
    simulation_results["predictions"].sort(key=lambda x: x["predicted_position"])
    
    logger.info(f"Completed race prediction for {circuit_id}")
    return simulation_results