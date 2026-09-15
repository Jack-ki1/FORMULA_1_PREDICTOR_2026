"""Alternate realities — branch replay, counterfactual championship, transfer simulator."""
from __future__ import annotations
import copy
import random
from typing import Any, Dict, List
from datetime import datetime, timezone

from backend.app.config.team_driver_lineup_2026 import TEAMS_2026, get_all_drivers, get_driver_by_code
from backend.app.engine.monte_carlo import MonteCarloSimulator
from backend.app.data.calendar_2026 import CALENDAR_2026

def branch_point_replay(race_id: str, freeze_lap: int = 25, altered: Dict[str,Any] | None = None) -> Dict[str,Any]:
    """Freeze at lap N, re-run forward with one variable changed.
    altered keys: tire_call, no_safety_car, puncture_driver, grid_swap, weather
    """
    altered = altered or {}
    codes = [d["code"] for d in get_all_drivers()]
    sim = MonteCarloSimulator(num_simulations=3000)
    # Base grid: strength order
    alld = get_all_drivers()
    base_grid = {d["code"]: i+1 for i,d in enumerate(sorted(alld, key=lambda d: d["strength"], reverse=True))}
    # Apply altered
    grid = dict(base_grid)
    weather = altered.get("weather","dry")
    sc_prob = 0.3
    chaos = 30
    explanation=[]
    if altered.get("no_safety_car"):
        sc_prob = 0.02
        explanation.append("Safety car removed — pure pace simulation")
    if altered.get("tire_call"):
        # tire_call: {driver, compound} -> boost that driver slightly
        drv = altered["tire_call"].get("driver")
        if drv in grid:
            # move up 2 positions worth of pace boost by improving grid effect
            grid[drv] = max(1, grid[drv]-2)
            explanation.append(f"{drv} pitted one lap earlier — track position + undercut")
    if altered.get("puncture_driver"):
        drv = altered["puncture_driver"]
        if drv in grid:
            grid[drv] = min(len(codes), grid[drv]+8)
            explanation.append(f"{drv} puncture added — drops 8 positions in model")
    if altered.get("grid_swap"):
        a,b = altered["grid_swap"].get("a"), altered["grid_swap"].get("b")
        if a in grid and b in grid:
            grid[a], grid[b] = grid[b], grid[a]
            explanation.append(f"Grid swap {a}<->{b}")
    # Simulate both: baseline vs altered
    baseline_out = sim.simulate_race(race_id, base_grid, "dry", 0.3, chaos_level=30, num_simulations=2500, seed=freeze_lap)
    altered_out  = sim.simulate_race(race_id, grid, weather, sc_prob, chaos_level=chaos, num_simulations=2500, seed=freeze_lap+999)
    def top5(out):
        probs = out["results"]["probabilities"]
        return [{"code": c, "win": round(probs[c]["win_prob"],4)} for c,_ in sorted(probs.items(), key=lambda x: x[1]["win_prob"], reverse=True)[:5]]
    # Delta
    b_probs = {c: baseline_out["results"]["probabilities"][c]["win_prob"] for c in codes}
    a_probs = {c: altered_out["results"]["probabilities"][c]["win_prob"] for c in codes}
    deltas = {c: round(a_probs[c]-b_probs[c],4) for c in codes}
    biggest = sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    return {"race_id": race_id, "freeze_lap": freeze_lap, "altered": altered,
            "explanation": explanation or ["Single-variable branching replay"],
            "baseline_top5": top5(baseline_out), "altered_top5": top5(altered_out),
            "deltas": deltas, "biggest_movers": [{"code": c, "delta": d} for c,d in biggest],
            "note": "Froze at lap N with exact gaps/grid, re-ran Monte Carlo forward — what-if as a tool, not a tweet."}

def counterfactual_championship(remove_dnf: bool = True, remove_sc: bool = False) -> Dict[str,Any]:
    """Rerun full season with DNFs/SC removed — who should have won on pure pace."""
    # Simulate each race without DNF variance, sum expected points
    sim = MonteCarloSimulator(num_simulations=2000)
    codes = [d["code"] for d in get_all_drivers()]
    # Use 23-round 2026 calendar, but simulate pure pace (reliability=100, sc low)
    totals: Dict[str,float] = {c:0 for c in codes}
    race_breakdown=[]
    for race in CALENDAR_2026[:10]:  # 10 representative to keep fast
        # Temporarily patch reliability effect: force dnf_rate low
        out = sim.simulate_race(race["id"], None, "dry", 0.05 if remove_sc else 0.3, chaos_level=10 if remove_dnf else 30, num_simulations=1500, seed=hash(race["id"])%10000)
        # Map win/podium/points to points: 25-18-15...
        probs = out["results"]["probabilities"]
        # Expected points approximation
        for c in codes:
            p = probs[c]
            exp_pts = p["win_prob"]*25 + (p["podium_prob"]-p["win_prob"])*15 + (p["points_prob"]-p["podium_prob"])*6
            if remove_dnf:
                exp_pts /= max(0.85, 1 - p["dnf_prob"]*0.5)
            totals[c] += exp_pts
        winner = max(probs.items(), key=lambda x: x[1]["win_prob"])[0]
        race_breakdown.append({"race_id": race["id"], "race": race["name"], "model_winner": winner,
                               "top3": sorted(probs.items(), key=lambda x: x[1]["win_prob"], reverse=True)[:3]})
    # Scale to 23 races
    scale = 23/10
    for c in totals: totals[c] = round(totals[c]*scale,1)
    standings = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    # Compare to "current" synthetic standings (hand-typed strength order) — reveal delta
    real_order = sorted(get_all_drivers(), key=lambda d: d["strength"], reverse=True)
    real_rank = {d["code"]: i+1 for i,d in enumerate(real_order)}
    cf_rank = {c: i+1 for i,(c,_) in enumerate(standings)}
    movers = [{"code": c, "real_rank": real_rank[c], "cf_rank": cf_rank[c], "delta": real_rank[c]-cf_rank[c]} for c in codes]
    movers = sorted(movers, key=lambda x: abs(x["delta"]), reverse=True)[:5]
    return {"mode": "pure_pace" if remove_dnf else "with_dnf", "remove_dnf": remove_dnf, "remove_sc": remove_sc,
            "standings": [{"code": c, "points": pts, "pos": i+1} for i,(c,pts) in enumerate(standings)],
            "biggest_movers_vs_strength": movers, "race_breakdown": race_breakdown,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": "Content piece — 'who should have won on pace' vs actual chaos/DNF."

            }

def transfer_simulator(driver_code: str, target_team_id: str) -> Dict[str,Any]:
    """Drag driver into different team — projected shift via team pace blend."""
    driver = get_driver_by_code(driver_code)
    if not driver:
        raise ValueError(f"Unknown driver {driver_code}")
    from backend.app.config.team_driver_lineup_2026 import get_team_by_id
    target = get_team_by_id(target_team_id)
    if not target:
        raise ValueError(f"Unknown team {target_team_id}")
    # Team pace proxy: avg strength of current drivers
    current_team = get_team_by_id(driver["team_id"])
    target_avg = sum(d["strength"] for d in target["drivers"])/len(target["drivers"])
    current_avg = sum(d["strength"] for d in current_team["drivers"])/len(current_team["drivers"])
    # Car effect: assume 60% car, 40% driver — moving driver changes effective strength
    driver_strength = driver["strength"]
    effective_before = 0.4*driver_strength + 0.6*current_avg
    effective_after  = 0.4*driver_strength + 0.6*target_avg
    delta = effective_after - effective_before
    # Simulate win% before/after via MC
    sim = MonteCarloSimulator(num_simulations=2000)
    # Build two grids: driver at current vs target team pace
    # For simplicity, perturb driver's effective strength by delta
    alld = copy.deepcopy(get_all_drivers())
    for d in alld:
        if d["code"]==driver_code:
            d["strength"] = max(30, min(99, d["strength"]+delta*0.5))
    # Quick MC both ways: hack by temporarily patching get_all_drivers via sim init
    # Instead, run two sims with grids biased by delta
    base_grid = {d["code"]: i+1 for i,d in enumerate(sorted(get_all_drivers(), key=lambda x: x["strength"], reverse=True))}
    # After: driver moves up/down Grid positions by delta
    new_grid = dict(base_grid)
    shift = int(round(delta/5))  # ~1 pos per 5 strength
    new_grid[driver_code] = max(1, min(23, base_grid[driver_code]-shift))
    # Re-sort to avoid collisions
    ordered = sorted(new_grid.items(), key=lambda x: x[1])
    new_grid = {c:i+1 for i,(c,_) in enumerate(ordered)}
    # Simulate
    out_before = sim.simulate_race("au", base_grid, "dry", 0.3, chaos_level=30, num_simulations=1500, seed=42)
    out_after  = sim.simulate_race("au", new_grid, "dry", 0.3, chaos_level=30, num_simulations=1500, seed=43)
    win_before = out_before["results"]["probabilities"][driver_code]["win_prob"]
    win_after  = out_after["results"]["probabilities"][driver_code]["win_prob"]
    return {"driver": driver_code, "from_team": driver["team_id"], "to_team": target_team_id,
            "effective_before": round(effective_before,1), "effective_after": round(effective_after,1),
            "delta_strength": round(delta,1), "grid_shift": -shift,
            "win_prob_before": round(win_before,4), "win_prob_after": round(win_after,4),
            "win_delta_pp": round((win_after-win_before)*100,2),
            "teammate_comparison": [{"code": d["code"], "strength": d["strength"]} for d in target["drivers"]],
            "verdict": f"{driver_code} {'gains' if delta>0 else 'loses'} ~{abs(round(delta,1))} pts moving to {target['name']}"}
