"""Run: cd backend && python -m pytest -q tests/test_engine_v2.py   (copy engine_v2.py to backend/app/engine.py first)"""
import json
from pathlib import Path

import numpy as np
import pytest

from app.engine import Params, pair_stats, predict

SEED = json.loads((Path(__file__).parents[1] / "app/data/seed.json").read_text())
T = {t["id"]: t for t in SEED["teams"]}


def field():
    return [dict(code=d["code"], name=d["name"], team=d["team"], pace=T[d["team"]]["pace"], skill=d["skill"], wet=d["wet"],
                 rel=T[d["team"]]["rel"], form=(d["points"] / 17 if d["points"] is not None else None)) for d in SEED["drivers"]]


CIRC = dict(SEED["circuits"]["rodriguez"], lap_ref=77.774)
CODES = [f["code"] for f in field()]


def grid_by(order):  # list of driver codes P1..Pn -> grid_fixed tuple in field order
    fix = [-1] * len(CODES)
    for slot, c in enumerate(order):
        fix[CODES.index(c)] = slot
    return tuple(fix)


# a plausible known grid: reverse of the model's own ordering, so the grid disagrees strongly with the ratings
BASE_ORDER = [d["code"] for d in predict(field(), CIRC, Params(sims=3000, seed=1))["drivers"]]
REVERSED = grid_by(BASE_ORDER[::-1])
FORM = grid_by(BASE_ORDER)


def w(r, code):
    return next(d for d in r["drivers"] if d["code"] == code)


def test_probabilities_consistent_all_sessions():
    for s in ("race", "sprint", "qualifying", "sprint_qualifying", "practice"):
        r = predict(field(), CIRC, Params(sims=3000, session=s, sub="FP2"))
        assert abs(sum(d["win"] for d in r["drivers"]) - 1) < 1e-9
        assert abs(sum(d["podium"] for d in r["drivers"]) - 3) < 1e-9
        assert abs(sum(s_["prob"] for s_ in r["strategies"]) - 100) < 1e-9
    r = predict(field(), CIRC, Params(sims=3000))
    assert abs(sum(d["fastest_lap"] for d in r["drivers"]) - 1) < 1e-9
    assert all(abs(sum(d["full_dist"]) + d["dnf"] - 1) < 1e-9 for d in r["drivers"])
    assert all(abs(sum(d["pts_dist"]) - 1) < 1e-9 for d in r["drivers"])
    assert abs(sum(r["scenario"].values()) - 1) < 1e-9
    assert abs(sum(r["win_by_grid"]) - 1) < 1e-9


def test_known_grid_carries_at_least_half_of_the_score():
    free = predict(field(), CIRC, Params(sims=3000, seed=2))
    full = predict(field(), CIRC, Params(sims=3000, seed=2, grid_fixed=REVERSED))
    assert free["grid_influence"] == 0.0 and full["grid_influence"] >= 0.5
    gs = next(f["share"] for f in full["factors"] if f["name"] == "Starting Grid")
    assert gs >= 0.5                          # shown to the user as a factor share
    # behavioural check: the slowest car on pole now has a far higher win chance than with a simulated grid
    last = BASE_ORDER[-1]
    assert w(full, last) is not None
    pole = w(predict(field(), CIRC, Params(sims=6000, seed=2, grid_fixed=REVERSED)), BASE_ORDER[-1])["win"]
    pole_free = w(predict(field(), CIRC, Params(sims=6000, seed=2)), BASE_ORDER[-1])["win"]
    assert pole > 20 * max(pole_free, 1e-4) or pole > 0.05


def test_grid_strength_scales_with_circuit_and_never_below_min():
    monaco = dict(SEED["circuits"]["monaco"], lap_ref=72.0)
    a = predict(field(), monaco, Params(sims=2000, seed=3, grid_fixed=FORM))["grid_influence"]
    b = predict(field(), dict(SEED["circuits"]["monza"], lap_ref=80.0), Params(sims=2000, seed=3, grid_fixed=FORM))["grid_influence"]
    assert a > b >= 0.5
    z = predict(field(), CIRC, Params(sims=2000, seed=3, grid_fixed=FORM, grid_weight=0.0))["grid_influence"]
    assert z >= 0.5


def test_partial_manual_grid_only_affects_pinned_drivers():
    fix = [-1] * len(CODES); fix[CODES.index("HAM")] = 0
    r = predict(field(), CIRC, Params(sims=4000, seed=4, grid_fixed=tuple(fix)))
    assert 0 < r["grid_influence"] < 0.1 and r["grid_locked_count"] == 1
    h = w(r, "HAM")
    assert h["pole"] == 1.0 and h["avg_quali"] == 1.0 and h["avg_grid"] == 1.0 and h["reach_q3"] == 1.0   # consistency fix


def test_locked_grid_makes_qualifying_view_consistent():
    r = predict(field(), CIRC, Params(sims=2000, seed=5, grid_fixed=FORM))
    assert abs(sum(d["pole"] for d in r["drivers"]) - 1) < 1e-9
    assert [q["code"] for q in r["qualifying"]][:3] == BASE_ORDER[:3]


def test_teammates_are_correlated_only_with_team_share():
    def corr(ts):
        r = predict(field(), CIRC, Params(sims=8000, seed=6, team_share=ts, want_samples=False) if False else Params(sims=8000, seed=6, team_share=ts), want_samples=True)
        pos = r["_samples"]["pos"]
        i, j = CODES.index("ALO"), CODES.index("STR")
        return np.corrcoef(pos[:, i], pos[:, j])[0, 1]
    assert corr(0.35) > corr(0.0) + 0.10


def test_model_uncertainty_is_reported_separately_from_mc_error():
    r = predict(field(), CIRC, Params(sims=20000, seed=7))
    top = r["drivers"][0]
    assert top["win_lo"] <= top["win"] <= top["win_hi"]
    assert top["win_model_sd"] > 0.01                        # parameter uncertainty is real ...
    assert (top["win_hi"] - top["win_lo"]) / 2 > 3 * top["win_mc_ci"]   # ... and larger than the MC error at 20k sims
    r0 = predict(field(), CIRC, Params(sims=20000, seed=7, rating_sd=0.0))
    assert sum(d["win_model_sd"] > 0 for d in r0["drivers"]) <= 2          # noise-floor guard: ~nothing resolvable


def test_sprint_physics_differs():
    race = predict(field(), CIRC, Params(sims=8000, seed=8, session="race"))
    spr = predict(field(), CIRC, Params(sims=8000, seed=8, session="sprint"))
    assert np.mean([d["dnf"] for d in spr["drivers"]]) < 0.6 * np.mean([d["dnf"] for d in race["drivers"]])
    assert spr["safety_car_prob"] < race["safety_car_prob"]
    assert max(d["avg_points"] for d in spr["drivers"]) <= 8 and spr["strategies"][0]["stops"] == "No stop"
    assert spr["drivers"][0]["pts_dist"][-1] >= 0


def test_practice_profiles_differ():
    sp = lambda sub: np.mean([d["pace_hi"] - d["pace_lo"] for d in predict(field(), CIRC, Params(sims=4000, seed=9, session="practice", sub=sub))["drivers"]])
    assert sp("FP1") > sp("FP2") > sp("FP3")
    d = predict(field(), CIRC, Params(sims=3000, seed=9, session="practice", sub="FP2"))["drivers"][0]
    assert {"long_gap", "top3", "top10", "pace_gap"} <= set(d)


def test_quali_segments_cut_sizes_and_labels():
    r = predict(field(), CIRC, Params(sims=4000, seed=10, session="qualifying"))
    s = r["quali_segments"]; n = len(CODES)
    assert set(s) == {"Q1", "Q2", "Q3"}
    assert abs(sum(x["p_eliminated"] for x in s["Q1"]) - (n - 16)) < 1e-9
    assert abs(sum(x["p_eliminated"] for x in s["Q2"]) - (16 - 10)) < 1e-9
    assert abs(sum(x["pole"] for x in s["Q3"]) - 1) < 1e-9
    assert set(predict(field(), CIRC, Params(sims=1000, seed=10, session="sprint_qualifying"))["quali_segments"]) == {"SQ1", "SQ2", "SQ3"}
    assert len(r["teammate_battle"]) == 11


def test_pair_stats():
    r = predict(field(), CIRC, Params(sims=5000, seed=11), want_samples=True)
    ps = pair_stats(r["_samples"], "VER", "NOR")
    assert abs(ps["p_a_ahead"] + ps["p_b_ahead"] - 1) < 1e-12 and 0 <= ps["p_both_dnf"] <= 0.05


def test_deterministic_and_json_safe():
    a = predict(field(), CIRC, Params(sims=2000)); b = predict(field(), CIRC, Params(sims=2000))
    assert a["drivers"][0]["win"] == b["drivers"][0]["win"]
    json.dumps(a)
    json.dumps(predict(field(), CIRC, Params(sims=1000, session="qualifying")))


def test_what_if_grid_warning_and_rank_corr():
    ok = predict(field(), CIRC, Params(sims=2000, seed=12, grid_fixed=FORM))
    bad = predict(field(), CIRC, Params(sims=2000, seed=12, grid_fixed=REVERSED))
    assert ok["warnings"] == [] and ok["grid_pace_corr"] > 0.8
    assert len(bad["warnings"]) == 1 and bad["grid_pace_corr"] < 0
    assert predict(field(), CIRC, Params(sims=1000, seed=12))["grid_pace_corr"] is None


def test_realistic_pole_conversion_band():
    r = predict(field(), CIRC, Params(sims=8000, seed=13, grid_fixed=FORM))
    assert 0.35 < r["win_by_grid"][0] < 0.65          # hybrid-era pole->win is roughly 40%; the model favourite converts a bit more
    assert r["win_by_grid"][0] > r["win_by_grid"][1] > r["win_by_grid"][2]
