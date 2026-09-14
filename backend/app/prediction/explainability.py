"""
Explainability — data-grounded reasons per driver (no LLM hallucination).
"""
from typing import Dict, Any

def explain(driver_code: str, prob: float, grid: int, driver: Dict[str,Any], ctx: Dict[str,Any]) -> Dict[str,Any]:
    pos, neg = [], []
    if grid <= 3: pos.append("Strong starting grid (track position crucial in 2026 aero)")
    elif grid >= 14: neg.append(f"Starting P{grid} — overtaking difficulty {ctx.get('overtaking','medium')}")
    if driver.get("strength",50) >= 85: pos.append("High recent pace / qualifying strength")
    if driver.get("wet_skill",50) >= 88 and ctx.get("weather") in ("wet","mixed"): pos.append("Elite wet-weather skill")
    if driver.get("reliability",50) < 75: neg.append("Elevated DNF risk")
    if prob >= 0.30: pos.append(f"Model win probability {prob*100:.1f}% — clear favourite")
    elif prob <= 0.02: neg.append("Low model probability — dark horse only")
    # tyre/strategy
    if ctx.get("tyre_degradation","medium") == "high": neg.append("High tyre degradation risk")
    return {"driver": driver_code, "probability": round(prob,4), "grid": grid, "positives": pos[:3], "negatives": neg[:2], "source": "feature-grounded"}
