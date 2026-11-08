"""Vectorised Monte Carlo weekend engine v2 (NumPy only).

Drop-in replacement for backend/app/engine.py. Tested with numpy 2.5.4 / Python 3.12.
Sessions: practice (FP1|FP2|FP3), qualifying, sprint_qualifying, sprint, race.

What changed vs v1 (see changes.txt, section 3):
  * known / locked starting grid carries >= 50 % of the deterministic race score (per locked driver)
  * team-shared noise (teammates are correlated)
  * rating (parameter) uncertainty is propagated and reported separately from Monte-Carlo error
  * qualifying exposes Q1/Q2/Q3 segments; locked grids make pole / avg_quali / Q2 / Q3 consistent
  * practice FP1/FP2/FP3 profiles + long-run pace; sprint physics differ from the Grand Prix
  * many extra distributions used by the new plots (full finishing distribution, points distribution,
    grid->win conversion, scenario split, team points ranges, safety-car conditional win rates, ...)
"""
from __future__ import annotations

import json
import zlib
from dataclasses import asdict, dataclass

import numpy as np

PTS_RACE = np.array([25, 18, 15, 12, 10, 8, 6, 4, 2, 1])
PTS_SPRINT = np.array([8, 7, 6, 5, 4, 3, 2, 1])
WETNESS = {"dry": 0.0, "mixed": 0.5, "wet": 1.0}
ZCI = {0.9: 1.645, 0.95: 1.96, 0.99: 2.576}
SESSIONS = ("practice", "qualifying", "sprint_qualifying", "sprint", "race")
# one-lap sd multiplier, long-run sd multiplier (tunable; FP1 = unknown track/programmes, FP3 = quali sims)
PRACTICE_PROFILE = {"FP1": (1.25, 1.30), "FP2": (1.00, 0.70), "FP3": (0.80, 1.50)}
# segment time offsets (s) added to the simulated gap-to-pole; placeholders, estimates only
SEG_OFFSET = {1: 0.90, 2: 0.45, 3: 0.0}


@dataclass
class Params:
    sims: int = 3000
    weather: str = "dry"  # dry | mixed | wet (resolve "auto" before calling)
    session: str = "race"  # see SESSIONS
    sub: str = ""  # practice: FP1|FP2|FP3 (default FP2)
    mech: bool = True
    sc: bool = True
    enhanced: bool = True
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
    # --- new in v2 ---
    grid_known_min: float = 0.50  # minimum grid share of the race score for a locked driver
    rating_sd: float = 0.20  # sd (z units) of the rating random effect, one draw per block (tune via backtest)
    team_share: float = 0.35  # share of race/quali noise variance that is common to a team's cars
    blocks: int = 20  # parameter-uncertainty blocks


def _z(a: np.ndarray) -> np.ndarray:
    s = a.std()
    return (a - a.mean()) / s if s > 1e-9 else a * 0.0


def base_ratings(field, enhanced=True, team_w=0.6, driver_w=0.4, form_k=32.0) -> np.ndarray:
    pace = np.array([f["pace"] for f in field], float)
    skill = np.array([f["skill"] for f in field], float)
    prior = _z(team_w * _z(pace) + driver_w * _z(skill))
    form = np.array([np.nan if f.get("form") is None else f["form"] for f in field], float)
    known = ~np.isnan(form)
    fz = prior
    if known.sum() >= 4:
        a, b = np.polyfit(prior[known], form[known], 1)
        fz = _z(np.where(known, form, np.maximum(a * prior + b, 0)))
    lam = float(np.clip(form_k / 64, 0, 1)) if enhanced else 0.15
    return _z((1 - lam) * prior + lam * fz)


def _pos(score: np.ndarray) -> np.ndarray:  # 0-based rank, best = 0
    return np.argsort(np.argsort(-score, axis=1), axis=1)


def fmt_lap(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"{int(m)}:{s:06.3f}"


def _qualifying(rng, mean, w, p: Params, S, n, tidx, T, sd_mult=1.0):
    """Q1 (all) -> Q2 (best ~16/22) -> Q3 (best ~10/22). `mean` is (S,n) or (n,).
    Returns final 0-based order, per-segment ranks and the advancement masks."""
    sd = (0.28 + 0.30 * p.chaos) * (1 + 0.6 * w) * sd_mult
    sd_t, sd_d = sd * np.sqrt(p.team_share), sd * np.sqrt(1 - p.team_share)

    def noise(scale):
        return scale * (rng.normal(0, sd_d, (S, n)) + rng.normal(0, sd_t, (S, T))[:, tidx])

    keep1, keep2 = round(n * 16 / 22), round(n * 10 / 22)
    s1 = mean + noise(1.0); r1 = _pos(s1); in16 = r1 < keep1
    s2 = np.where(in16, mean + noise(0.9), -1e9); r2 = _pos(s2); in10 = in16 & (r2 < keep2)
    s3 = np.where(in10, mean + noise(0.8), -1e9); r3 = _pos(s3)
    final = np.where(in10, r3, np.where(in16, r2, r1))
    return final, r1, r2, r3, in16, in10


def _cond_mean(x, mask):
    c = mask.sum(0)
    return np.where(c > 0, (x * mask).sum(0) / np.maximum(c, 1), np.nan), c / mask.shape[0]


def _nn(v):  # nan -> None for JSON
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)


def predict(field: list[dict], circ: dict, p: Params, rounds_of_data: int = 0, want_samples: bool = False) -> dict:
    if p.session not in SESSIONS:
        raise ValueError(f"unknown session {p.session}")
    n, S = len(field), int(p.sims)
    K = max(1, min(int(p.blocks), S))
    seed = p.seed
    if seed is None:
        key = json.dumps([[f["code"], round(f["pace"]), round(f["skill"]), round(f.get("form") or 0, 1)] for f in field]
                         + [circ.get("name"), asdict(p)], default=str)
        seed = zlib.crc32(key.encode())
    rng = np.random.default_rng(seed)

    teams = sorted({f["team"] for f in field})
    T = len(teams)
    tidx = np.array([teams.index(f["team"]) for f in field])

    base0 = base_ratings(field, p.enhanced, p.team_w, p.driver_w, p.form_k)
    # parameter uncertainty: one rating perturbation per block, shared by every sim in the block
    block_id = np.arange(S) % K
    eps = rng.normal(0, p.rating_sd, (K, n)) if p.rating_sd > 0 else np.zeros((K, n))
    base = base0[None, :] + eps[block_id]  # (S,n)

    wz = _z(np.array([f["wet"] for f in field], float))
    rel = np.array([f["rel"] for f in field], float)
    w = float(np.clip(WETNESS[p.weather] * p.weather_w, 0, 1.5))
    wk = p.wet_influence / 0.6
    ot = float(np.clip(0.5 + p.track_w * (circ.get("overtaking", 0.5) - 0.5), 0, 1))
    tw = float(np.clip(0.5 + p.track_w * (circ.get("tyre_wear", 0.5) - 0.5), 0, 1))
    lap_ref = circ.get("lap_ref", 90.0)
    gap_scale = 0.0030 * lap_ref
    sprint = p.session == "sprint"
    sc_p = min(0.95, circ.get("sc_prob", 0.45) * p.track_w * (1 + 0.3 * w) * (p.sc_weight / 0.3) * (0.5 if sprint else 1.0)) if p.sc else 0.0

    # ---------------- qualifying-type simulation (always run: it also seeds the free part of the grid) -------------
    qmean = base + 0.6 * w * wz * wk
    q_sd_mult = 1.1 if p.session == "sprint_qualifying" else 1.0
    qpos, r1, r2, r3, in16, in10 = _qualifying(rng, qmean, w, p, S, n, tidx, T, q_sd_mult)

    fixed = p.grid_fixed is not None and any(g >= 0 for g in p.grid_fixed)
    locked = np.zeros(n, bool)
    gpos = qpos
    if fixed:
        fix = np.array(p.grid_fixed)
        locked = fix >= 0
        free = np.where(~locked)[0]
        slots = np.array(sorted(set(range(n)) - set(int(x) for x in fix if x >= 0)))
        gpos = np.tile(np.where(locked, fix, 0), (S, 1))
        if len(free):
            sd_q = 0.28 + 0.30 * p.chaos
            sc_noise = qmean[:, free] + rng.normal(0, sd_q, (S, len(free)))
            order = np.argsort(-sc_noise, axis=1)
            gp_free = np.empty((S, len(free)), int)
            np.put_along_axis(gp_free, order, np.broadcast_to(slots[: len(free)], (S, len(free))), axis=1)
            gpos[:, free] = gp_free

    # reported qualifying view must agree with a locked grid
    if fixed:
        qview = gpos
        in16v, in10v = gpos < round(n * 16 / 22), gpos < round(n * 10 / 22)
        for_sd = locked  # which drivers are fully determined
    else:
        qview, in16v, in10v = qpos, in16, in10

    warnings: list[str] = []
    grid_pace_corr = None
    if fixed and locked.mean() >= 0.5:
        # rank-correlation between the locked grid and the car/driver ratings; low/negative => a "what-if" grid
        idx = np.where(locked)[0]
        rk = np.argsort(np.argsort(-base0[idx]))
        grid_pace_corr = float(np.corrcoef(rk, gpos[:, idx].mean(0))[0, 1]) if len(idx) > 2 else None
        if grid_pace_corr is not None and grid_pace_corr < 0.3:
            warnings.append("The locked grid disagrees strongly with car/driver pace. With a known grid carrying >= 50% of the score, "
                            "the model will heavily favour the front of this grid (what-if mode).")
    sc_hit = np.zeros(S, bool)
    pace_extra: dict = {}
    gamma_used = 0.0
    if p.session in ("qualifying", "sprint_qualifying"):
        pos, dnf = qpos + 1, np.zeros((S, n), bool)
    elif p.session == "practice":
        one_m, long_m = PRACTICE_PROFILE.get(p.sub or "FP2", PRACTICE_PROFILE["FP2"])
        sd1 = (0.30 + 0.25 * p.chaos + 0.25) * one_m
        ps = base + 0.6 * w * wz * wk + rng.normal(0, sd1, (S, n))
        base_long = _z(0.8 * _z(np.array([f["pace"] for f in field], float)) + 0.2 * _z(np.array([f["skill"] for f in field], float)))
        ls = base_long[None, :] + eps[block_id] + 0.9 * w * wz * wk + rng.normal(0, (0.30 + 0.25 * p.chaos + 0.15) * long_m, (S, n))
        pos, dnf = _pos(ps) + 1, np.zeros((S, n), bool)
        gaps = (ps.max(1, keepdims=True) - ps) * gap_scale
        lgaps = (ls.max(1, keepdims=True) - ls) * gap_scale
        pace_extra = dict(pace_gap=(gaps.mean(0), np.percentile(gaps, 10, axis=0), np.percentile(gaps, 90, axis=0)),
                          long_gap=lgaps.mean(0), long_pos=_pos(ls) + 1)
    else:  # race | sprint
        # grid score: front-loaded (clean air / no traffic matter most at the front): -log(1+slot), z-scored over the field.
        # (a linear score treats P1-P2 like P11-P12 and under-rates pole; the shape is tunable, see changes.txt)
        _lg = -np.log1p(np.arange(n))
        gz = (-np.log1p(gpos) - _lg.mean()) / _lg.std()  # (S,n), best slot = highest
        G_free = (0.25 + 0.85 * (1 - ot)) * (p.grid_weight / 0.55)
        gamma = float(np.clip(p.grid_known_min + 0.30 * (1 - ot) * (p.grid_weight / 0.55) * (1.15 if sprint else 1.0), p.grid_known_min, 0.90))
        mix = (1 - gamma) * base + gamma * gz
        # re-standardise per simulation: a convex mix of two imperfectly correlated z-scores has < unit spread, which would
        # silently make a known-grid race *noisier* than a free one. Keep the deterministic spread equal to the base spread.
        mix = (mix - mix.mean(1, keepdims=True)) / np.maximum(mix.std(1, keepdims=True), 1e-9)
        free_det = base + G_free * (-gpos / max(n - 1, 1))
        det = np.where(locked[None, :], mix, free_det) + 0.9 * w * wz * wk
        gamma_used = gamma * locked.mean() if fixed else 0.0
        sc_hit = rng.random(S) < sc_p
        det = np.where(sc_hit[:, None], 0.7 * det, det)
        sd = (0.40 + 0.85 * p.chaos) * (1 + 0.5 * w) * (1 + 0.3 * (p.strategy_aggr - 0.5)) * (1 + 0.25 * (tw * p.deg_w - 0.5)) * (0.75 if sprint else 1.0)
        sd_t, sd_d = sd * np.sqrt(p.team_share), sd * np.sqrt(1 - p.team_share)
        noise = rng.normal(0, sd_d, (S, n)) + rng.normal(0, sd_t, (S, T))[:, tidx]
        noise = noise * np.where(sc_hit, 1.35, 1.0)[:, None]
        pdnf = 0.02 * (1 + w) + ((0.9 * (1 - rel) * (1 + 0.5 * w) * (p.reliability / 0.4)) if p.mech else 0)
        pdnf = pdnf * (0.35 if sprint else 1.0)
        dnf = rng.random((S, n)) < np.clip(pdnf, 0, 0.9)
        pos = _pos(np.where(dnf, det + noise - 100, det + noise)) + 1

    fin = ~dnf
    table = {"race": PTS_RACE, "sprint": PTS_SPRINT}.get(p.session, np.zeros(1, int))
    pts = np.where((pos <= len(table)) & fin, table[np.minimum(pos, len(table)) - 1], 0)

    fl = np.zeros(n)
    if p.session == "race":
        pz = _z(np.array([f["pace"] for f in field], float)); sz = _z(np.array([f["skill"] for f in field], float))
        s = 0.85 * pz + 0.15 * sz + rng.normal(0, 0.9, (S, n))
        fl = np.bincount(np.argmax(np.where(fin & (pos <= 12), s, -1e9), axis=1), minlength=n) / S

    win, podium = (pos == 1).mean(0), (pos <= 3).mean(0)
    ptsp = ((pos <= 10) & fin).mean(0)
    exp_pos = (pos * fin).sum(0) / np.maximum(fin.sum(0), 1)
    dist = np.stack([(pos == k).mean(0) for k in range(1, 11)], 1)
    pole = (qview == 0).mean(0)
    z = ZCI.get(round(p.ci, 2), 1.96)
    ci_mc = z * np.sqrt(win * (1 - win) / S)

    # ---- model (parameter) uncertainty via law of total variance over blocks ----
    wblk = np.stack([(pos[b::K] == 1).mean(0) for b in range(K)])  # (K,n)
    m = S / K
    mc_var_blk = win * (1 - win) / m  # sampling variance of one block's win frequency
    if K > 2:
        raw = wblk.var(0, ddof=1) - mc_var_blk
        se_raw = mc_var_blk * np.sqrt(2 / (K - 1))  # noise of the variance estimate itself
        var_model = np.where(raw > 2 * se_raw, raw, 0.0)  # report only what is statistically resolvable
    else:
        var_model = np.zeros(n)
    sd_model = np.sqrt(var_model)
    # total interval = parameter uncertainty + Monte-Carlo error (collapses to the MC interval where unresolved)
    tot_sd = np.sqrt(var_model + win * (1 - win) / S)
    win_lo, win_hi = np.clip(win - z * tot_sd, 0, 1), np.clip(win + z * tot_sd, 0, 1)

    gap_q = (qmean.mean(0).max() - qmean.mean(0)) * gap_scale
    avg_grid = (gpos.mean(0) + 1) if p.session in ("race", "sprint") else (qview.mean(0) + 1)

    # ---- extra distributions ----
    race_like = p.session in ("race", "sprint")
    full = np.stack([((pos == k) & fin).mean(0) for k in range(1, n + 1)], 1) if p.session != "practice" or True else None
    pvals = [0] + sorted(set(int(x) for x in table if x > 0)) if len(table) > 1 else [0]
    pts_dist = np.stack([(pts == v).mean(0) for v in pvals], 1)
    gain = (gpos + 1) - pos if race_like else np.zeros((S, n), int)
    avg_gain = (gain * fin).sum(0) / np.maximum(fin.sum(0), 1)
    p_gain, p_loss = ((gain > 0) & fin).mean(0), ((gain < 0) & fin).mean(0)

    extras: dict = {}
    if race_like:
        winner = np.argmax(pos == 1, axis=1)
        win_by_grid = np.bincount(gpos[np.arange(S), winner], minlength=n) / S
        podium_by_grid = np.bincount(gpos[(pos <= 3) & fin], minlength=n) / S  # expected podium finishers per slot
        ndnf = dnf.sum(1)
        carnage = ndnf >= 3
        scenario = dict(clean=float((~carnage & ~sc_hit).mean()), safety_car=float((~carnage & sc_hit).mean()), attritional=float(carnage.mean()))
        nsc = max(int(sc_hit.sum()), 1); nns = max(int((~sc_hit).sum()), 1)
        win_sc = ((pos == 1) & sc_hit[:, None]).sum(0) / nsc if sc_hit.any() else np.zeros(n)
        win_nosc = ((pos == 1) & ~sc_hit[:, None]).sum(0) / nns
        tp = np.stack([pts[:, tidx == t].sum(1) for t in range(T)], 1)
        team_rows = [dict(team=teams[t], mean=float(tp[:, t].mean()), p10=float(np.percentile(tp[:, t], 10)), p50=float(np.percentile(tp[:, t], 50)),
                          p90=float(np.percentile(tp[:, t], 90)), both_points=float(np.mean((pos[:, tidx == t] <= 10).all(1) & fin[:, tidx == t].all(1))),
                          win_share=float(win[tidx == t].sum())) for t in range(T)]
        extras = dict(win_by_grid=[float(x) for x in win_by_grid], podium_by_grid=[float(x) for x in podium_by_grid], scenario=scenario,
                      team_ranges=team_rows, pts_values=pvals)
        sc_rate = float(sc_hit.mean())
    else:
        win_sc = win_nosc = np.zeros(n)
        sc_rate = 0.0

    rows = []
    for i, f in enumerate(field):
        r = dict(code=f["code"], name=f["name"], team=f["team"], win=float(win[i]), win_ci=float(ci_mc[i]), win_mc_ci=float(ci_mc[i]),
                 win_lo=float(win_lo[i]), win_hi=float(win_hi[i]), win_model_sd=float(sd_model[i]),
                 podium=float(podium[i]), points_prob=float(ptsp[i]), dnf=float(dnf[:, i].mean()), avg_points=float(pts[:, i].mean()),
                 exp_pos=float(exp_pos[i]), fastest_lap=float(fl[i]), pole=float(pole[i]), avg_quali=float(qview[:, i].mean() + 1),
                 avg_grid=float(avg_grid[i]), reach_q2=float(in16v[:, i].mean() if fixed else in16[:, i].mean()),
                 reach_q3=float(in10v[:, i].mean() if fixed else in10[:, i].mean()), dist=[float(x) for x in dist[i]], gap=float(gap_q[i]),
                 full_dist=[float(x) for x in full[i]], pts_dist=[float(x) for x in pts_dist[i]], avg_gain=float(avg_gain[i]),
                 p_gain=float(p_gain[i]), p_loss=float(p_loss[i]), win_sc=float(win_sc[i]), win_nosc=float(win_nosc[i]),
                 grid_locked=bool(locked[i]))
        if p.session == "practice":
            r.update(pace_gap=float(pace_extra["pace_gap"][0][i]), pace_lo=float(pace_extra["pace_gap"][1][i]), pace_hi=float(pace_extra["pace_gap"][2][i]),
                     long_gap=float(pace_extra["long_gap"][i]), long_pos=float((pace_extra["long_pos"][:, i]).mean()),
                     top3=float((pos[:, i] <= 3).mean()), top10=float((pos[:, i] <= 10).mean()))
        rows.append(r)

    if p.session == "practice":
        key = lambda r: (r["pace_gap"], -r["win"])
    elif p.session in ("qualifying", "sprint_qualifying"):
        key = lambda r: (r["avg_quali"], -r["pole"])
    else:
        key = lambda r: (-r["avg_points"], -r["win"], r["exp_pos"])
    rows.sort(key=key)
    for k, r in enumerate(rows, 1):
        r["pos"] = k
    qual = sorted(rows, key=lambda r: r["avg_quali"])
    qualifying = [dict(pos=k, code=r["code"], pole=r["pole"], gap=r["gap"], time=fmt_lap(lap_ref + r["gap"]), q2=r["reach_q2"], q3=r["reach_q3"]) for k, r in enumerate(qual, 1)]

    # ---- per-segment qualifying view (Q1/Q2/Q3 or SQ1/SQ2/SQ3) ----
    pre = "SQ" if p.session == "sprint_qualifying" else "Q"
    seg = {}
    if p.session in ("qualifying", "sprint_qualifying"):
        a1 = r1.mean(0) + 1
        a2, f2 = _cond_mean(r2, in16)
        a3, f3 = _cond_mean(r3, in10)
        gq = gap_q
        s1 = [dict(code=field[i]["code"], avg_pos=float(a1[i]), p_advance=float(in16[:, i].mean()), p_eliminated=float(1 - in16[:, i].mean()),
                   time=fmt_lap(lap_ref + gq[i] + SEG_OFFSET[1])) for i in range(n)]
        s2 = [dict(code=field[i]["code"], avg_pos=_nn(a2[i]), p_reach=float(f2[i]), p_advance=float(in10[:, i].mean()), p_eliminated=float((in16 & ~in10)[:, i].mean()),
                  time=fmt_lap(lap_ref + gq[i] + SEG_OFFSET[2])) for i in range(n) if f2[i] > 0.01]
        s3 = [dict(code=field[i]["code"], avg_pos=_nn(a3[i]), p_reach=float(f3[i]), pole=float((r3[:, i] == 0)[in10[:, i]].mean() * f3[i]) if f3[i] > 0 else 0.0,
                   front_row=float(((r3[:, i] <= 1) & in10[:, i]).mean()), time=fmt_lap(lap_ref + gq[i] + SEG_OFFSET[3])) for i in range(n) if f3[i] > 0.01]
        seg = {f"{pre}1": sorted(s1, key=lambda r: r["avg_pos"]), f"{pre}2": sorted(s2, key=lambda r: r["avg_pos"]), f"{pre}3": sorted(s3, key=lambda r: r["avg_pos"])}
        # teammate qualifying battle: P(first driver of the team ahead of the second)
        battle = []
        for t in range(T):
            ids = np.where(tidx == t)[0]
            if len(ids) == 2:
                a, b = ids
                battle.append(dict(team=teams[t], a=field[a]["code"], b=field[b]["code"], p_a_ahead=float((qpos[:, a] < qpos[:, b]).mean())))
        extras["teammate_battle"] = battle
        extras["both_in_q3"] = [dict(team=teams[t], p=float(in10[:, tidx == t].all(1).mean())) for t in range(T)]

    # ---- confidence & factors ----
    wp = np.clip(win, 1e-12, 1); wp = wp / wp.sum()
    sharp = float(np.clip(1 + (wp * np.log(wp)).sum() / np.log(n), 0, 1))
    conf = float(np.clip(0.45 + 0.35 * sharp + 0.12 * min(1.0, S / 10000) ** 0.5 - 0.18 * min(w, 1) - 0.10 * p.chaos, 0.2, 0.95))
    pz_ = _z(np.array([f["pace"] for f in field], float)); sz_ = _z(np.array([f["skill"] for f in field], float))
    comp = {"Team Performance": float(np.std(p.team_w * pz_)),
            "Driver Form": float(np.std(p.driver_w * sz_ + (np.clip(p.form_k / 64, 0, 1) if p.enhanced else 0.15) * base0)),
            "Weather": float(np.std(0.9 * w * wk * wz)) if w > 0 else 0.0}
    rest = sum(comp.values()) or 1.0
    g_share = gamma_used if race_like else 0.0
    if race_like and not fixed:
        g_share = float(np.std(G_free * (-np.arange(n) / max(n - 1, 1))) / (np.std(G_free * (-np.arange(n) / max(n - 1, 1))) + rest))
    comp = {k: v / rest * (1 - g_share) for k, v in comp.items()}
    comp["Starting Grid"] = g_share
    tot = sum(comp.values()) or 1.0
    lvl = lambda s: "High" if s >= 0.33 else "Medium" if s >= 0.18 else "Low"
    factors = [dict(name=k, level=lvl(v / tot), share=float(v / tot)) for k, v in comp.items()]
    factors.append(dict(name="Historical Data", level="High" if rounds_of_data >= 10 else "Medium" if rounds_of_data >= 4 else "Low", share=min(1.0, rounds_of_data / 23)))

    # ---- strategy (heuristic; unchanged logic) ----
    ag = p.strategy_aggr - 0.5
    if sprint:
        names = [("No stop", "Medium → (no stop)"), ("No stop", "Hard → (no stop)"), ("1 Stop", "Soft → Medium")]
        u = np.array([0.9 - 0.4 * tw * p.deg_w, 0.5 + 0.2 * tw * p.deg_w, 0.1 + 0.4 * ot + 1.0 * ag])
    elif w >= 0.75:
        names = [("1 Stop", "Intermediate → Medium"), ("2 Stops", "Intermediate → Intermediate → Medium"), ("1 Stop", "Full Wet → Intermediate")]
        u = np.array([0.7 - 0.6 * ag, 0.55 + 0.3 * tw * p.deg_w, 0.2 + 1.2 * ag])
    else:
        names = [("1 Stop", "Medium → Hard"), ("2 Stops", "Medium → Medium → Hard"), ("1 Stop", "Soft → Hard")]
        u = np.array([0.9 - 1.0 * tw * p.deg_w - 0.6 * ag, 0.2 + 0.9 * tw * p.deg_w + 0.35 * sc_p, 0.1 + 0.5 * (1 - tw) + 0.4 * ot - 0.3 * w + 1.2 * ag])
    e = np.exp(3 * (u - u.max())); pr = np.round(100 * e / e.sum()).astype(int); pr[0] += 100 - pr.sum()
    strategies = [dict(name=f"Strategy {i + 1}", stops=a, tyres=b, prob=int(pr[i]), optimal=bool(i == int(np.argmax(pr)))) for i, (a, b) in enumerate(names)]

    out = dict(drivers=rows, qualifying=qualifying, quali_segments=seg, strategies=strategies, factors=factors, confidence=conf, sharpness=sharp,
               safety_car_rate=sc_rate, safety_car_prob=float(sc_p), seed=int(seed), weather_used=p.weather, session=p.session, sub=p.sub,
               grid_influence=float(gamma_used), grid_locked_count=int(locked.sum()), grid_pace_corr=grid_pace_corr, warnings=warnings, **extras)
    if want_samples:  # internal use (fantasy): not JSON-serialisable on purpose
        out["_samples"] = dict(pts=pts, pos=pos, fin=fin, codes=[f["code"] for f in field])
    return out


def pair_stats(samples: dict, a: str, b: str) -> dict:
    """Head-to-head from simulation samples (call predict(..., want_samples=True) first)."""
    codes = samples["codes"]; ia, ib = codes.index(a), codes.index(b)
    pos, fin = samples["pos"], samples["fin"]
    ahead = np.where(fin[:, ia] & ~fin[:, ib], True, np.where(~fin[:, ia] & fin[:, ib], False, pos[:, ia] < pos[:, ib]))
    both = fin[:, ia] & fin[:, ib]
    return dict(p_a_ahead=float(ahead.mean()), p_b_ahead=float(1 - ahead.mean()),
                p_a_ahead_both_finish=float((pos[both, ia] < pos[both, ib]).mean()) if both.any() else None,
                p_both_dnf=float((~fin[:, ia] & ~fin[:, ib]).mean()), p_both_podium=float(((pos[:, ia] <= 3) & (pos[:, ib] <= 3) & both).mean()),
                p_both_points=float(((pos[:, ia] <= 10) & (pos[:, ib] <= 10) & both).mean()))
