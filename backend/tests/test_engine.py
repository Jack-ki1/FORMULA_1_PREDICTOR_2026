import json
from pathlib import Path
from app.engine import Params, predict

SEED = json.loads((Path(__file__).parents[1] / "app/data/seed.json").read_text())
T = {t["id"]: t for t in SEED["teams"]}


def field():
    return [dict(code=d["code"], name=d["name"], team=d["team"], pace=T[d["team"]]["pace"], skill=d["skill"],
                 wet=d["wet"], rel=T[d["team"]]["rel"], form=(d["points"] / 17 if d["points"] is not None else None))
            for d in SEED["drivers"]]


CIRC = dict(SEED["circuits"]["rodriguez"], lap_ref=77.774)


def test_probabilities_are_consistent():
    r = predict(field(), CIRC, Params(sims=4000))
    assert abs(sum(d["win"] for d in r["drivers"]) - 1) < 1e-9
    assert abs(sum(d["podium"] for d in r["drivers"]) - 3) < 1e-9
    assert abs(sum(s["prob"] for s in r["strategies"]) - 100) < 1e-9
    assert 0.2 <= r["confidence"] <= 0.95


def test_deterministic_and_seed_sensitive():
    a = predict(field(), CIRC, Params(sims=2000))
    b = predict(field(), CIRC, Params(sims=2000))
    assert a["drivers"][0]["win"] == b["drivers"][0]["win"]
    c = predict(field(), CIRC, Params(sims=2000, seed=7))
    assert c["seed"] == 7


def test_wet_adds_uncertainty_and_favours_wet_specialists():
    dry = predict(field(), CIRC, Params(sims=6000, weather="dry"))
    wet = predict(field(), CIRC, Params(sims=6000, weather="wet"))
    assert wet["confidence"] < dry["confidence"]
    top = lambda r: r["drivers"][0]["win"]
    assert top(wet) < top(dry)


def test_qualifying_session_has_no_points_and_race_fastest_lap_sums_to_one():
    q = predict(field(), CIRC, Params(sims=2000, session="qualifying"))
    assert all(d["avg_points"] == 0 for d in q["drivers"])
    r = predict(field(), CIRC, Params(sims=2000))
    assert abs(sum(d["fastest_lap"] for d in r["drivers"]) - 1) < 1e-9
