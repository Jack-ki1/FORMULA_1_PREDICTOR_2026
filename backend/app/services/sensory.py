"""Sensory — sonification + rivalry graph."""
from __future__ import annotations
import math
import hashlib
from typing import Any, Dict, List

from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.engine.elo_calculator import elo_calculator
from backend.app.engine.monte_carlo import MonteCarloSimulator

def sonify_race(race_id: str = "au", duration_s: int = 30) -> Dict[str,Any]:
    """Gap-to-leader / tire-degradation curve -> generative audio params.
    Telemetry is already a time series — map to frequencies.
    """
    # Synthetic gap curve: leader gap 0, others follow with noise + degradation
    drivers = get_all_drivers()[:6]  # top6 for brevity
    # Base gaps from Monte Carlo avg_position -> seconds
    sim = MonteCarloSimulator(num_simulations=800)
    grid = {d["code"]: i+1 for i,d in enumerate(sorted(drivers, key=lambda x: x["strength"], reverse=True))}
    out = sim.simulate_race(race_id, grid, "dry", 0.3, 30, 800)
    gaps = {c: out["results"]["probabilities"][c]["avg_position"]*2.2 for c in out["results"]["probabilities"] if c in [d["code"] for d in drivers]}
    # Build audio: each driver = oscillator, gap -> frequency, degradation -> filter
    steps = 24  # 24 steps across duration
    tracks=[]
    base_freq=110  # A2
    for d in drivers:
        code = d["code"]
        gap = gaps.get(code, 10)
        # Map gap 0-20s to semitones 0..12
        semitones = min(12, gap*0.6)
        freq = base_freq * (2 ** (semitones/12))
        # Degradation: late race tire drop -> add vibrato
        curve = [round(math.sin(2*math.pi*i/steps + hash(code)%7)* (gap/10),3) for i in range(steps)]
        tracks.append({"code": code, "team": d["team_name"], "gap_s": round(gap,2),
                       "base_freq_hz": round(freq,1), "semitones": round(semitones,2),
                       "curve": curve, "instrument": "sine" if gap<5 else "saw"})
    # Master timeline
    timeline = [{"t": round(i/steps*duration_s,2), "note": i} for i in range(steps)]
    # WebAudio snippet
    snippet = """// Play with WebAudio: gap->frequency, degradation->filter\nconst ctx=new AudioContext(); tracks.forEach(tr=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=tr.instrument;o.frequency.value=tr.base_freq_hz;g.gain.value=0.12;o.connect(g).connect(ctx.destination);o.start();});"""
    return {"race_id": race_id, "duration_s": duration_s, "tracks": tracks, "timeline": timeline,
            "web_audio_snippet": snippet, "note": "Telemetry as audio — genuinely unique demo."}

def rivalry_graph() -> Dict[str,Any]:
    """Elo head-to-head matrix -> force-directed graph (nodes=drivers, edge=battles)."""
    drivers = get_all_drivers()
    codes = [d["code"] for d in drivers]
    # Build Elo matrix: expected score driver A vs B
    nodes = [{"id": d["code"], "name": d["name"], "team": d["team_name"], "color": d["team_color"],
              "elo": round(elo_calculator.get_rating(d["code"]),0)} for d in drivers]
    links=[]
    for i, a in enumerate(codes):
        for b in codes[i+1:]:
            prob = elo_calculator.get_h2h_probability(a,b)  # A beats B
            # Edge thickness = battles (proxy: inverse Elo distance -> close rivals battle more)
            # Color = dominance (red if A >> B, blue if B >> A)
            diff = abs(elo_calculator.get_rating(a)-elo_calculator.get_rating(b))
            battles = max(1, int(12 - diff/60))  # 1..12
            dominance = prob if prob>0.5 else 1-prob
            links.append({"source": a, "target": b, "prob_a_beats_b": round(prob,3),
                          "battles": battles, "dominance": round(dominance,3),
                          "winner": a if prob>0.5 else b})
    # Sort links by battles desc for vis
    links = sorted(links, key=lambda x: x["battles"], reverse=True)[:60]  # top 60 edges
    return {"nodes": nodes, "links": links, "note": "Edge thickness=battles, color=dominance — more visceral than a table."}
