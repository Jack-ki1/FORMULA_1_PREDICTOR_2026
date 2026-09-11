# F1 Predictor

A prediction + fantasy-league app for the 2026/2027 F1 seasons: Monte
Carlo race simulations, ML-assisted probability models, head-to-head
driver comparisons, and a season-long pick-em leaderboard.

This is the result of migrating an original Flask monolith into a real
frontend/backend split — see [`PLAN.md`](PLAN.md) for the full research
and design rationale, and [`AUDIT.md`](AUDIT.md) for the history of bugs
found and fixed in the original codebase before this migration. This
README is the practical "how do I run/deploy this" reference.

## Architecture

```
apps/web/       Next.js 15 + TypeScript frontend (deployed to Vercel)
apps/api/       FastAPI backend — Monte Carlo engine, ML models, DB,
                auth (deployed to Vercel as its own project, see below)
apps/ingest/    Scheduled jobs: sync live data, precompute predictions,
                score fantasy-league picks (run by GitHub Actions)
packages/api-types/  TypeScript types generated from apps/api's OpenAPI
                     schema — the frontend/backend contract
```

**One adjustment from the original plan worth flagging up front:**
[`PLAN.md`](PLAN.md) originally described one Vercel project hosting
both the frontend and the Python API together (via a `/api/*` rewrite
inside a single deployment). Building it, the cleaner and more robust
setup turned out to be **two separate Vercel projects** in this one
repo — one with Root Directory `apps/web`, one with Root Directory
`apps/api` — rather than fighting Vercel's monorepo multi-runtime
config. Same result (both still deploy from this repo, both still free,
both still "just Vercel"), just two projects instead of one. Everything
else in `PLAN.md` (Neon, Upstash, GitHub Actions for scheduling, the
precompute-predictions architecture) is unchanged.

Data flow: GitHub Actions runs `apps/ingest` on a schedule → writes to
Neon Postgres → `apps/api` serves fast reads from Postgres → `apps/web`
renders them. The one on-demand compute path left in the request cycle
is the "what-if" slider panel (`POST /api/predictions/{id}/recompute`),
by design — see `PLAN.md` §3.

## Local development

You need Python 3.12+, Node 20+, and (optionally) Docker if you'd rather
run Postgres/Redis locally than use SQLite/in-memory fallbacks — nothing
below requires it.

### Backend

```bash
cd apps/api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env    # defaults to local SQLite — no further setup needed
alembic upgrade head    # creates f1_predictions.db with the full schema

uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/api/docs
```

Run the test suite:

```bash
pip install pytest httpx
pytest tests/ -v
```

### Frontend

```bash
cd apps/web
npm install
cp .env.example .env.local   # defaults already point at localhost:8000
npm run dev
# http://localhost:3000
```

Sign-in without setting up a real GitHub OAuth app: in development, an
extra "Dev login" option appears on `/account` that mints an account
from just a display name (see `lib/auth.ts` — this provider is never
registered when `NODE_ENV=production`).

### Ingestion scripts (optional locally)

```bash
cd apps/ingest
export DATABASE_URL=sqlite:///../api/f1_predictions.db
python sync_data.py            # warms standings cache, records a freshness marker
python run_predictions.py      # precomputes predictions for every upcoming race
python evaluate_accuracy.py    # scores any pending picks for completed races
```

## Deploying (all free tiers, see `PLAN.md` §1 for the research behind these choices)

1. **Neon** (Postgres) — create a project, copy the **pooled** connection
   string (the one with `-pooler` in the hostname — required for
   serverless; see `apps/api/database/db.py`'s comments on why).
2. **Upstash** (Redis) — create a database, copy the `rediss://` URL.
3. **Vercel project 1 — API**: import this repo, set Root Directory to
   `apps/api`. Environment variables: `DATABASE_URL` (Neon), `REDIS_URL`
   (Upstash), `AUTH_SYNC_SECRET` (generate a random string), `SECRET_KEY`
   (another random string), `ALLOWED_ORIGINS` (your web project's URL,
   added after step 4). Deploy. Then run `alembic upgrade head` against
   the Neon URL once, from your machine or CI, to create the schema.
4. **Vercel project 2 — Web**: import this repo again, set Root
   Directory to `apps/web`. Environment variables: `NEXT_PUBLIC_API_URL`
   and `API_INTERNAL_URL` (project 1's URL + `/api`), `AUTH_SYNC_SECRET`
   (same value as project 1), `AUTH_SECRET` (`npx auth secret`),
   `AUTH_GITHUB_ID`/`AUTH_GITHUB_SECRET` (from a GitHub OAuth App whose
   callback URL is `https://<this-project>.vercel.app/api/auth/callback/github`).
   Deploy.
5. Go back to **project 1** and set `ALLOWED_ORIGINS` to project 2's
   real URL, redeploy.
6. **GitHub Actions**: add repo secrets `DATABASE_URL` (same Neon URL).
   The `ingest-schedule.yml` workflow runs hourly by default — tune the
   cron expression for denser polling on race weekends, or trigger it
   manually from the Actions tab.

### Fallback: API on Render instead of Vercel (PLAN.md §9)

If the Python function bundle (numpy/scipy/scikit-learn/xgboost/
lightgbm/fastf1/weasyprint all together) ever gets uncomfortably large
or slow to cold-start on Vercel: deploy `apps/api` to Render's free web
service instead (same code, `uvicorn main:app --host 0.0.0.0 --port
$PORT` as the start command), and point the web project's
`NEXT_PUBLIC_API_URL`/`API_INTERNAL_URL` at Render's URL. Nothing else
changes.

## What's built vs. what's a documented next step

Built and tested end-to-end (backend test suite + a real frontend build
+ a live cross-service smoke test, all reproduced in this repo's CI):

- All prediction/standings/H2H/constructors/reports endpoints, ported
  1:1 from the original Flask blueprints
- Real Alembic migrations (replacing the original's two competing
  hand-rolled schema-creation paths — see `AUDIT.md` M-3)
- A consolidated single database module (was two duplicated ones)
- Real JWT auth wired to an actual sign-in flow (was dead code with no
  login route at all — `AUDIT.md` B-6)
- A working Redis-backed rate limiter (the original's rate limiter
  stored counters in Flask's per-request `g`, so it silently never
  limited anything — this is fixed, not just ported)
- The fantasy league feature end-to-end: sign in, submit a pick, get
  scored after the race, see the leaderboard — built almost entirely on
  top of `UserPick`/`LeaderboardEntry` tables and
  `engine/fantasy_scoring.py` logic that existed in the original
  codebase but nothing ever called

Explicitly **not** built, with the reasoning documented rather than
silently skipped:

- **Live qualifying-result ingestion for "pole" picks**
  (`apps/ingest/evaluate_accuracy.py`) — race results are fully wired
  up; pole picks correctly stay in `pending` status until qualifying
  result parsing is added. Small, well-scoped follow-up.
- **Full relational ingestion** of Jolpica/OpenF1 data into
  `database/models.py`'s Team/Driver/Circuit/Race/QualifyingResult/
  RaceResult tables — the prediction engine reads from the static
  `config/team_driver_lineup_2026.py`/`data/calendar_2026.py` today, not
  those tables, so building a full ingestion mapper for them now would
  have no consumer. `apps/ingest/sync_data.py` documents this scope
  decision inline.
- **`packages/api-types` is generated but not yet consumed** — `apps/web`'s
  hand-written API types match it today (both were written against the
  same routers) but nothing enforces that they stay in sync. Switching
  `lib/api-client.ts` to import from `@f1-predictor/api-types` (e.g. via
  `openapi-fetch`) closes that gap — see that package's README.
- **Live Ergast/Jolpica JSON parsing in `evaluate_accuracy.py`** is
  written to the documented schema but only exercised against the local
  fallback data in this environment (no network access to the live
  Jolpica API from where this was built) — it degrades to skipping a
  race and logging a warning rather than crashing if the live shape
  doesn't parse as expected, but is worth a real smoke test against
  live data before relying on it for a real race weekend.
- **Prometheus-style metrics** — replaced with a small real `/api/status`
  JSON endpoint instead of porting the original's Prometheus exporter,
  which was never wired up in the original app anyway and would need a
  Prometheus server (which nothing in this stack runs) to be useful.
  Documented in `PLAN.md` §6.
