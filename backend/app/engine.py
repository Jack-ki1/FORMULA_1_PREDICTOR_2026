"""Vectorised Monte Carlo weekend engine (NumPy only, so it fits comfortably in a Vercel function).

Sessions: practice (pace distribution), qualifying (Q1/Q2/Q3 elimination), race, sprint.
All "weight" parameters are normalised so their defaults reproduce the base model."""
from __future__ import annotations

import json
import zlib
from dataclasses import asdict, dataclass

import numpy as np

PTS_RACE = np.array([25, 18, 15, 12, 10, 8, 6, 4, 2, 1])
PTS_SPRINT = np.array([8, 7, 6, 5, 4, 3, 2, 1])
WETNESS = {"dry": 0.0, "mixed": 0.5, "wet": 1.0}
ZCI = {0.9: 1.645, 0.95: 1.96, 0.99: 2.576}


@dataclass
class Params:
    sims: int = 3000
    weather: str = "dry"  # dry | mixed | wet (resolve "auto" before calling)
    session: str = "race"  # practice | qualifying | race | sprint
    mech: bool = True
    sc: bool = True
    enhanced: bool = True  # blend season form into the base ratings
    chaos: float = 0.5
    seed: int | None = None
    grid_fixed: tuple | None = None  # per driver (field order): locked grid slot (0-based) or -1 when free
    grid_weight: float = 0.55
    wet_influence: float = 0.6
    reliability: float = 0.4
    strategy_aggr: float = 0.5
    sc_weight: float = 0.3
    team_w: float = 0.6
    driver_w: float = 0.4
    track_w: float = 1.0
    weather_w: float = 1.0
    deg_w: float = 1.0
    form_k: float = 32.0
    ci: float = 0.95


def _z(a: np.ndarray) -> np.ndarray:
    s = a.std()
    return (a - a.mean()) / s if s > 1e-9 else a * 0.0


def base_ratings(field: list[dict], enhanced: bool = True, team_w: float = 0.6, driver_w: float = 0.4, form_k: float = 32.0) -> np.ndarray:
    pace = np.array([f["pace"] for f in field], float)
    skill = np.array([f["skill"] for f in field], float)
    prior = _z(team_w * _z(pace) + driver_w * _z(skill))
    form = np.array([np.nan if f.get("form") is None else f["form"] for f in field], float)
    known = ~np.isnan(form)
    fz = prior
    if known.sum() >= 4:  # impute unknown drivers' form from the prior, then z-score together
        a, b = np.polyfit(prior[known], form[known], 1)
        fz = _z(np.where(known, form, np.maximum(a * prior + b, 0)))
    lam = float(np.clip(form_k / 64, 0, 1)) if enhanced else 0.15
    return _z((1 - lam) * prior + lam * fz)


def _pos(score: np.ndarray) -> np.ndarray:  # 0-based rank, best = 0
    return np.argsort(np.argsort(-score, axis=1), axis=1)


def fmt_lap(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"{int(m)}:{s:06.3f}"


def _qualifying(rng, base, wz, w, p: Params, S: int, n: int):
    """Q1 (all) -> Q2 (best 16 of 22) -> Q3 (best 10). Returns 0-based final positions and the advancement masks."""
    sd = (0.28 + 0.30 * p.chaos) * (1 + 0.6 * w)
    mean = base + 0.6 * w * wz * (p.wet_influence / 0.6)
    keep1, keep2 = round(n * 16 / 22), round(n * 10 / 22)
    s1 = mean + rng.normal(0, sd, (S, n)); r1 = _pos(s1); in16 = r1 < keep1
    s2 = np.where(in16, mean + rng.normal(0, sd * 0.9, (S, n)), -1e9); r2 = _pos(s2); in10 = in16 & (r2 < keep2)
    s3 = np.where(in10, mean + rng.normal(0, sd * 0.8, (S, n)), -1e9); r3 = _pos(s3)
    return np.where(in10, r3, np.where(in16, r2, r1)), in16, in10, mean


def predict(field: list[dict], circ: dict, p: Params, rounds_of_data: int = 0) -> dict:
    n, S = len(field), int(p.sims)
    seed = p.seed
    if seed is None:
        key = json.dumps([[f["code"], round(f["pace"]), round(f["skill"]), round(f.get("form") or 0, 1)] for f in field]
                         + [circ.get("name"), asdict(p)], default=str)
        seed = zlib.crc32(key.encode())
    rng = np.random.default_rng(seed)
    base = base_ratings(field, p.enhanced, p.team_w, p.driver_w, p.form_k)
    wz = _z(np.array([f["wet"] for f in field], float))
    rel = np.array([f["rel"] for f in field], float)
    w = float(np.clip(WETNESS[p.weather] * p.weather_w, 0, 1.5))
    wk = p.wet_influence / 0.6
    ot = float(np.clip(0.5 + p.track_w * (circ.get("overtaking", 0.5) - 0.5), 0, 1))
    tw = float(np.clip(0.5 + p.track_w * (circ.get("tyre_wear", 0.5) - 0.5), 0, 1))
    G = (0.25 + 0.85 * (1 - ot)) * (p.grid_weight / 0.55)  # how "sticky" the grid is at this circuit
    lap_ref = circ.get("lap_ref", 90.0)
    gap_scale = 0.0030 * lap_ref
    sc_p = min(0.95, circ.get("sc_prob", 0.45) * p.track_w * (1 + 0.3 * w) * (p.sc_weight / 0.3)) if p.sc else 0.0

    qpos, in16, in10, qmean = _qualifying(rng, base, wz, w, p, S, n)
    # Starting grid: locked slots (manual or fetched) + simulated qualifying order for the free drivers
    gpos = qpos
    if p.grid_fixed is not None and any(g >= 0 for g in p.grid_fixed):
        fix = np.array(p.grid_fixed)
        free = np.where(fix < 0)[0]
        slots = np.array(sorted(set(range(n)) - set(int(x) for x in fix if x >= 0)))
        gpos = np.tile(np.where(fix >= 0, fix, 0), (S, 1))
        if len(free):
            order = np.argsort(-qmean_noise(rng, qmean, free, S, base, p), axis=1)
            gp_free = np.empty((S, len(free)), int)
            np.put_along_axis(gp_free, order, np.broadcast_to(slots[: len(free)], (S, len(free))), axis=1)
            gpos[:, free] = gp_free

    sc_hit = np.zeros(S, bool)
    pace_gap = None
    if p.session == "qualifying":
        pos, dnf = qpos + 1, np.zeros((S, n), bool)
    elif p.session == "practice":
        sd = 0.30 + 0.25 * p.chaos + 0.25  # extra spread: teams run different programmes
        ps = base + 0.6 * w * wz * wk + rng.normal(0, sd, (S, n))
        pos, dnf = _pos(ps) + 1, np.zeros((S, n), bool)
        gaps = (ps.max(1, keepdims=True) - ps) * gap_scale
        pace_gap = (gaps.mean(0), np.percentile(gaps, 10, axis=0), np.percentile(gaps, 90, axis=0))
    else:
        det = base + G * (-gpos / max(n - 1, 1)) + 0.9 * w * wz * wk
        sc_hit = rng.random(S) < sc_p
        det = np.where(sc_hit[:, None], 0.7 * det, det)
        sd = (0.40 + 0.85 * p.chaos) * (1 + 0.5 * w) * (1 + 0.3 * (p.strategy_aggr - 0.5)) * (1 + 0.25 * (tw * p.deg_w - 0.5))
        noise = rng.normal(0, 1, (S, n)) * sd * np.where(sc_hit, 1.35, 1.0)[:, None]
        pdnf = 0.02 * (1 + w) + ((0.9 * (1 - rel) * (1 + 0.5 * w) * (p.reliability / 0.4)) if p.mech else 0)
        dnf = rng.random((S, n)) < np.clip(pdnf, 0, 0.9)
        pos = _pos(np.where(dnf, det + noise - 100, det + noise)) + 1

    fin = ~dnf
    table = {"race": PTS_RACE, "sprint": PTS_SPRINT}.get(p.session, np.zeros(1, int))
    pts = np.where((pos <= len(table)) & fin, table[np.minimum(pos, len(table)) - 1], 0)

    fl = np.zeros(n)
    if p.session == "race":  # fastest lap: pace-driven, from finishers in the top 12
        pz = _z(np.array([f["pace"] for f in field], float)); sz = _z(np.array([f["skill"] for f in field], float))
        s = 0.85 * pz + 0.15 * sz + rng.normal(0, 0.9, (S, n))
        fl = np.bincount(np.argmax(np.where(fin & (pos <= 12), s, -1e9), axis=1), minlength=n) / S

    win, podium = (pos == 1).mean(0), (pos <= 3).mean(0)
    ptsp = ((pos <= 10) & fin).mean(0)
    exp_pos = (pos * fin).sum(0) / np.maximum(fin.sum(0), 1)
    dist = np.stack([(pos == k).mean(0) for k in range(1, 11)], 1)
    pole = (qpos == 0).mean(0)
    z = ZCI.get(round(p.ci, 2), 1.96)
    ci = z * np.sqrt(win * (1 - win) / S)
    gap_q = (qmean.max() - qmean) * gap_scale
    avg_grid = (gpos.mean(0) + 1) if p.session in ("race", "sprint") else (qpos.mean(0) + 1)

    rows = []
    for i, f in enumerate(field):
        r = dict(code=f["code"], name=f["name"], team=f["team"], win=float(win[i]), win_ci=float(ci[i]), podium=float(podium[i]),
                 points_prob=float(ptsp[i]), dnf=float(dnf[i].mean()), avg_points=float(pts[:, i].mean()), exp_pos=float(exp_pos[i]),
                 fastest_lap=float(fl[i]), pole=float(pole[i]), avg_quali=float(qpos[:, i].mean() + 1), avg_grid=float(avg_grid[i]),
                 reach_q2=float(in16[:, i].mean()), reach_q3=float(in10[:, i].mean()), dist=[float(x) for x in dist[i]], gap=float(gap_q[i]))
        if pace_gap is not None:
            r.update(pace_gap=float(pace_gap[0][i]), pace_lo=float(pace_gap[1][i]), pace_hi=float(pace_gap[2][i]))
        rows.append(r)
    key = (lambda r: (r["pace_gap"], -r["win"])) if p.session == "practice" else (lambda r: (-r["avg_points"], -r["win"], r["exp_pos"]))
    if p.session == "qualifying":
        key = lambda r: (r["avg_quali"], -r["pole"])
    rows.sort(key=key)
    for k, r in enumerate(rows, 1):
        r["pos"] = k
    qual = sorted(rows, key=lambda r: r["avg_quali"])
    qualifying = [dict(pos=k, code=r["code"], pole=r["pole"], gap=r["gap"], time=fmt_lap(lap_ref + r["gap"]), q2=r["reach_q2"], q3=r["reach_q3"])
                  for k, r in enumerate(qual, 1)]

    # --- confidence & factors ---
    wp = np.clip(win, 1e-12, 1); wp = wp / wp.sum()
    sharp = float(np.clip(1 + (wp * np.log(wp)).sum() / np.log(n), 0, 1))
    conf = float(np.clip(0.45 + 0.35 * sharp + 0.12 * min(1.0, S / 10000) ** 0.5 - 0.18 * min(w, 1) - 0.10 * p.chaos, 0.2, 0.95))
    comp = {
        "Team Performance": np.std(p.team_w * _z(np.array([f["pace"] for f in field], float))),
        "Driver Form": np.std(p.driver_w * _z(np.array([f["skill"] for f in field], float)) + (np.clip(p.form_k / 64, 0, 1) if p.enhanced else 0.15) * base),
        "Track Suitability": np.std(G * (-np.arange(n) / max(n - 1, 1))),
        "Weather": np.std(0.9 * w * wk * wz) if w > 0 else 0.0,
    }
    tot = sum(comp.values()) or 1.0
    lvl = lambda s: "High" if s >= 0.33 else "Medium" if s >= 0.18 else "Low"
    factors = [dict(name=k, level=lvl(v / tot), share=float(v / tot)) for k, v in comp.items()]
    factors.append(dict(name="Historical Data", level="High" if rounds_of_data >= 10 else "Medium" if rounds_of_data >= 4 else "Low", share=min(1.0, rounds_of_data / 23)))

    # --- strategy ---
    ag = p.strategy_aggr - 0.5
    if w >= 0.75:
        names = [("1 Stop", "Intermediate → Medium"), ("2 Stops", "Intermediate → Intermediate → Medium"), ("1 Stop", "Full Wet → Intermediate")]
        u = np.array([0.7 - 0.6 * ag, 0.55 + 0.3 * tw * p.deg_w, 0.2 + 1.2 * ag])
    else:
        names = [("1 Stop", "Medium → Hard"), ("2 Stops", "Medium → Medium → Hard"), ("1 Stop", "Soft → Hard")]
        u = np.array([0.9 - 1.0 * tw * p.deg_w - 0.6 * ag, 0.2 + 0.9 * tw * p.deg_w + 0.35 * sc_p, 0.1 + 0.5 * (1 - tw) + 0.4 * ot - 0.3 * w + 1.2 * ag])
    e = np.exp(3 * (u - u.max())); pr = np.round(100 * e / e.sum()).astype(int); pr[0] += 100 - pr.sum()
    strategies = [dict(name=f"Strategy {i + 1}", stops=a, tyres=b, prob=int(pr[i]), optimal=bool(i == int(np.argmax(pr)))) for i, (a, b) in enumerate(names)]

    return dict(drivers=rows, qualifying=qualifying, strategies=strategies, factors=factors, confidence=conf, sharpness=sharp,
                safety_car_rate=float(sc_hit.mean()), safety_car_prob=float(sc_p), seed=int(seed), weather_used=p.weather)


def qmean_noise(rng, qmean, free, S, base, p):
    """Qualifying-style scores for the drivers whose grid slot is not locked."""
    return qmean[free][None, :] + rng.normal(0, 0.28 + 0.30 * p.chaos, (S, len(free)))
