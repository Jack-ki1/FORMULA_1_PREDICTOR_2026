# F1 Predictor — Frontend/Backend Split & Deployment Plan

**Goal:** turn the current Flask monolith into a real frontend/backend
application — TypeScript frontend, Python backend keeping all the ML/
Monte Carlo work — deployable for $0/month on Vercel (or a close second
choice), while using the chance to make the product genuinely more
realistic and advanced (user accounts, a fantasy league, live sessions,
model explainability), without the plumbing becoming its own project.

This doc is deliberately long because "keep it simple" and "make it
more advanced" pull in opposite directions, and the only way to satisfy
both is to be explicit about *what* stays simple (infrastructure, deploy
story, number of moving pieces) versus *what* gets to be ambitious
(features, data depth, UX). Read it top to bottom once; after that,
each section stands alone as a reference while building.

---

## 1. Research findings — what's actually true about free hosting in Sept 2026

I looked this up rather than relying on memory, since hosting free tiers
change constantly and my training predates some of this. Verified against
Vercel's own docs and cross-checked pricing/limits pages as of this month:

| Platform | Current free tier reality (Sept 2026) | Verdict |
|---|---|---|
| **Vercel Hobby** | Next.js frontend: genuinely free, no card, no expiry (commercial use technically requires Pro, but nobody enforces this for a side project). **Python Functions**: 2 GB RAM, **300s max duration** (this used to be 10s — it's not anymore), 500 MB uncompressed bundle, **5 GB with "Large Functions"** (enabled by default for any project created after June 30, 2026 — i.e. yours). Cron: only **2 cron jobs, once/day, fires sometime within the chosen hour**, UTC only. | **Primary target.** 300s + 2GB + 5GB bundle is enough for the Monte Carlo/ML workload. The cron cap is the one real gap — solved below with GitHub Actions. |
| **Render** | Still has a genuine no-card free web service tier (512MB RAM) — but it **sleeps after 15 min idle, ~30–50s cold start** to wake. Free Postgres exists but is time-limited (expires and needs recreation). | Good **fallback/Plan B** if the Vercel Python bundle ever gets too unwieldy — same FastAPI code, different host, see §9. Not great as a *primary* target because of the sleep/cold-start UX for something the user will pull up on a race weekend. |
| **Railway / Fly.io** | Both effectively killed their free tiers (Railway: one-time $5 trial credit only; Fly.io: 2-hour trial for new accounts). | Not viable as a genuinely free option anymore. Skip. |
| **Neon (Postgres)** | Real, permanent free tier: 0.5 GB storage, 100 compute-hours/month, scale-to-zero, branching. | **Primary database.** Plenty for this app's data volume (a season of race/quali/standings data is tiny). |
| **Upstash (Redis)** | Real, permanent free tier: 256 MB, 500k commands/month, reachable over HTTP (works from serverless without a persistent TCP connection, which matters — Vercel functions are short-lived). | **Primary cache**, drop-in replacement for the code's existing `cache/redis.py` abstraction. |
| **GitHub Actions** | Free scheduled workflows (`cron:` trigger) on public *or* private repos within generous free minutes, any cadence you want. | **Cron workaround.** Used to trigger data ingestion more than once a day, since Vercel Hobby cron can't.

**Bottom line:** a $0/month stack of **Vercel (frontend + Python API) + Neon (Postgres) + Upstash (Redis) + GitHub Actions (scheduling)** is realistic today, and is what the rest of this plan targets. Render is documented as the fallback in case the Python function bundle becomes painful — the plan is written so switching costs about an hour, not a rewrite.

---

## 2. Target architecture

```
┌─────────────────────────────┐         ┌──────────────────────────────┐
│   apps/web  (Next.js/TS)    │  HTTPS  │   apps/api  (FastAPI/Python)  │
│   Vercel — static + edge    │────────▶│   Vercel Python Functions     │
│   React 19, Tailwind,       │  JSON   │   (same ASGI app also runs    │
│   shadcn/ui, TanStack Query │◀────────│   standalone on Render if     │
└──────────────┬───────────────┘         │   ever needed — see §9)       │
               │ NextAuth session         └───────────────┬────────────────┘
               ▼                                          │ SQLAlchemy (async)
     ┌───────────────────┐                                ▼
     │  Neon Postgres     │◀───────── reads/writes ───────┤
     │  (users, races,    │                                │
     │   predictions,     │                Upstash Redis   │
     │   picks, leaderboard)               (cache, rate     │
     └────────┬────────────┘               limiting)       │
              ▲                                             │
              │ upserts                                     │
     ┌────────┴─────────────────────┐                       │
     │  apps/ingest (Python,        │                       │
     │  scheduled by GitHub Actions)│──── fetches from ──────┘
     │  Jolpica / OpenF1 / FastF1   │
     └───────────────────────────────┘
```

Three deployable units, one repo:

1. **`apps/web`** — Next.js 15 (App Router) + TypeScript. Everything the
   user's browser talks to. Deployed as the "main" Vercel project.
2. **`apps/api`** — FastAPI (Python 3.12), wraps the *existing* `engine/`,
   `data/`, `database/` code almost unchanged. Deployed as Vercel Python
   Functions **inside the same Vercel project** (via `/api` routing —
   Vercel natively supports a Python backend living alongside a Next.js
   frontend in one project, one `vercel deploy`).
3. **`apps/ingest`** — a thin Python entry point that reuses `apps/api`'s
   ingestion/prediction code, invoked on a schedule by GitHub Actions
   (not Vercel Cron, because of the 2-jobs/once-a-day cap) to pull fresh
   data and pre-compute predictions, writing results to Postgres so the
   API layer almost never computes on the request path.

This is **one repo, one Vercel project, two free managed data services,
one GitHub Actions workflow file.** That's the entire infrastructure —
deliberately not more than that.

---

## 3. Why precompute instead of predict-on-request?

The current Flask app computes a fresh Monte Carlo simulation on every
`POST /predict-session` call. That's fine for a demo; it's the wrong
default for a real product, for two reasons:

- **UX**: a visitor loading the dashboard shouldn't wait 1–3 seconds for
  a simulation before seeing anything.
- **Free-tier economics**: Vercel Hobby bills active CPU time. Running
  the same simulation for every visitor of a popular race weekend burns
  far more compute than running it once and serving the cached result.

So the plan flips the current architecture's default: **`apps/ingest`
runs the Monte Carlo + ML pipeline once per data update** (new quali
result, new standings, etc.) and writes the output to
Postgres (`predictions` table, already in `database/models.py`/
`models/prediction.py` — reused as-is). `apps/api` serves those rows
directly — sub-100ms responses. The **on-demand path stays**, just
demoted to a secondary, explicitly-labeled feature: a "what-if" panel
where a signed-in user can nudge chaos/wet-weather/reliability sliders
and get a *live* recompute (this is the one place a real-time Monte
Carlo run still makes sense product-wise, and it's rare enough per user
that the compute cost is trivial).

---

## 4. Repo layout

```
f1-predictor/
├── apps/
│   ├── web/                      # Next.js 15 + TypeScript
│   │   ├── app/                  # App Router pages (see §6 mapping)
│   │   ├── components/
│   │   ├── lib/
│   │   │   ├── api-client.ts     # generated from the API's OpenAPI schema
│   │   │   └── auth.ts           # Auth.js config
│   │   └── package.json
│   │
│   ├── api/                      # FastAPI — this IS today's Flask app,
│   │   │                         # restructured, not rewritten
│   │   ├── main.py               # FastAPI app + /api/* routers
│   │   ├── routers/              # 1:1 with today's dashboard/blueprints/*
│   │   ├── engine/                → moved from repo root, ~unchanged
│   │   ├── data/                  → moved from repo root, ~unchanged
│   │   ├── database/              → moved from repo root, SQLite→Postgres
│   │   ├── models/                → moved from repo root, unchanged
│   │   ├── security/              → moved from repo root, now actually wired up
│   │   └── requirements.txt
│   │
│   └── ingest/                   # thin scheduled-job entrypoints
│       ├── sync_data.py          # pulls Jolpica/OpenF1/FastF1 → Postgres
│       ├── run_predictions.py    # (re)computes predictions → Postgres
│       └── evaluate_accuracy.py  # post-race scoring, from scripts/measure_accuracy.py
│
├── packages/
│   └── api-types/                # generated TS types from FastAPI's OpenAPI
│                                  # schema (openapi-typescript) — the contract
│                                  # between web and api, regenerated in CI
│
├── .github/workflows/
│   ├── ingest-schedule.yml       # cron: every N minutes on race weekends,
│   │                             # hourly otherwise (see §8)
│   └── ci.yml                    # lint/type-check/test both apps on PRs
│
├── vercel.json                   # routes /api/* to apps/api, rest to apps/web
├── AUDIT.md                      # kept — historical record of the Flask-era fixes
└── README.md
```

`apps/api`'s Python code is intentionally almost a straight move of the
current `engine/`, `data/`, `database/`, `models/`, `security/`
directories — the audit already made them installable, correct, and
tested. The rewrite effort goes into the *edges* (how requests reach
them, how they're persisted, how the frontend consumes them), not into
re-deriving Monte Carlo logic that already works.

---

## 5. Data layer changes

| Change | From | To | Why |
|---|---|---|---|
| Database engine | SQLite (`f1_predictions.db`, checked into git) | **Neon Postgres** | Serverless functions have no persistent disk between invocations; SQLite-on-disk doesn't survive a redeploy or even a second invocation reliably. Postgres is the only option that's both persistent and reachable from a stateless function. |
| Migrations | Hand-rolled raw SQL (`migrations/_001_initial_schema.py`) + separate `Base.metadata.create_all()` path (the two-migration-systems issue flagged in `AUDIT.md` M-3) | **Alembic**, generated from the existing SQLAlchemy models in `database/models.py` + `models/prediction.py` | One source of truth, real up/down migrations, `alembic upgrade head` in CI before each deploy. This retires both of the old ad-hoc systems in one move instead of trying to reconcile them. |
| Connection pooling | Two separate hand-rolled engines (`database/connection.py` vs `database/client.py`, flagged in `AUDIT.md` M-3) | **One** async SQLAlchemy engine using Neon's pooled connection string (`-pooler` suffix, required for serverless — Neon docs are explicit that unpooled connections exhaust fast under Lambda-style concurrency) | Collapses the duplication the audit flagged, and serverless *requires* getting this right or you'll see "too many connections" errors under any real traffic. |
| Cache | `cache/redis.py`, already redis-or-in-memory-fallback | **Same code, pointed at Upstash** (works either over Upstash's Redis-protocol endpoint from a long-lived process, or its REST API from an edge function) | This file survives the migration essentially untouched — it's the one piece of the current app already written the right way. |
| Tables actually used | `UserPick`, `Leaderboard` exist in `database/models.py` today but **nothing in the app ever reads or writes them** | **Activated** — see §7 (fantasy league feature) | Free win: the schema for a real feature already exists, it's just never been wired to anything. |

---

## 6. Backend: Flask blueprints → FastAPI routers

Direct mapping, so nothing gets lost or silently dropped:

| Current Flask blueprint | New FastAPI router | Notes |
|---|---|---|
| `dashboard/blueprints/landing.py` | *(removed — becomes a Next.js page, no API needed)* | Static content lives in the frontend now. |
| `dashboard/blueprints/predictions.py` | `routers/predictions.py` | `GET /api/predictions/{race_id}` now reads precomputed rows (§3) instead of running Monte Carlo inline; `POST /api/predictions/{race_id}/what-if` keeps the on-demand path for the slider feature. |
| `dashboard/blueprints/standings.py` | `routers/standings.py` | Same logic, thinner — data comes from Postgres, refreshed by `apps/ingest`, not fetched live per-request. |
| `dashboard/blueprints/h2h.py` | `routers/h2h.py` | Unchanged logic. |
| `dashboard/blueprints/constructors.py` | `routers/constructors.py` | Unchanged logic. |
| `dashboard/blueprints/analytics_settings.py` | `routers/settings.py` | Chaos/wet-weather/reliability sliders — now scoped per-user (ties into auth, §7) instead of global server state. |
| `dashboard/blueprints/reports.py` | `routers/reports.py` | CSV/PDF/Excel export — same `reports/` generators, called from an API route instead of a Flask view; frontend triggers a download via a signed URL. |
| `dashboard/blueprints/dashboard.py`, `health.py` (previously dead code, see `AUDIT.md` B-6/M-1) | `routers/health.py` (a real, minimal one) + **deleted** the auth-locked duplicate entirely | No reason to carry forward code that was already flagged as dead and broken; a FastAPI health route is 5 lines. |
| `security/auth.py`, `security/middleware.py` (real code, previously never wired to anything — `AUDIT.md` B-6) | `routers/auth.py` + FastAPI dependency (`Depends(get_current_user)`) | **Finally wired up for real** — this is where the audit's "flagged, not fixed" item gets resolved, because now there's an actual login flow (Auth.js on the frontend, issuing/verifying the same JWTs) to attach it to. |
| `monitoring/blueprint.py` (dead code — `AUDIT.md` m-3) | `routers/status.py` — a small, real "data freshness / model version / last ingest run" JSON endpoint, rendered as a status strip in the UI | Prometheus's `/metrics` format is overkill for a project with no Prometheus server to scrape it; a plain JSON status endpoint gets 90% of the value (page uptime + a "synced 4 minutes ago" indicator) for a fraction of the complexity. Full Prometheus stays a documented "if you ever need it" note, not something built now. |

FastAPI gets you two things Flask didn't have for free: **automatic
OpenAPI schema generation** and **Pydantic request/response validation**
(which — bonus — `config/settings.py` already uses via
`pydantic-settings`, so the mental model transfers directly).

The OpenAPI schema is the single most valuable "keep it simple" move in
this whole plan: point `openapi-typescript` at `apps/api`'s
`/openapi.json` in CI, and `packages/api-types` regenerates itself. The
frontend then gets typed `fetch` calls with zero hand-maintained
interface definitions that can drift from what the backend actually
returns — a common source of frontend/backend bugs in split
architectures, solved by tooling instead of discipline.

---

## 7. Frontend: pages and the fantasy-league feature

### Page mapping (Jinja templates → Next.js routes)

| Current template | New route | Change |
|---|---|---|
| `dashboard/templates/homepage.html` | `app/page.tsx` | Rebuilt as a React landing page — season overview, next race countdown, top headline prediction. |
| `dashboard/templates/dashboard.html` | `app/predictions/[raceId]/page.tsx` | Prediction cards, probability bars (recharts), the what-if slider panel. |
| `dashboard/templates/standings.html` | `app/standings/page.tsx` | Driver/constructor tables with sortable columns (a real upgrade over the current server-rendered table — client-side sort/filter, no round-trip). |
| `dashboard/templates/h2h.html` | `app/h2h/page.tsx` | Driver-vs-driver comparison, same data, nicer side-by-side layout. |
| `dashboard/templates/constructors.html` | `app/constructors/page.tsx` | Unchanged data, componentized. |
| `dashboard/templates/analytics_settings.html` | `app/settings/page.tsx` | Now **per-user** (needs auth) instead of a global server setting — a meaningfully more realistic behavior, not just a reskin. |
| *(new — reports were export-only before)* | `app/predictions/[raceId]/export` (a menu, not a page) | Calls `routers/reports.py`, triggers a download. |
| *(new)* | `app/leaderboard/page.tsx` | The fantasy league feature below. |
| *(new)* | `app/account/page.tsx` | Sign-in state, saved picks history, API key (if the public API ships one — optional stretch). |

Stack: **Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui,
TanStack Query** (for client-side data fetching/caching/polling against
the FastAPI backend), **recharts** for probability bars and the Monte
Carlo distribution histogram, **Auth.js (next-auth v5)** for
sign-in.

### The fantasy league — turning two unused tables into a real feature

`database/models.py` already defines `UserPick` and `Leaderboard`. This
is the single best "make it more advanced" opportunity in the whole
codebase, because the schema design work is already done and just
never got a frontend or an endpoint:

1. **Sign in** (Auth.js — GitHub/Google OAuth is the simplest to wire up,
   no password/email-verification flow to build).
2. Before a race weekend's qualifying session, a signed-in user submits
   a **pick**: predicted top-3 finishers, fastest lap, "driver of the
   day" — stored in `UserPick`.
3. `apps/ingest`'s post-race step (`evaluate_accuracy.py`, extending the
   existing `scripts/post_race_evaluation.py`) scores every user's pick
   against the actual result using the **same fantasy scoring rules
   already implemented in `engine/fantasy_scoring.py`** — that file
   already exists and is fully test-free real logic, just never called
   from a user-facing feature. Scores accumulate into `Leaderboard`.
4. `/api/leaderboard` + `app/leaderboard/page.tsx` show a season-long
   ranking: users vs. the model's own predictions vs. each other.

This is realistic-product territory (season-long engagement loop, not
just a one-off prediction tool) built almost entirely out of code that
already exists in the repo but was inert.

### Live-session mode (lighter-weight than full WebSockets)

During an actual race/quali session, `app/predictions/[raceId]/page.tsx`
switches TanStack Query to a short polling interval (e.g. 15–30s) against
`/api/standings/live` (backed by OpenF1's live endpoints, which the
current `data/openf1_client.py` already integrates). Outside of a live
session, it fetches once and doesn't poll. This gets "feels live" UX
without needing WebSockets, Vercel's WebSocket support (public beta, per
research above) is a fine upgrade path later but isn't needed for v1.

---

## 8. Ingestion & scheduling

`apps/ingest/sync_data.py` and `run_predictions.py` are triggered by a
GitHub Actions workflow, **not Vercel Cron** — Hobby's 2-jobs/once-daily
cap makes it unusable for anything happening during a live race weekend.
GitHub Actions has no such limit on free scheduled workflows.

```yaml
# .github/workflows/ingest-schedule.yml   (illustrative — tune cadences later)
on:
  schedule:
    - cron: "0 * * * *"        # hourly by default
    # add a second, denser schedule for race weekends manually or
    # via a workflow_dispatch trigger the ingest job itself requests
  workflow_dispatch: {}
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r apps/api/requirements.txt
      - run: python apps/ingest/sync_data.py
        env:
          DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
      - run: python apps/ingest/run_predictions.py
        env:
          DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
```

This also fixes a real limitation of the current Flask app: FastF1's
local disk cache (`cache/fastf1_cache/`, ~98MB, currently committed to
git per `AUDIT.md` M-6) assumed a persistent filesystem. A serverless
function's filesystem doesn't survive between invocations, so that
cache would silently stop working the moment this moves to Vercel. Moving
all FastF1/Jolpica/OpenF1 fetching into the GitHub Actions job (which
*does* have a normal, persistent-for-the-run filesystem, and can even
cache the FastF1 directory between runs via `actions/cache`) solves this
cleanly rather than working around serverless's statelessness inside the
request path.

---

## 9. Deployment fallback (if Vercel Python ever gets painful)

The plan above should work on Vercel as the primary target given the
2026 limits above (300s duration, 2–5GB bundle). But `apps/api` is a
plain ASGi FastAPI app with no Vercel-specific code beyond a thin
`apps/api/index.py` adapter — so if the ML dependency bundle (xgboost +
lightgbm + scikit-learn + pandas + numpy + scipy + fastf1, all together)
ever pushes past what's comfortable, or cold starts on a bundle that
size get annoying, the fallback is:

- Deploy `apps/api` as-is to **Render's free web service** (no bundle
  size limit, since it's a normal container — the tradeoff is the
  15-minute-idle/30-50s cold start instead).
- Change exactly one thing on the frontend: the `NEXT_PUBLIC_API_URL`
  environment variable, pointing it at Render's URL instead of
  `/api/*` on the same Vercel deployment.
- Everything else (Neon, Upstash, GitHub Actions, the frontend) is
  untouched.

This is why the repo structure keeps `apps/api` fully decoupled from
`apps/web` (separate deploy target, own `requirements.txt`, communicates
only over HTTP) instead of trying to cleverly colocate them — the
decoupling is what makes this fallback a one-line change instead of a
redesign.

---

## 10. What ports over almost unchanged

Worth saying explicitly, because it's most of the actual code: the
audit already made these correct and tested, and none of them need to
be rewritten for this migration —

- `engine/*` (Monte Carlo, grid model, ML models, fantasy scoring, elo,
  tire/weather/safety-car models, calibration, ensemble predictor) —
  moves into `apps/api/engine/` unchanged.
- `data/*` (Jolpica/OpenF1/FastF1 clients, the now-fixed `api_client.py`
  cache bug) — moves into `apps/api/data/` and `apps/ingest/` unchanged.
- `config/*` (settings, team/driver lineup, feature weights) — unchanged,
  just gets `DATABASE_URL` pointed at Neon instead of SQLite.
- `ai/*` (multi-provider LLM client for the "AI boost"/chat features) —
  unchanged; API keys move from `.env` to Vercel/GitHub Actions secrets.
- `tests/*` — unchanged, plus new tests for the FastAPI routers and the
  ingestion scripts (the coverage gap flagged in `AUDIT.md` T-1 is a
  natural thing to close *while* doing this migration, since every
  router is being touched anyway).

---

## 11. Suggested build order

Phased so the app is deployable and demoable after each step, not one
big-bang rewrite:

1. **Repo restructure** — move code into `apps/api`, no logic changes,
   confirm `pytest` still passes from the new location.
2. **Postgres cutover** — Alembic migration from the SQLAlchemy models,
   point `DATABASE_URL` at Neon, retire the dual-migration system.
3. **FastAPI routers** — 1:1 port of the Flask blueprints (table in §6),
   deploy to Vercel, confirm parity with the current Flask app via the
   existing `tests/test_dashboard_blueprints.py` assertions ported to
   `httpx`/`TestClient`.
4. **Ingestion split** — move data fetching out of the request path into
   `apps/ingest` + GitHub Actions; predictions become precomputed
   (§3).
5. **Next.js frontend v1** — page-for-page parity with the current
   templates (§7 table), no new features yet, hooked up to the new API
   via generated types.
6. **Auth + fantasy league** — the `UserPick`/`Leaderboard` feature
   (§7), the single biggest "more advanced" win for the effort involved.
7. **Live-session polling, status page, what-if panel** — the remaining
   polish items from §6/§7.

Steps 1–3 are strictly about *not breaking anything*; steps 4–7 are
where "more realistic, more advanced" actually shows up. If time runs
short, stopping after step 5 already ships a genuinely better-architected
app than the Flask original; steps 6–7 are where it stops looking like a
student project and starts looking like a product.

---

## 12. Open questions worth deciding before writing code

- **OAuth provider for Auth.js**: GitHub is the lowest-friction choice
  for a technical audience; Google reaches more casual users. Can support
  both — decide if that's worth the extra setup now or later.
- **What-if panel scope**: full slider set (chaos/wet/reliability/
  strategy, matching `config/feature_weights.py`) or a curated subset for
  v1? Full set is more "advanced," a subset ships faster.
- **Public API**: worth exposing `/api/predictions/*` as a documented
  public read API (rate-limited via the Upstash-backed limiter already
  half-built in `security/middleware.py`)? Low effort given FastAPI's
  auto-docs, and it's a nice "realistic product" touch (a public API is
  something a hobby demo doesn't have), but it's the first thing to cut
  if the timeline is tight.
