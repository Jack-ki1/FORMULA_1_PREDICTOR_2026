"""Live extended — win-probability over time + timeline + mid-race re-sim."""
from __future__ import annotations
import random
import time
from typing import Any, Dict, List
from datetime import datetime, timezone

from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.engine.monte_carlo import MonteCarloSimulator
from backend.app.data.calendar_2026 import get_race_by_id
from backend.app.data.circuit_data import CIRCUITS


def _grid_for_race(race_id: str, grid_positions: Dict[str,int] | None) -> Dict[str,int]:
    codes = [d["code"] for d in get_all_drivers()]
    if grid_positions:
        return MonteCarloSimulator._complete_grid(grid_positions, codes)
    # fallback strength order
    alld = get_all_drivers()
    ordered = sorted(alld, key=lambda d: d["strength"], reverse=True)
    return {d["code"]: i+1 for i,d in enumerate(ordered)}

def simulate_win_prob_curve(race_id: str, grid_positions: Dict[str,int] | None = None,
                            weather: str="dry", gaps: List[float] | None = None,
                            laps_total: int = 58, num_points: int = 20) -> Dict[str,Any]:
    """Return win-probability evolution over laps — backbone for SSE live graph.
    gaps: optional mid-race gaps to leader (inject as strength bias).
    """
    codes = [d["code"] for d in get_all_drivers()]
    sim = MonteCarloSimulator(num_simulations=3000)
    grid = _grid_for_race(race_id, grid_positions)
    race_info = get_race_by_id(race_id) or {"base_sc":30}
    sc_prob = race_info.get("base_sc",30)/100
    # If gaps supplied, bias strength: leader gets boost, backmarkers penalised
    # For curve, we simulate at lap fractions: early chaos high, late chaos low
    points=[]
    for i in range(num_points):
        lap = int((i+1)/num_points * laps_total)
        # chaos decays as race progresses, weather influence rises mid-race
        chaos = max(5, 50 - i*2)
        if gaps and i >= num_points//2:
            # inject gap bias: map gaps to position bias
            # gaps sorted ascending = leader first
            biased_grid = {}
            if len(gaps) >= len(codes):
                order = sorted(codes, key=lambda c: gaps[codes.index(c)] if codes.index(c)<len(gaps) else 999)
                biased_grid = {c: pos for pos,c in enumerate(order,1)}
            else:
                biased_grid = grid
            out = sim.simulate_race(race_id, biased_grid, weather, sc_prob, chaos_level=chaos, num_simulations=1500, seed=lap*100)
        else:
            out = sim.simulate_race(race_id, grid, weather, sc_prob, chaos_level=chaos, num_simulations=1500, seed=lap*100)
        probs = {c: out["results"]["probabilities"][c]["win_prob"] for c in codes}
        top3 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
        points.append({"lap": lap, "probs": probs, "leader": top3[0][0], "leader_prob": round(top3[0][1],4),
                       "top3": [{"code": c, "p": round(p,4)} for c,p in top3], "confidence": round(out["results"]["confidence"],3)})
    return {"race_id": race_id, "laps_total": laps_total, "points": points,
            "generated_at": datetime.now(timezone.utc).isoformat()}

def probability_timeline(race_id: str) -> Dict[str,Any]:
    """FP1 -> Quali -> Grid -> Lights out story — animated line data."""
    stages = ["FP1","FP2","FP3","Q1","Q2","Q3","Grid","Lap 1","Mid-race","Chequered"]
    codes = [d["code"] for d in get_all_drivers()]
    sim = MonteCarloSimulator(num_simulations=2000)
    grid_base = _grid_for_race(race_id, None)
    # Each stage has different noise / grid influence
    timeline=[]
    for idx, stage in enumerate(stages):
        chaos = [40,35,30,35,30,25,20,30,35,15][idx]
        weather = "dry"
        if stage in ("Q1","Q2"): weather = "mixed" if random.random()<0.15 else "dry"
        out = sim.simulate_race(race_id, grid_base, weather, 0.3, chaos_level=chaos, num_simulations=1500, seed=1000+idx)
        probs = {c: round(out["results"]["probabilities"][c]["win_prob"],4) for c in codes}
        timeline.append({"stage": stage, "probs": probs, "confidence": round(out["results"]["confidence"],3)})
    return {"race_id": race_id, "stages": [s["stage"] for s in timeline], "timeline": timeline,
            "note": "How win% evolves from practice to flag — not a single number, a story."}

def mid_race_resim(race_id: str, session_key: str = "", gaps: Dict[str,float] | None = None,
                   pit_events: List[Dict[str,Any]] | None = None,
                   sc_deployed: bool = False) -> Dict[str,Any]:
    """Re-simulate from current state: gaps + pit + SC.
    Called by SSE every event — milliseconds.
    """
    codes = [d["code"] for d in get_all_drivers()]
    grid = _grid_for_race(race_id, gaps if gaps and all(isinstance(v,int) for v in gaps.values()) else None)
    # Convert gaps (seconds to leader) to bias
    weather="dry"
    sc_prob = 0.6 if sc_deployed else 0.25
    chaos = 35 if sc_deployed else 30
    if gaps:
        # Build bias: smaller gap = stronger effective strength
        # Use inverse gap as grid tiebreaker
        sorted_by_gap = sorted(gaps.items(), key=lambda x: x[1])
        biased_grid = {code: pos for pos,(code,_) in enumerate(sorted_by_gap,1)}
        # fill missing
        for c in codes:
            if c not in biased_grid:
                biased_grid[c] = len(biased_grid)+1
        grid = biased_grid
    sim = MonteCarloSimulator(num_simulations=2500)
    out = sim.simulate_race(race_id, grid, weather, sc_prob, chaos_level=chaos, num_simulations=2500)
    probs = {c: out["results"]["probabilities"][c] for c in codes}
    sorted_win = sorted(probs.items(), key=lambda x: x[1]["win_prob"], reverse=True)
    return {"race_id": race_id, "session_key": session_key, "re_sim_at": datetime.now(timezone.utc).isoformat(),
            "inputs": {"gaps": gaps or {}, "pit_events": pit_events or [], "sc_deployed": sc_deployed},
            "probabilities": {c: {"win": round(v["win_prob"],4), "podium": round(v["podium_prob"],4), "dnf": round(v["dnf_prob"],4)} for c,v in probs.items()},
            "leader": sorted_win[0][0], "confidence": round(out["results"]["confidence"],3),
            "top5": [{"code": c, "win": round(v["win_prob"],4)} for c,v in sorted_win[:5]]}
