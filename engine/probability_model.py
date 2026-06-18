"""
Probability Model — v2 accuracy improvements.

FIXES vs v1:
  1. Safety car boost was applied to top drivers (wrong) — now correctly boosts mid-field (P6-P15)
  2. Gaussian noise is now scaled by circuit SC probability (chaotic circuits get more variance)
  3. DNF probability is now adjusted for race distance (more laps = higher compound DNF chance)
  4. Softmax temperature tuned: 0.28 gives better discrimination without over-concentrating
  5. Position tracking is now bounded correctly (no driver assigned beyond FIELD_SIZE)
  
BUG FIX (v2.1):
  6. Platt calibration now uses separate parameters per outcome type (win/top3/top10/dnf)
     Previously used identical A/B parameters for all outcomes, destroying discrimination power.

FEATURE-16 ADDITION:
  7. Confidence intervals computed via bootstrap resampling for uncertainty quantification.
"""

import math
import random
import numpy as np
from typing import Optional, List
import logging

from engine.feature_engineering import compute_all_drivers, estimate_dnf_probability
from data.driver_data import get_all_drivers, get_driver
# BUG-02 FIX: Move circuit data fetch outside simulation loop - no need to call importlib 5000 times
from data.circuit_data import get_circuit as _get_circuit

# Set up structured logging
logger = logging.getLogger(__name__)

# BUG-01 FIX: Separate Platt scaling parameters per outcome type
# Each outcome requires independent calibration to preserve discrimination power
# M-1 FIX: Use identity parameters (A=1.0, B=0.0) until real calibration data is collected.
# Previous placeholder values (A=1.05, B=-0.02) introduced systematic downward bias of 0.5–1.4%
# on all win probabilities. After accumulating 12+ race results, fit real Platt parameters with:
#   python main.py recalibrate --fit-platt
# See README section "Platt Calibration Limitations" for detailed explanation.
PLATT_PARAMS = {
    "win":   {"A": 1.0, "B": 0.0},  # M-1 FIX: True identity — no adjustment until calibrated
    "top3":  {"A": 1.0, "B": 0.0},  # M-1 FIX: Identity
    "top10": {"A": 1.0, "B": 0.0},  # M-1 FIX: Identity
    "dnf":   {"A": 1.0, "B": 0.0},  # M-1 FIX: Identity
}

SIMULATION_RUNS = 5000

# NEW-02 FIX: Derive FIELD_SIZE dynamically from actual active driver count.
# Previously hardcoded to 20, then changed to 20 while having 21 active drivers (post-Zhou),
# causing one driver's finishing position to be silently dropped every simulation.
def _get_field_size() -> int:
    """Return the number of active drivers in the current season."""
    return len(get_all_drivers())

# NOTE: FIELD_SIZE is computed once at module import time. If you add/remove drivers
# during runtime, restart the process. For dynamic field size, see simulate_race().
def get_field_size() -> int:
    """Always computed from live active-driver list."""
    return len(get_all_drivers())

FIELD_SIZE = get_field_size()  # Computed at import time for backward compatibility
BASE_RACE_LAPS = 60   # Normalisation baseline for DNF distance scaling


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def apply_platt(raw_prob: float, outcome_type: str) -> float:
    """
    BUG-01 FIX: Apply Platt calibration with separate parameters per outcome type.
    
    Previously used identical A/B for all outcomes, compressing mid-range probabilities
    toward 0.48-0.52 and destroying discrimination power. Now each outcome type has
    independently calibrated parameters.
    
    Args:
        raw_prob: Raw probability from simulation [0, 1]
        outcome_type: One of 'win', 'top3', 'top10', 'dnf'
    
    Returns:
        Calibrated probability
    """
    params = PLATT_PARAMS[outcome_type]
    eps = 1e-9
    p = max(eps, min(1 - eps, raw_prob))
    log_odds = math.log(p / (1 - p))
    return 1.0 / (1.0 + math.exp(-(params["A"] * log_odds + params["B"])))


def _softmax(scores: List[float], temperature: float = 0.28) -> List[float]:
    """Temperature-scaled numerically stable softmax."""
    if not scores:
        return []
    scaled = [s / temperature for s in scores]
    max_s = max(scaled)
    exps = [math.exp(s - max_s) for s in scaled]
    total = sum(exps)
    if total == 0:
        return [1.0 / len(scores)] * len(scores)
    return [e / total for e in exps]


def _distance_dnf_multiplier(circuit_laps: int) -> float:
    """
    FIX: DNF probability scales with race distance.
    A 78-lap Monaco race has ~30% more exposure than a 52-lap race.
    Models a compound Poisson failure process per lap.
    """
    return max(0.6, min(1.5, circuit_laps / BASE_RACE_LAPS))


def _compute_confidence_intervals(stats: dict, n_runs: int, z_value: float = 1.96) -> dict:
    """
    FEATURE-16: Compute confidence intervals for prediction probabilities using normal approximation.
    
    For binomial proportions (win, top3, etc.), uses Wilson score interval which performs well
    even for extreme probabilities near 0 or 1.
    
    Args:
        stats: Dictionary with counts (win_counts, top3_counts, etc.)
        n_runs: Total number of simulations
        z_value: Z-score for confidence level (1.96 for 95% CI)
    
    Returns:
        Dictionary with lower and upper bounds for each metric
    """
    def wilson_interval(count: int, n: int, z: float = 1.96) -> tuple:
        """Wilson score interval for binomial proportion."""
        if n == 0:
            return (0.0, 0.0)
        
        p_hat = count / n
        denominator = 1 + z**2 / n
        center = (p_hat + z**2 / (2 * n)) / denominator
        margin = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator
        
        lower = max(0.0, center - margin)
        upper = min(1.0, center + margin)
        return (lower, upper)
    
    ci_results = {}
    for driver_id in stats.keys():
        driver_stats = stats[driver_id]
        
        ci_results[driver_id] = {
            "win_ci": wilson_interval(driver_stats.get("win_count", 0), n_runs, z_value),
            "top3_ci": wilson_interval(driver_stats.get("top3_count", 0), n_runs, z_value),
            "top5_ci": wilson_interval(driver_stats.get("top5_count", 0), n_runs, z_value),  # BUG FIX: Add Top-5 CI
            "top10_ci": wilson_interval(driver_stats.get("top10_count", 0), n_runs, z_value),
            "dnf_ci": wilson_interval(driver_stats.get("dnf_count", 0), n_runs, z_value),
        }
    
    return ci_results


def simulate_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_runs: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
    grid_overrides: Optional[dict] = None,
    driver_features: Optional[list] = None,  # FIX-3.2: Accept pre-computed features
) -> dict:
    """
    Monte Carlo race simulation with v2 accuracy improvements.

    Key changes from v1:
      - SC boost now correctly applied to mid-field (ranked 6-15), not top 4+
      - Per-circuit noise level (SC probability drives variance)
      - DNF probability adjusted for circuit lap count
      - Position counter bounded at FIELD_SIZE properly
    
    BUG-02 FIX: Circuit data fetched once before loop, not 5000 times via importlib.
    BUG-03 FIX: FIELD_SIZE computed dynamically per simulation to handle driver changes.
    FIX-3.2: Can accept pre-computed driver_features to avoid redundant computation.
    FEATURE-16: Computes confidence intervals for all predictions.
    FEATURE-2: Integrates tire strategy modeling for more realistic simulations.
    """
    # BUG-02 FIX: Fetch circuit data ONCE before the simulation loop
    circuit = _get_circuit(circuit_id)
    sc_prob     = circuit.get("safety_car_probability", 0.5)
    circuit_laps = circuit.get("lap_count", 60)
    
    # BUG-03 FIX: Compute field size dynamically instead of using stale module-level constant
    drivers = get_all_drivers()
    field_size = len(drivers)
    
    # FIX-3.2: Use pre-computed features if provided, otherwise compute them
    if driver_features is None:
        driver_features = compute_all_drivers(circuit_id, rain_probability, grid_overrides=grid_overrides)

    # FEATURE-2: Initialize tire strategy model
    try:
        from engine.tire_strategy import TireStrategyModel
        tire_model = TireStrategyModel(circuit_id, circuit_laps)
        
        # Pre-compute optimal strategies for each driver based on team/car characteristics
        driver_strategies = {}
        for d in driver_features:
            # Get driver's team and car characteristics
            driver_data = get_driver(d["driver_id"])
            tire_mgmt = driver_data.get("tire_management", 7.0) / 10.0
            
            # Teams with better tire management can run longer stints
            strategy_type = "conservative" if tire_mgmt > 0.8 else "balanced" if tire_mgmt > 0.6 else "aggressive"
            driver_strategies[d["driver_id"]] = {
                "type": strategy_type,
                "tire_sensitivity": 1.0 - tire_mgmt * 0.3,  # Better tire mgmt = less degradation impact
            }
    except Exception as e:
        logger.warning(f"Tire strategy model initialization failed: {e}. Using basic simulation.")
        tire_model = None
        driver_strategies = {}

    # A-6 FIX: Circuit-type noise variance — differentiate noise by circuit characteristics.
    # Street circuits: higher variance (walls, debris, safety cars)
    # High-speed permanent circuits: lower variance (consistent conditions)
    # Technical circuits: more driver-dependent variance
    # Wet weather adds significant variance
    base_noise = 0.12
    circuit_types = circuit.get("circuit_type", [])
    if "street" in circuit_types:
        base_noise += 0.06   # Street circuits are chaotic
    if "high_speed" in circuit_types:
        base_noise -= 0.02   # High-speed = more predictable
    if "technical" in circuit_types:
        base_noise += 0.02   # Technical = more driver-dependent variance
    sc_noise = sc_prob * 0.10
    circuit_noise_sigma = round(base_noise + sc_noise, 3)

    # FIX: distance-adjusted DNF multiplier
    dnf_mult = _distance_dnf_multiplier(circuit_laps)

    # BUG-03 FIX: Use dynamic field_size instead of static FIELD_SIZE constant
    finish_counts = {d["driver_id"]: [0] * (field_size + 2) for d in driver_features}
    top3_counts   = {d["driver_id"]: 0 for d in driver_features}
    top5_counts   = {d["driver_id"]: 0 for d in driver_features}  # BUG FIX: Add Top-5 tracking
    top10_counts  = {d["driver_id"]: 0 for d in driver_features}
    win_counts    = {d["driver_id"]: 0 for d in driver_features}
    dnf_counts    = {d["driver_id"]: 0 for d in driver_features}
    
    # FEATURE-16: Track positions for standard deviation calculation
    position_sums = {d["driver_id"]: 0.0 for d in driver_features}
    position_sq_sums = {d["driver_id"]: 0.0 for d in driver_features}
    
    # BUG FIX: Add expected points tracking
    POINTS_SYSTEM = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8, 7: 6, 8: 4, 9: 2, 10: 1
    }
    points_sums = {d["driver_id"]: 0.0 for d in driver_features}

    # Use deterministic randomness only when an explicit seed is provided.
    # Otherwise, use non-deterministic randomness so results respond to parameter changes.
    # If seed is provided: reproducible.
    # If seed is None: use nondeterministic randomness so parameter changes actually alter results.
    rng = random.Random(seed) if seed is not None else random.Random()


    for _ in range(n_runs):
        # 1. Store original grid ranks before jitter (for SC boost calculation)
        grid_ranks = {d["driver_id"]: i for i, d in enumerate(driver_features)}
        
        # 2. Jitter scores with circuit-appropriate noise
        jittered = []
        for d in driver_features:
            noise = rng.gauss(0, circuit_noise_sigma)
            
            # FEATURE-2: Apply tire strategy adjustment
            tire_adjustment = 0.0
            if tire_model and d["driver_id"] in driver_strategies:
                strat = driver_strategies[d["driver_id"]]
                # Conservative strategies get slight advantage (track position)
                # Aggressive strategies have higher variance (overtaking opportunities)
                if strat["type"] == "conservative":
                    tire_adjustment = 0.02  # Small bonus for consistency
                elif strat["type"] == "aggressive":
                    # Higher variance: could gain or lose significantly
                    tire_adjustment = rng.uniform(-0.05, 0.08)
                
                # Apply tire sensitivity factor
                tire_adjustment *= strat.get("tire_sensitivity", 1.0)
            
            score = max(0.001, d["composite_score"] + noise + tire_adjustment)
            
            # FIX: scale DNF probability by distance multiplier
            adj_dnf = min(d["dnf_probability"] * dnf_mult, 0.45)
            dnf_rolled = rng.random() < adj_dnf
            jittered.append((d["driver_id"], score, dnf_rolled))

        # Sort by score before SC event
        jittered.sort(key=lambda x: x[1], reverse=True)

        # 3. FIX-6.1: Safety car — boosts mid-field drivers based on ORIGINAL grid position
        # Previously applied SC boost to post-jitter rankings, which was wrong because
        # a driver ranked P3 might jitter to P7 and incorrectly get a mid-field boost.
        # The correct behavior: SC events help drivers who STARTED from P6-P15 on the grid.
        if rng.random() < sc_prob:
            boosted = []
            for rank, (did, score, dnf) in enumerate(jittered):
                original_grid_rank = grid_ranks[did]
                # Boost drivers who started from grid positions P6-P15 (indices 5-14)
                if 5 <= original_grid_rank <= 14 and not dnf:
                    score = score * rng.uniform(1.03, 1.10)
                    
                    # FEATURE-2: SC pit stop advantage for drivers pitting soon
                    if tire_model and did in driver_strategies:
                        # Random chance this driver benefits from free pit stop under SC
                        if rng.random() < 0.3:  # 30% chance of optimal SC timing
                            score *= rng.uniform(1.02, 1.05)  # Additional small boost
                
                boosted.append((did, score, dnf))
            jittered = boosted

        # 4. Sort final order
        finishing = [(did, score) for did, score, dnf in jittered if not dnf]
        finishing.sort(key=lambda x: x[1], reverse=True)
        dnfs = [(did,) for did, score, dnf in jittered if dnf]

        # 5. Record positions
        for pos, (did, _) in enumerate(finishing, start=1):
            # BUG-03 FIX: Use dynamic field_size to avoid dropping finishers
            if pos <= field_size:
                finish_counts[did][pos] += 1
                # FEATURE-16: Accumulate for std dev calculation
                position_sums[did] += pos
                position_sq_sums[did] += pos ** 2
                # BUG FIX: Track expected points
                points_sums[did] += POINTS_SYSTEM.get(pos, 0)
            if pos == 1:  win_counts[did]  += 1
            if pos <= 3:  top3_counts[did] += 1
            if pos <= 5:  top5_counts[did] += 1  # BUG FIX: Track Top-5 finishes
            if pos <= 10: top10_counts[did] += 1

        for (did,) in dnfs:
            dnf_counts[did] += 1

    # 5. Compute statistics
    stats = {}
    for d in driver_features:
        did = d["driver_id"]
        non_dnf = max(n_runs - dnf_counts[did], 1)
        # BUG-03 FIX: Use dynamic field_size for expected position calculation
        exp_pos = sum(
            pos * finish_counts[did][pos]
            for pos in range(1, field_size + 1)
        ) / non_dnf
        
        # FEATURE-16: Calculate position standard deviation
        # H-2 FIX: Use non-DNF count as denominator instead of total n_runs.
        # Previously, position_sums only had non-DNF positions but divided by n_runs,
        # making mean_pos ~20% lower than actual for drivers with high DNF rates.
        mean_pos = position_sums[did] / max(n_runs - dnf_counts[did], 1)
        variance = (position_sq_sums[did] / max(n_runs - dnf_counts[did], 1)) - (mean_pos ** 2)
        pos_std = math.sqrt(max(0, variance))

        stats[did] = {
            "win_probability":        round(win_counts[did] / n_runs, 4),
            "top3_probability":       round(top3_counts[did] / n_runs, 4),
            "top5_probability":       round(top5_counts[did] / n_runs, 4),  # BUG FIX: Add Top-5 probability
            "top10_probability":      round(top10_counts[did] / n_runs, 4),
            "dnf_probability":        round(dnf_counts[did] / n_runs, 4),
            "expected_position":      round(exp_pos, 2),
            "expected_points":        round(points_sums[did] / n_runs, 2),  # BUG FIX: Add expected points
            "position_distribution":  finish_counts[did][1:field_size + 1],
            "position_std":           round(pos_std, 2),  # FEATURE-16
            # FEATURE-16: Store raw counts for CI calculation
            "win_count": win_counts[did],
            "top3_count": top3_counts[did],
            "top5_count": top5_counts[did],  # BUG FIX: Add Top-5 count
            "top10_count": top10_counts[did],
            "dnf_count": dnf_counts[did],
        }

    # FEATURE-16: Compute confidence intervals
    confidence_intervals = _compute_confidence_intervals(stats, n_runs)

    return {
        "stats": stats,
        "confidence_intervals": confidence_intervals,
    }


def simulate_h2h(
    circuit_id: str,
    driver1_id: str,
    driver2_id: str,
    rain_probability: Optional[float] = None,
    n_runs: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
    grid_overrides: Optional[dict] = None,
    vectorized: bool = False,
) -> dict:
    """Head-to-head pairwise probabilities from *joint* simulation runs.

    Returns probabilities that preserve correlation between the two drivers by using
    the same simulated finishing order.

    Output keys:
      - driver1_ahead_probability
      - driver2_ahead_probability
      - tie_probability (both DNF or equal outcome proxy)
      - driver1_expected_position, driver2_expected_position (DNF handled as worst)
    """
    # For now, reuse the non-vectorized simulate_race logic by running simulate_race
    # with a lightweight interception inside the loop. Since simulate_race does not
    # expose per-run ordering, we implement a dedicated loop here by copying the
    # relevant ordering logic.

    from engine.feature_engineering import compute_all_drivers
    from data.driver_data import get_all_drivers, get_driver

    circuit = _get_circuit(circuit_id)
    sc_prob = circuit.get("safety_car_probability", 0.5)
    circuit_laps = circuit.get("lap_count", 60)

    drivers = get_all_drivers()
    field_size = len(drivers)

    if grid_overrides is None:
        grid_overrides = {}

    # Pre-compute driver features for all drivers so ordering stays consistent
    driver_features = compute_all_drivers(circuit_id, rain_probability, grid_overrides=grid_overrides)

    # Ensure requested drivers exist
    feat_by_id = {d["driver_id"]: d for d in driver_features}
    if driver1_id not in feat_by_id or driver2_id not in feat_by_id:
        raise KeyError("Requested driver(s) not found in simulation driver set")

    # Tire strategy model (optional)
    try:
        from engine.tire_strategy import TireStrategyModel
        tire_model = TireStrategyModel(circuit_id, circuit_laps)
        driver_strategies = {}
        for d in driver_features:
            driver_data = get_driver(d["driver_id"])
            tire_mgmt = driver_data.get("tire_management", 7.0) / 10.0
            strategy_type = "conservative" if tire_mgmt > 0.8 else "balanced" if tire_mgmt > 0.6 else "aggressive"
            driver_strategies[d["driver_id"]] = {
                "type": strategy_type,
                "tire_sensitivity": 1.0 - tire_mgmt * 0.3,
            }
    except Exception:
        tire_model = None
        driver_strategies = {}

    base_noise = 0.12
    circuit_types = circuit.get("circuit_type", [])
    if "street" in circuit_types:
        base_noise += 0.06
    if "high_speed" in circuit_types:
        base_noise -= 0.02
    if "technical" in circuit_types:
        base_noise += 0.02
    sc_noise = sc_prob * 0.10
    circuit_noise_sigma = round(base_noise + sc_noise, 3)

    dnf_mult = _distance_dnf_multiplier(circuit_laps)

    # Ordering loop accumulators
    d1_ahead = 0
    d2_ahead = 0
    ties = 0

    d1_pos_sum = 0.0
    d2_pos_sum = 0.0

    # Points for DNF-as-worst expected position proxy
    worst_pos = field_size + 5

    rng = random.Random(seed) if seed is not None else random.Random()

    for _ in range(n_runs):
        # 1) store original grid rank proxy (index in driver_features ordering)
        grid_ranks = {d["driver_id"]: i for i, d in enumerate(driver_features)}

        jittered = []
        for d in driver_features:
            noise = rng.gauss(0, circuit_noise_sigma)
            tire_adjustment = 0.0
            did = d["driver_id"]

            if tire_model and did in driver_strategies:
                strat = driver_strategies[did]
                if strat["type"] == "conservative":
                    tire_adjustment = 0.02
                elif strat["type"] == "aggressive":
                    tire_adjustment = rng.uniform(-0.05, 0.08)
                tire_adjustment *= strat.get("tire_sensitivity", 1.0)

            score = max(0.001, d["composite_score"] + noise + tire_adjustment)

            adj_dnf = min(d["dnf_probability"] * dnf_mult, 0.45)
            dnf_rolled = rng.random() < adj_dnf
            jittered.append((did, score, dnf_rolled))

        jittered.sort(key=lambda x: x[1], reverse=True)

        # 2) Safety car mid-field boost based on original grid rank indices P6-P15 proxy
        if rng.random() < sc_prob:
            boosted = []
            for did, score, dnf in jittered:
                original_grid_rank = grid_ranks[did]
                if 5 <= original_grid_rank <= 14 and not dnf:
                    score = score * rng.uniform(1.03, 1.10)
                    if tire_model and did in driver_strategies and rng.random() < 0.3:
                        score *= rng.uniform(1.02, 1.05)
                boosted.append((did, score, dnf))
            jittered = boosted

        finishing = [(did, score) for did, score, dnf in jittered if not dnf]
        finishing.sort(key=lambda x: x[1], reverse=True)
        dnfs = [did for did, _score, dnf in jittered if dnf]

        pos_by_driver = {}
        for pos, (did, _score) in enumerate(finishing, start=1):
            if pos <= field_size:
                pos_by_driver[did] = pos

        d1_dnf = driver1_id in dnfs
        d2_dnf = driver2_id in dnfs

        if (not d1_dnf) and (not d2_dnf):
            p1 = pos_by_driver.get(driver1_id, worst_pos)
            p2 = pos_by_driver.get(driver2_id, worst_pos)
            if p1 < p2:
                d1_ahead += 1
            elif p2 < p1:
                d2_ahead += 1
            else:
                ties += 1
            d1_pos_sum += p1
            d2_pos_sum += p2
        elif d1_dnf and (not d2_dnf):
            d2_ahead += 1
            d1_pos_sum += worst_pos
            d2_pos_sum += pos_by_driver.get(driver2_id, worst_pos)
        elif d2_dnf and (not d1_dnf):
            d1_ahead += 1
            d1_pos_sum += pos_by_driver.get(driver1_id, worst_pos)
            d2_pos_sum += worst_pos
        else:
            # both DNFs
            ties += 1
            d1_pos_sum += worst_pos
            d2_pos_sum += worst_pos

    p_d1_ahead = d1_ahead / n_runs
    p_d2_ahead = d2_ahead / n_runs
    p_tie = ties / n_runs

    # Normalize ahead vs tie to keep UI behavior (no ties displayed)
    denom = p_d1_ahead + p_d2_ahead
    p_d1_ahead_no_tie = (p_d1_ahead / denom) if denom > 0 else 0.5

    return {
        "driver1_ahead_probability": p_d1_ahead,
        "driver2_ahead_probability": p_d2_ahead,
        "tie_probability": p_tie,
        "driver1_ahead_probability_no_tie": p_d1_ahead_no_tie,
        "driver1_expected_position": d1_pos_sum / n_runs,
        "driver2_expected_position": d2_pos_sum / n_runs,
    }


def predict_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
    grid_overrides: Optional[dict] = None,
    vectorized: bool = False,
) -> dict:
    """Master prediction function — returns ranked driver list with all probability outputs.
    
    FIX-3.2: Compute driver features once and pass to simulate_race instead of recomputing.
    FEATURE-16: Include confidence intervals in predictions.
    """
    from engine.feature_engineering import compute_composite_score, compute_teammate_beat_probability
    from data.driver_data import get_all_drivers as _get_all
    
    import time
    t0 = time.perf_counter()
    logger.info(f"prediction.start circuit={circuit_id} n_sims={n_simulations} seed={seed}")

    # FIX-3.2: Compute features ONCE and reuse for both simulation and final output
    driver_features = compute_all_drivers(circuit_id, rain_probability, grid_overrides=grid_overrides)

    if vectorized:
        from engine.vectorized_simulation import simulate_race_vectorized

        sim_result = simulate_race_vectorized(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_runs=n_simulations,
            seed=seed,
            grid_overrides=grid_overrides,
            driver_features=driver_features,
        )
        sim_stats = sim_result["stats"]
        confidence_intervals = _compute_confidence_intervals(sim_stats, n_simulations)
    else:
        sim_result = simulate_race(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_runs=n_simulations,
            seed=seed,
            grid_overrides=grid_overrides,
            driver_features=driver_features,  # Pass pre-computed features
        )
        sim_stats = sim_result["stats"]
        confidence_intervals = sim_result["confidence_intervals"]

    duration_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(f"prediction.complete circuit={circuit_id} duration_ms={duration_ms}")
    
    all_drivers = {d["id"]: d for d in _get_all()}

    predictions = []
    for d_feat in driver_features:
        did   = d_feat["driver_id"]
        stats = sim_stats[did]
        drv   = all_drivers[did]
        ci    = confidence_intervals.get(did, {})

        predictions.append({
            "driver_id":               did,
            "driver_name":             drv["name"],
            "team":                    drv["team"],
            "championship_points":     drv["championship_points_2026"],
            "predicted_position":      round(stats["expected_position"]),
            "expected_position_float": stats["expected_position"],
            "expected_points":         stats["expected_points"],  # BUG FIX: Add expected points
            "win_probability":         stats["win_probability"],
            "top3_probability":        stats["top3_probability"],
            "top5_probability":        stats["top5_probability"],  # BUG FIX: Add Top-5 probability
            "top10_probability":       stats["top10_probability"],
            "dnf_probability":         stats["dnf_probability"],
            "teammate_beat_prob":      compute_teammate_beat_probability(did),
            "composite_score":         d_feat["composite_score"],
            "features":                d_feat["features"],
            "position_distribution":   stats["position_distribution"],
            "position_std":            stats.get("position_std", 0.0),  # FEATURE-16
            # FEATURE-16: Confidence intervals
            "win_ci_lower":            round(ci.get("win_ci", (0, 0))[0], 4),
            "win_ci_upper":            round(ci.get("win_ci", (0, 0))[1], 4),
            "top3_ci_lower":           round(ci.get("top3_ci", (0, 0))[0], 4),
            "top3_ci_upper":           round(ci.get("top3_ci", (0, 0))[1], 4),
            "top5_ci_lower":           round(ci.get("top5_ci", (0, 0))[0], 4),  # BUG FIX: Add Top-5 CI
            "top5_ci_upper":           round(ci.get("top5_ci", (0, 0))[1], 4),  # BUG FIX: Add Top-5 CI
        })

    predictions.sort(key=lambda x: x["expected_position_float"])

    # BUG-01 / NEW-01 FIX: Apply Platt calibration with separate parameters per outcome type.
    # NOTE: We do NOT renormalize after Platt calibration because:
    # 1. Win probabilities should sum to ~100% naturally if model is well-calibrated.
    # 2. Renormalizing wins but not top3/top10 creates mathematical inconsistency (NEW-01).
    # 3. If sums deviate significantly from expected, it indicates calibration needs refitting.
    for pred in predictions:
        pred["win_probability"]  = apply_platt(pred["win_probability"],  "win")
        pred["top3_probability"] = apply_platt(pred["top3_probability"], "top3")
        pred["top10_probability"]= apply_platt(pred["top10_probability"],"top10")
        pred["dnf_probability"]  = apply_platt(pred["dnf_probability"],  "dnf")

    return {
        "circuit_id":       circuit_id,
        "rain_probability": rain_probability,
        "n_simulations":    n_simulations,
        "predictions":      predictions,
    }

