"""
ChampionshipProjection — run the existing Monte Carlo engine across the
*remaining* calendar to produce P(driver wins the title).

Not new modelling machinery: it reuses MonteCarloSimulator (already the
production path) plus the calendar and results already on disk. It is simply a
different time horizon — season-to-date plus every remaining round, rather than
a single race. (modify.md section 5)
"""
import logging
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)

POINTS_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]  # P1..P10


def _season_to_date() -> Dict[str, int]:
    """Points already banked per driver, from the recorded standings."""
    try:
        from backend.app.data.season_2026 import DRIVER_STANDINGS_2026
        return {row["driver_code"]: int(row.get("points", 0)) for row in DRIVER_STANDINGS_2026}
    except Exception as e:
        logger.warning("season-to-date load failed: %s", e)
        return {}


def _remaining_rounds() -> List[Dict[str, Any]]:
    try:
        from backend.app.data.calendar_2026 import CALENDAR_2026
        from backend.app.data.season_2026 import SEASON_2026_RESULTS
        done = set(SEASON_2026_RESULTS.get("results", {}).keys())
        return [r for r in CALENDAR_2026 if r.get("round") not in done]
    except Exception as e:
        logger.warning("remaining calendar load failed: %s", e)
        return []


def project_championship(simulations: int = 2000, seed: int = 42) -> Dict[str, Any]:
    """Simulate every remaining round to estimate title probabilities."""
    from backend.app.config.constants import grid_size
    from backend.app.config.team_driver_lineup_2026 import get_all_drivers
    from backend.app.engine.monte_carlo import MonteCarloSimulator

    sims = max(200, min(int(simulations or 2000), 20000))
    drivers = get_all_drivers()
    codes = [d["code"] for d in drivers]
    index = {c: i for i, c in enumerate(codes)}

    base_points = _season_to_date()
    banked = np.array([float(base_points.get(c, 0)) for c in codes])

    remaining = _remaining_rounds()
    if not remaining:
        order = sorted(codes, key=lambda c: banked[index[c]], reverse=True)
        return {
            "status": "season_complete",
            "remaining_rounds": 0,
            "samples": 0,
            "title_probability": {c: (1.0 if i == 0 else 0.0) for i, c in enumerate(order)},
            "expected_points": {c: float(banked[index[c]]) for c in codes},
            "ranked": order,
            "projected_champion": order[0] if order else None,
            "note": "no remaining rounds — projection is the current standings",
        }

    grid = {d["code"]: i + 1 for i, d in enumerate(
        sorted(drivers, key=lambda x: x["strength"], reverse=True)
    )}

    # One Monte Carlo call per remaining round, reusing the production simulator.
    totals = np.tile(banked, (sims, 1))
    sim = MonteCarloSimulator(num_simulations=sims)

    for race in remaining:
        race_id = race.get("id")
        sc_prob = (race.get("base_sc", 30)) / 100.0
        out = sim.simulate_race(race_id, grid, "dry", sc_prob, 30, sims, seed=seed)
        probs = out["results"]["probabilities"]
        # Per-round finishing order: rank by expected position, then perturb so
        # each simulated round differs (a simulation must not replay one order).
        rng = np.random.default_rng(seed + int(race.get("round", 0)))
        strength = np.array([probs[c]["avg_position"] for c in codes], dtype=float)
        noise = rng.normal(0, 1.2, size=(sims, len(codes)))
        order = np.argsort(strength[None, :] + noise, axis=1)
        pts = np.zeros((sims, len(codes)))
        for slot, points in enumerate(POINTS_TABLE):
            pts[np.arange(sims), order[:, slot]] += points
        totals += pts

    winners = np.argmax(totals, axis=1)
    title_prob = {c: float(np.mean(winners == index[c])) for c in codes}
    expected = {c: float(np.mean(totals[:, index[c]])) for c in codes}
    ranked = sorted(codes, key=lambda c: title_prob[c], reverse=True)

    return {
        "status": "projected",
        "remaining_rounds": len(remaining),
        "remaining_race_ids": [r.get("id") for r in remaining],
        "samples": sims,
        "title_probability": title_prob,
        "expected_points": {c: round(expected[c], 1) for c in codes},
        "ranked": ranked,
        "projected_champion": ranked[0] if ranked else None,
        "points_table_used": POINTS_TABLE,
        "note": ("drawn from the production Monte Carlo path; sprint points and "
                 "reliability are not modelled per-round here"),
        "grid_size": grid_size(),
    }
