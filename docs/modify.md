# modify.md

This file did not exist anywhere in the repository even though roughly 25 code
comments across the backend cite it by section number (`modify.md section 1.2`,
`modify.md s2`, and so on) as the reason a piece of code is written the way it
is. Every one of those citations pointed at nothing — anyone reading the
source, including a new contributor or an AI assistant working on the code,
hit a dead reference.

This document reconstructs those sections from the evidence actually left
behind in the comments themselves (each entry below cites the file where the
original comment lives). Nothing here is invented; it's the fixes the
codebase's own comments already describe, given a home so the citations
resolve to something real. If the team that owns this project has the actual
original `modify.md`, replace this file with it — the section numbers below
were chosen to match what the existing comments already reference.

## Section 1 — Correctness fixes

### 1.1 — Typecheck-level fixes
`frontend/src/__tests__/regressions.test.ts` guards a small set of TypeScript
casing/typing mistakes (e.g. a CSS-in-JS property that must be
`webkitTextSizeAdjust`, not `WebkitTextSizeAdjust`, to satisfy the
`CSSProperties` type). Low-severity, but the kind of thing that silently
breaks a build on a stricter TypeScript version.

### 1.2 — The `SETTINGS_ADMIN_TOKEN` / `SECRET_KEY` fallback
`backend/app/api/routes/settings.py` used to fall back to `SECRET_KEY` when
`SETTINGS_ADMIN_TOKEN` was unset. `SECRET_KEY` itself defaults to a
well-known placeholder value in `backend/app/config/settings.py` for local
development. The combination meant that, on any deployment where an operator
set neither variable, anyone could send that well-known placeholder as the
`X-Admin-Token` header and flip admin-only settings (including
`RATE_LIMIT_ENABLED`) on a public instance. Reproduced against a live
instance: `POST /api/v1/settings {"RATE_LIMIT_ENABLED": false}` with that
header returned `200`.

Fix: `SETTINGS_ADMIN_TOKEN` no longer falls back to `SECRET_KEY`. If it's
unset, admin-only fields are simply unwritable (`ADMIN_DISABLED`) rather than
writable with a guessable value. The `/api/v1/settings/reset` endpoint had
the identical fallback and was fixed the same way — resetting settings was
an equally valid way to bypass the intended protection.

### 1.4 — `None` reaching a `.upper()` / string method
Several report/export code paths built a dict with `{"key": other.get("key")}`.
`dict.get` only returns its default when the key is *missing* — if the key
exists with a value of `None` (which happened when an upstream caller omitted
`target_id`), `.get("target_id", "winner")` still returns `None`, and the
first `.upper()` or similar call downstream throws
`'NoneType' object has no attribute 'upper'`, surfaced to the client as an
HTTP 500. Fixed in `report_service.py` and `pdf_generator.py` by treating a
present-but-`None` value the same as a missing one (`data.get('race_id') or
'Race'`, not a bare `.get('race_id', 'Race')`).

### 1.5 — The 22 vs 23 driver grid
The 2026 grid is 11 teams × 2 drivers = 22. An earlier version of the driver
lineup listed Racing Bulls with three drivers (a leftover from a
mid-2025-season substitution), so the grid silently ran at 23 entrants
everywhere that number was hardcoded — diluting every Monte Carlo
probability by one extra, non-existent car. Fixed by deriving `grid_size()`
in `backend/app/config/constants.py` from the actual lineup
(`team_driver_lineup_2026.py`, now exactly 2 drivers per team) instead of a
hardcoded literal, so the two can't drift apart again. The frontend
regression tests (`regressions.test.ts`, "grid size consistency") assert the
grid editor derives its position count from the driver list rather than a
literal `23`.

## Section 2 — Health checks that were honest about "healthy"

Several data providers (see `backend/app/data/providers/`) catch their own
upstream errors and return a `local_seed` fallback with HTTP 200 rather than
raising. That's the right behavior for the request itself — the caller still
gets a response — but it meant `health()` only ever asked "did the call
throw?", never "did we actually get live data?", so a health check reported
"healthy" even when every single request was silently being served from the
2026 offline seed data with zero live upstream reachable.

Fixed by tracking `last_call_used_fallback` per provider
(`data/providers/base.py`) and aggregating honestly in the registry
(`data/providers/registry.py`): if *no* provider served live data, the whole
federation reports `degraded`, not `healthy`. This is what stops a
fully-offline install from showing a green status. `system.py`'s
`/api/v1/system/provenance/{race_id}` endpoint exposes the same
per-race distinction so a client can tell a prediction backed by live
Jolpica data apart from one served out of the offline seed.

## Section 3 — Duplicated config, and one truly dead module

`requirements.txt` and `.env.example` each existed twice — once at the repo
root, once under `backend/` — as byte-for-byte duplicates. Every dependency
or config change had to be made in both places or the two silently diverged
(this is how `pytest` ended up missing from one copy of `requirements.txt`
while `pyproject.toml` still declared it as a dependency). Fixed by making
the root file the single source of truth and having `backend/requirements.txt`
and `backend/.env.example` reference it instead of duplicating it.

The historical `FLASK_ENV` / `FLASK_HOST` / `FLASK_PORT` trio in
`.env.example` was a leftover from before the backend was rewritten from
Flask to FastAPI — the runtime stopped reading those variables long ago, but
`.env.example` kept documenting them, so a new deployment would set three
variables that did nothing. Removed.

Separately: `backend/app/engine/experimental/safety_car_model.py` has zero
references anywhere in the repository — no production import, no training
import, no test. It's kept in an `experimental/` folder specifically so that
question is answered by the folder name rather than by a repo-wide grep
someone has to remember to run before touching it.

## Section 4 — Fail loud, not quietly wrong

`backend/app/api/routes/fantasy.py`'s scoring endpoint accepted a driver's
race-finish field under one specific key. A reasonable-but-differently-named
field — `finish_position` instead of `race_position` — fell through to a
default of 12th and returned a plausible-looking, all-zero-ish score with
HTTP 200. No error, just a quietly wrong answer. Fixed by accepting a small
set of reasonable aliases (`_RACE_POSITION_ALIASES`) explicitly, so a genuine
typo outside that set fails loudly instead of returning a number that looks
fine.

## Section 5 — Real recorded data, or an explicit null — never a fabricated verdict

A cluster of endpoints share one rule: when there's something real to report,
report it; when there isn't, say so explicitly rather than showing something
that merely *looks* like an answer.

- `history_service.py` — prediction-vs-actual comparison used to always
  render a check or cross mark even when there was no recorded result for
  that race yet, which meant a fabricated verdict. It now reads real
  recorded results from `season_2026` and returns `actual: null` when there
  is genuinely nothing to compare against.
- `h2h_service.py` / `routes/h2h.py`'s `/history` endpoint — counts, per
  completed round, which of two drivers actually finished ahead, from
  recorded results only. Distinct from `/compare`, which is a
  ratings-derived *probability*, not a record of what happened. If neither
  driver appears in any recorded result, the caller gets an empty list and
  an explicit note, never invented rounds.
- `projection_service.py` / `routes/standings.py`'s championship projection
  — reuses the same production Monte Carlo engine used for single-race
  predictions, just run across every remaining round of the calendar
  instead of one race, so a title-probability number rests on the same
  model as everything else instead of a separate, unaudited code path.
- `routes/predictions.py`'s `/history/{race_id}` — actual-vs-predicted for
  one specific race, same "real data or explicit null" rule.
- `routes/fantasy.py`'s `FANTASY_RULES_2026` and `/transfers` — the fantasy
  game's structural constraints ($100M budget cap, 5+2 roster, the 6 chips,
  the $3M price floor, the net-transfer rule) are defined once, here, as the
  single source of truth. The frontend previously hardcoded its own guesses
  at these numbers separately from whatever the backend actually enforced.

---
*Reconstructed from in-repo comment evidence. If a real `modify.md` exists
outside version control, it supersedes this file.*
