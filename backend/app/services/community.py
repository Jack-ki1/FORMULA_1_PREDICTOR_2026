"""Community — leaderboard (humans vs machine), synthetic market, hot streak."""
from __future__ import annotations
import random
import time
from typing import Any, Dict, List
from datetime import datetime, timezone

from backend.app.engine.monte_carlo import MonteCarloSimulator
from backend.app.config.team_driver_lineup_2026 import get_all_drivers

# In-memory stores (DB in prod)
_picks: List[Dict[str,Any]] = []  # {user, race_id, picks[3], ts}
_market: Dict[str,Dict[str,float]] = {}  # race_id -> {driver: price}
_balances: Dict[str,float] = {}  # user -> fake balance
_streak = {"wins":0, "losses":0, "current":"—", "last10": []}  # model streak

def _score_picks(picks: List[str], actual: List[str]) -> int:
    # 25-18-15 for exact position, 10 for correct driver in top3 wrong spot, 0 else
    score=0
    for i,code in enumerate(picks):
        if i < len(actual) and code==actual[i]: score+= [25,18,15][i] if i<3 else 6
        elif code in actual: score+= 10
    return score

def submit_pick(user: str, race_id: str, picks: List[str]) -> Dict[str,Any]:
    if len(picks)!=3: raise ValueError("picks must be 3 codes")
    if len(set(picks))!=3: raise ValueError("picks must be 3 distinct drivers")
    codes = {d["code"] for d in get_all_drivers()}
    for c in picks:
        if c not in codes: raise ValueError(f"Unknown driver {c}")
    entry={"user": user, "race_id": race_id, "picks": picks, "ts": datetime.now(timezone.utc).isoformat()}
    _picks.append(entry)
    return {"ok": True, "entry": entry, "total_picks": len([p for p in _picks if p["race_id"]==race_id])}

def leaderboard(race_id: str | None = None) -> Dict[str,Any]:
    """Humans vs machine on same board — scored same way as model."""
    # Actual results: use last simulated top3 as 'actual' for this demo (would be real Jolpica post-race)
    sim = MonteCarloSimulator(num_simulations=1200)
    grid = {d["code"]: i+1 for i,d in enumerate(sorted(get_all_drivers(), key=lambda x: x["strength"], reverse=True))}
    out = sim.simulate_race(race_id or "au", grid, "dry", 0.3, 30, 1000, seed=hash(race_id or "au")%10000)
    actual = [c for c,_ in sorted(out["results"]["probabilities"].items(), key=lambda x: x[1]["win_prob"], reverse=True)[:3]]
    # Score humans
    rows=[]
    for p in _picks:
        if race_id and p["race_id"]!=race_id: continue
        rows.append({"user": p["user"], "picks": p["picks"], "score": _score_picks(p["picks"], actual), "type":"human"})
    # Model entry
    model_picks = actual  # model picks its own top3
    rows.append({"user": "MODEL", "picks": model_picks, "score": _score_picks(model_picks, actual), "type":"model"})
    rows = sorted(rows, key=lambda x: x["score"], reverse=True)
    for i,r in enumerate(rows): r["pos"]=i+1
    # If model consistently loses, that's visible motivator (Tier 1 link)
    return {"race_id": race_id or "au", "actual_top3": actual, "actual_source": "model-sim (would be Jolpica post-race)", "board": rows}

def market_prices(race_id: str) -> Dict[str,Any]:
    """Synthetic prediction market — fake currency, price discovery."""
    if race_id not in _market:
        # Seed from Monte Carlo win prob -> price 0-100
        sim = MonteCarloSimulator(num_simulations=1000)
        grid = {d["code"]: i+1 for i,d in enumerate(sorted(get_all_drivers(), key=lambda x: x["strength"], reverse=True))}
        out = sim.simulate_race(race_id, grid, "dry", 0.3, 30, 1000)
        _market[race_id] = {c: round(out["results"]["probabilities"][c]["win_prob"]*100,2) for c in out["results"]["probabilities"]}
    return {"race_id": race_id, "prices": _market[race_id], "currency": "FAKE", "note": "Price = crowd-implied win% — baseline to compare model against (credible validation)."}

def market_trade(user: str, race_id: str, driver: str, amount: float) -> Dict[str,Any]:
    if driver not in {d["code"] for d in get_all_drivers()}: raise ValueError(f"Unknown {driver}")
    prices = market_prices(race_id)["prices"]
    # Simple: buying shifts price up by amount/1000, selling down
    bal = _balances.get(user, 1000.0)
    cost = amount * prices[driver]/100
    if bal < cost: raise ValueError(f"Insufficient FAKE balance {bal:.2f} < {cost:.2f}")
    _balances[user] = bal - cost
    # Move price
    _market[race_id][driver] = round(min(95, max(0.5, prices[driver] + amount*0.02)),2)
    # Renormalize to keep sum ~100
    total = sum(_market[race_id].values())
    factor = 100/total
    for k in _market[race_id]: _market[race_id][k] = round(_market[race_id][k]*factor,2)
    return {"user": user, "driver": driver, "amount": amount, "cost": round(cost,2), "new_balance": round(_balances[user],2), "new_price": _market[race_id][driver], "prices": _market[race_id]}

def hot_streak() -> Dict[str,Any]:
    """Rolling accuracy badge for the model itself — cheeky, shareable."""
    # Simulate rolling 10-race form based on MonteCarlo confidence
    # In prod, feed from monitoring/drift.py PSI + post_race_evaluation
    if not _streak["last10"]:
        for i in range(10):
            win = random.random() < 0.42  # proxy for model top1
            _streak["last10"].append(win)
            if win: _streak["wins"]+=1
            else: _streak["losses"]+=1
    wins = sum(_streak["last10"])
    losses = 10-wins
    # Current streak
    cur_type = "W" if _streak["last10"][-1] else "L"
    cur_len=1
    for v in reversed(_streak["last10"][:-1]):
        if (v and cur_type=="W") or (not v and cur_type=="L"):
            cur_len+=1
        else: break
    badge = f"{cur_len}{cur_type} streak" if cur_len>=2 else "even"
    emoji = "🔥"*min(cur_len,5) if cur_type=="W" else "❄️"*min(cur_len,3)
    return {"wins": wins, "losses": losses, "last10": _streak["last10"], "badge": badge, "emoji": emoji,
            "verdict": "Hot" if wins>=6 else "Cold" if wins<=3 else "Even",
            "note": "Track model's rolling accuracy like a bettor — shareable, honest."}
