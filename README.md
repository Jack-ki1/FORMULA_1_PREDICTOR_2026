# FORMULA 1 PREDICTOR 2026 — Decoupled Full-Stack

> **React + TypeScript + Vite + Tailwind frontend · Flask REST API backend · Preserved Python prediction engine · SQLAlchemy + Redis**
>
> Same inputs → same `engine.predictor.generate_prediction()` → same outputs → same UX, now with a typed API boundary and an independently-deployable SPA. Built as a controlled **Strangler Fig migration** (Jinja → React) over the existing Flask domain — not a rewrite.

Live local stack: Flask `http://localhost:5000` **single port** serves everything — legacy Jinja UI at `/`, `/dashboard/`, `/standings/`… (the “right” UI), built React SPA at `/app` (`/app/dashboard`, `/app/standings`…), API at `/api/v1/*`, plus Redis `6379`. No separate Vite dev server on `5173`. `frontend/` remains a standalone `npm` + `TSX` + `Vite` project whose `npm run build` (→ `frontend/dist`, `base: '/app/'`) is served by Flask on the same `5000`.

> **2026-09-13 Transformation + 2026-09-13 Single-Port Consolidation:** CSP raw-HTML bug fixed (`config/settings.py` allowlists Tailwind/Chart.js/Fonts), `main.py` honors `$PORT`, `Dockerfile` multi-stage builds `frontend/dist` + adds WeasyPrint libs, `CORS_ORIGINS` configurable, React Home/Reports + start-lights/countdown/ticker (`frontend/src/pages/Home`). **Sep 13 single-port:** removed `5173` — Vite dev server no longer exposed; Flask now serves `frontend/dist` at `/app` on `5000` (legacy `5000` remains primary). `docker-compose.yml` is now `backend:5000` + `redis:6379` only. Verified `python3 -m pytest 27 passed` + `npm run build 123 modules 448kB` + `curl http://localhost:5000/` (legacy 2090 lines) + `curl http://localhost:5000/app` (React).

---

## Table of Contents

1. [What This Is](#what-this-is)
2. [Architecture at a Glance](#architecture-at-a-glance)
3. [Repository Map](#repository-map)
4. [Prerequisites](#prerequisites)
5. [Run — Single Port (5000)](#run--single-port-5000)
   - [A. Docker Compose (one command, single port)](#a-docker-compose-one-command-single-port)
   - [B. Manual: Build Frontend + Run Backend (single port)](#b-manual-build-frontend--run-backend-single-port)
6. [Backend Deep Dive](#backend-deep-dive)
7. [Frontend Deep Dive](#frontend-deep-dive)
8. [API Reference](#api-reference)
9. [Prediction Engine](#prediction-engine)
10. [Data Sources & Fallbacks](#data-sources--fallbacks)
11. [Configuration](#configuration)
12. [Testing, Golden Fixtures & Parity](#testing-golden-fixtures--parity)
13. [Docker & Production](#docker--production)
14. [Visual & Prediction Parity](#visual--prediction-parity)
15. [Troubleshooting](#troubleshooting)
16. [Contributing & Scripts](#contributing--scripts)

---

## What This Is

2026 FIA World Championship predictor. 23-round calendar (`data/calendar_2026.py`), 11 teams / 22 drivers (`config/team_driver_lineup_2026.py`). Covers:

- **Race** (Monte Carlo `engine/monte_carlo.py` → win/podium/points), **Qualifying** (`engine/grid_model.py` + Q1/Q2/Q3 pressure 0.9/1.0/1.1), **Practice** (FP1 0.95 / FP2 1.00 / FP3 1.05) via `engine/predictor.py:97` `generate_prediction()`.
- **Grid**: manual P1–22 takes precedence → `GridModel.get_grid_positions()` → `_strength_based_grid()` (strength + `np.random` noise).
- **Shaping**: `probability_model.enforce_probability_sum` (winner sums to 1.0), chaos smoothing linear blend to uniform (never power-law), `calibrate_probabilities`, `calculate_confidence_intervals`, `detect_model_drift`.
- **Live sources** `data/jolpica_client.py` (championship standings), `openf1_client.py`, `fastf1_integration.py` with local fallback (`data/season_2026.py`).
- **AI**: `ai/provider.py` + `engine/ai_client.py` blending (`ai_weight` 0–1) only when `ai_mode == "ai"` and a real key is supplied; key is never persisted to `localStorage`.
- **Exports**: `reports/csv_excel_report.py`, `pdf_generator.py`, `share_card_generator.py` (CSV/JSON/PDF/share-card).

The product invariant is **prediction parity** — the migration changes delivery (Jinja → React, route → service) but never the algorithm (`docs/PREDICTION_PARITY.md`).

---

## Architecture at a Glance

```
                          Browser
                            │
               React + TypeScript + Vite + Tailwind
               React Router + TanStack Query + Zod + Chart.js
                            │  HTTPS / JSON  X-Request-ID  (JWT when present)
                            ▼
                  Flask REST API  `dashboard/app.py:1`  (factory)
               ┌─────────────────────────────────────────┐
               │  Legacy Jinja blueprints  (dual-run)    │  /dashboard/api/*  /standings/*  etc.
               │  + versioned /api/v1 blueprints          │  /api/v1/*  +  /api/v1/openapi.json
               │  Middleware: request-id, timing,        │
               │  security headers, rate-limit stub, CORS │
               └──────────────┬──────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
     Prediction Services              Data Services
   backend/app/services/*            data/* clients
              │                               │
              ▼                               ▼
     Existing Engine  engine/*  (monte_carlo, grid_model, probability_model, calibration, elo, ml_models)
              │                               │
       ┌──────┴──────┐                        │
       ▼             ▼                        ▼
     Redis      SQLAlchemy  ←─────────  Jolpica / OpenF1 / FastF1
  cache/redis   → SQLite (dev) / PostgreSQL (prod)
```

Single-port (5000) note: `frontend/dist` (Vite `base: '/app/'`) is built via `npm run build` and served by Flask at `/app` (`/app/assets/*` + SPA fallback) on the **same** `5000` — no separate `5173`. Legacy Jinja (`/`, `/dashboard/`…) keeps precedence at the root; React (`/app`, `/app/dashboard`…) and API (`/api/v1/*`) share the same origin. `frontend/` remains a standalone `npm`/`TSX` codebase; `Dockerfile` multi-stage builds it into the Flask image.

**State split (modern analytics pattern — `docs/ARCHITECTURE.md`):**

- *Server state* (TanStack Query): `["races"]`, `["drivers"]`, `["standings","drivers",2026]`, `["prediction", raceId, session, …]`, `["h2h", A, B]`.
- *Client state* (tiny store `frontend/src/stores/dashboardStore.ts:1` + `localStorage`): draft race/weather/simCount, session/subSession/target, manualGrid, AI mode/model/weight/temperature (API key excluded).

---

## Repository Map

```
FORMULA_1_PREDICTOR_2026/
├── main.py                        # boots Flask + live_updater + DB init
├── dashboard/app.py               # application factory — legacy + /api/v1 + middleware
├── dashboard/
│   ├── blueprints/
│   │   ├── landing.py             # GET /  → homepage.html
│   │   ├── predictions.py         # /dashboard/ + /dashboard/api/* (legacy, dual-run)
│   │   ├── standings.py           # /standings/*  live+fallback
│   │   ├── h2h.py                 # /h2h/*  elo_calculator
│   │   ├── constructors.py        # /constructors/*  get_all_enhanced_teams
│   │   ├── analytics_settings.py  # /analytics/*  accuracy/weights/targets
│   │   └── reports.py             # /reports/api/export  csv/json/pdf/share
│   ├── templates/                 # base.html (Tailwind CDN + styles.css), dashboard.html …
│   └── static/
│       ├── css/styles.css         # 1:1 preserved as frontend/src/styles/legacy.css
│       ├── js/  dashboard.js (state ≈ 20 keys), charts.js, grid_editor.js …
│       ├── img/  car_parts, podium, racer* …
│       └── videos/  F1_monaco.mp4 …
├── backend/                       # new service/API layer (Strangler Fig)
│   ├── app/
│   │   ├── services/
│   │   │   ├── prediction_service.py  # wraps generate_prediction, logs, gridHash
│   │   │   ├── race_service.py        # races:2026 cache key
│   │   │   ├── standings_service.py   # standings:*:2026 live→local fallback
│   │   │   ├── h2h_service.py         # h2h:{A}:{B}
│   │   │   ├── constructor_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── ai_service.py
│   │   │   └── report_service.py
│   │   ├── api/
│   │   │   ├── schemas/prediction.py / common.py  # Pydantic contracts
│   │   │   ├── dependencies.py                    # request-id, gridHash
│   │   │   └── routes/
│   │   │       ├── health.py       # /api/v1/health
│   │   │       ├── races.py        # /api/v1/races
│   │   │       ├── predictions.py  # /api/v1/predictions (+/predict +/predict-session)
│   │   │       ├── standings.py    # /api/v1/standings/{drivers,constructors}
│   │   │       ├── h2h.py          # /api/v1/h2h/{drivers,compare}
│   │   │       ├── constructors.py # /api/v1/constructors/{teams,power-rankings}
│   │   │       ├── analytics.py    # /api/v1/analytics/{accuracy,feature-weights,targets}
│   │   │       ├── reports.py      # /api/v1/reports/export
│   │   │       ├── ai.py           # /api/v1/ai/chat
│   │   │       └── openapi.py      # /api/v1/openapi.json
│   │   ├── security/middleware.py  # request-id, rate-limit stub, security headers
│   │   ├── domain/README.md        # reserved
│   │   ├── data/README.md          # maps to data/
│   │   └── engine/README.md        # maps to engine/ (preserved)
│   └── requirements.txt            # -r ../requirements.txt
├── frontend/                      # React SPA  (docs/MIGRATION.md 07–19)
│   ├── package.json               # react, react-router-dom, @tanstack/react-query, zod, chart.js
│   ├── vite.config.ts             # dev proxy /api,/dashboard,/standings,/h2h… → :5000
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html                 # theme script before paint (f1-theme localStorage)
│   ├── nginx.conf                 # prod: /api → backend:5000, SPA fallback
│   ├── Dockerfile                 # node:20 build → nginx
│   ├── src/
│   │   ├── main.tsx               # ReactDOM + App + globals.css
│   │   ├── styles/
│   │   │   ├── variables.css      # tokens — light + [data-theme="dark"]
│   │   │   ├── legacy.css         # verbatim copy of dashboard/static/css/styles.css
│   │   │   └── globals.css        # @import variables,legacy + @tailwind
│   │   ├── types/index.ts         # Race, Driver, PredictionResult …
│   │   ├── api/
│   │   │   ├── client.ts          # fetch wrapper: X-Request-ID, JWT, error contract
│   │   │   ├── races.ts, predictions.ts, standings.ts, h2h.ts, constructors.ts, analytics.ts, reports.ts
│   │   ├── hooks/  useRaces.ts, usePrediction.ts, useH2H.ts, useStandings.ts
│   │   ├── stores/ dashboardStore.ts (create.ts — tiny external-store, no Redux)
│   │   ├── utils/format.ts
│   │   ├── app/  App.tsx, router.tsx (createBrowserRouter), providers.tsx (QueryClient)
│   │   ├── components/
│   │   │   ├── layout/AppShell.tsx
│   │   │   ├── navigation/TopNavigation.tsx  (NavLink isActive ↔ request.blueprint)
│   │   │   ├── dashboard/ RaceSelector, SessionSelector, WeatherSelector, PredictionControls
│   │   │   ├── prediction/PredictionResults.tsx
│   │   │   ├── charts/PredictionCharts.tsx   # Bar + Doughnut (react-chartjs-2)
│   │   │   └── shared/ …
│   │   ├── features/
│   │   │   ├── manual-grid/GridEditor.tsx   # P1–22 selects
│   │   │   ├── ai-assistant/AISidebar.tsx   # Settings/Chat tabs, no key persistence
│   │   │   ├── theme/ ThemeProvider, ThemeToggle
│   │   │   └── exports/  (re-export via api/reports.ts)
│   │   └── pages/
│   │       ├── Home/         # navy hero + 3 CTA cards
│   │       ├── Dashboard/    # composes all dashboard features
│   │       ├── Standings/    # driver + constructor tables
│   │       ├── H2H/          # compare → Elo win%
│   │       ├── Constructors/ # teams + power rankings
│   │       ├── Analytics/    # accuracy, weight sliders, targets
│   │       └── Reports/      # note: export lives on Dashboard
│   └── src/assets/  (static)
├── engine/
│   ├── predictor.py           # generate_prediction() — orchestrator, 406 lines
│   ├── monte_carlo.py         # MonteCarloSimulator (vectorised, rank-safe)
│   ├── grid_model.py          # GridModel.get_grid_positions
│   ├── probability_model.py   # enforce sum, calibrate, confidence, drift
│   ├── elo_calculator.py      # elo_calculator.get_h2h_probability
│   ├── calibration.py, benchmark_suite.py, ml_models.py, ensemble_predictor.py …
│   ├── pit_strategy.py, tire_model.py, weather_model.py, safety_car_model.py
│   └── fantasy_scoring.py
├── data/
│   ├── calendar_2026.py       # 23 rounds, sprint flags, base_sc/rain/temp
│   ├── team_data.py, driver_data.py, circuit_data.py, season_2026.py
│   ├── jolpica_client.py, openf1_client.py, fastf1_integration.py
│   ├── live_updater.py        # background scheduler (interval = settings.LIVE_UPDATE_INTERVAL)
│   └── pipeline*.py, validation.py …
├── config/
│   ├── settings.py            # pydantic-settings, DATABASE_URL, REDIS_*, JWT_*, cache TTLs
│   ├── feature_weights.py     # chaos_level etc. (default/min/max/validate)
│   ├── constants.py           # TARGETS, team colors, points
│   └── team_driver_lineup_2026.py # get_all_drivers(), get_driver_by_code()
├── database/
│   ├── models.py              # Team, Driver, Circuit, Race, QualifyingResult, RaceResult, standings …
│   ├── client.py / connection.py / init.py
│   └── migrations/_001_initial_schema.py
├── models/prediction.py       # Prediction, SessionData, PredictionMetadata (shares Base from database.models)
├── cache/redis.py             # RedisCache + DictCache fallback, get_cache() singleton
├── security/auth.py           # generate/decode JWT, require_auth, require_role
├── reports/                   # CSVExcelReportGenerator, PDFGenerator, ShareCardGenerator
├── monitoring/                # prometheus_client, blueprint /metrics
├── scripts/
│   ├── generate_golden_fixtures.py  # → tests/fixtures/golden/*.json (parity harness)
│   ├── migrate_db.py, seed_2026_calendar.py, measure_accuracy.py …
├── tests/
│   ├── fixtures/golden/       # 5 deterministic fixtures (au/mc/it × race/qualifying/practice)
│   ├── test_predictor.py      # race/qualifying/practice + manual grid
│   ├── test_dashboard_blueprints.py # legacy /dashboard/api/* routes
│   ├── test_api_v1.py         # v1 + legacy dual-run, error contract, openapi, health
│   └── test_prediction_parity.py # engine vs /api/v1/predictions (±1e-6 seeded, sums ≈1.0)
├── docs/
│   ├── ARCHITECTURE.md        # layered diagram, state split, invariants
│   ├── API_CONTRACTS.md       # legacy + v1 table, error contract, cache keys, auth
│   ├── MIGRATION.md           # 25-step Strangler Fig order, cutover checklist
│   ├── UX_PARITY.md           # legacy.css preservation, screenshot checklist
│   ├── PREDICTION_PARITY.md   # engine pipeline, golden fixtures, seeded tolerance
│   ├── DATA_SOURCES.md        # Jolpica/OpenF1/FastF1 roles + fallbacks
│   └── DATA_PIPELINE.md       # pipeline normalization
├── docker-compose.yml         # backend:5000 + frontend:80 (nginx) + redis:6379
├── Dockerfile                 # python:3.11-slim, pip -r requirements.txt, python main.py
├── requirements.txt           # Flask 3+, SQLAlchemy 2+, Redis, scikit-learn, xgboost, lightgbm, openai, weasyprint …
├── pyproject.toml             # black, pytest testpaths
├── .env.example               # DATABASE_URL, REDIS_*, SECRET_KEY, AI keys, etc.
└── .gitignore                 # *.db, .venv, frontend/dist, frontend/node_modules, cache/*
```

---

## Prerequisites

- **Python** 3.9+ (3.11 in `Dockerfile:1`, 3.14 tested locally)
- **Node** 20+ / **npm** 10+ (frontend `package.json:1` → `v24.21.0` tested)
- **Redis** (optional — app falls back to in-memory `DictCache` `cache/redis.py:1`; `docker-compose.yml` runs `redis:7-alpine`)
- `pip >= 25` or `pip --break-system-packages` on Debian, `fastf1` needs `requests-cache`

---

## Run — Single Port (5000) — verified 2026-09-13

> **Single-port model:** Flask on `5000` is the *only* browsable port. It serves legacy Jinja UI (`/`, `/dashboard/`, `/standings/`, `/h2h/`, `/constructors/`, `/analytics/` — the “right” UI you see on `5000`) **and** the built React SPA at `/app` (`/app`, `/app/dashboard`, `/app/standings`…) **and** the API at `/api/v1/*`. `frontend/` remains a separate `npm` + `TSX` + `Vite` project (`base: '/app/'`, `router basename: '/app'`) whose `npm run build` → `frontend/dist` is served by Flask (see `dashboard/app.py`). No Vite dev server on `5173` is exposed — `5173` was the previous dev proxy and is now removed.

> **If `docker compose up` or `python main.py` appeared to hang/fail before, the fixes below address it:**
> - `data/live_updater.py:138` now starts Flask in `4s` (health `200` immediately); previously it blocked `20s` on `FastF1` fetch before `app.run`.
> - `Dockerfile:1` is now multi-stage: `node:20-alpine` builds `frontend/dist` (123 modules, 448kB) then `python:3.11-slim` copies it to `./frontend/dist` and serves it at `/app` on the same `5000` (plus `curl` + WeasyPrint `libpango/libcairo/fonts-liberation` for PDF).
> - `main.py:54` honors `$PORT` (Render/Railway/Fly) falling back to `FLASK_PORT`.
> - `config/settings.py:89` CSP fixed from bare `default-src 'self'` to `cdn.tailwindcss.com/cdn.jsdelivr.net/cdnjs/fonts.googleapis.com` — previously blocked Tailwind/Chart.js/Fonts and made every page look like raw HTML. Verify: `curl -I http://localhost:5000/ | grep -i content-security`.
> - `dashboard/app.py` now serves `frontend/dist` at `/app` with SPA fallback and `CORS_ORIGINS` handling; legacy Jinja keeps precedence at `/`.
> - `frontend/vite.config.ts` `base: '/app/'` + `frontend/src/app/router.tsx` `basename: '/app'` + `frontend/package.json` `dev` no longer starts `5173`.
> - `DATABASE_URL` unified to `sqlite:///./f1_predictions.db`.
> - `docker-compose.yml` is now `backend:5000` + `redis:6379` only — no `frontend:5173` service.

### A. Docker Compose — one command, single port (no local Python/Node needed)

Prereq: Docker Engine 20+ and Compose v2 (`docker --version`, `docker compose version`). If `docker: command not found` in WSL, enable WSL Integration in Docker Desktop Settings → Resources → WSL Integration, then `wsl --shutdown` and restart; otherwise use **B. Manual** below.

```bash
# 1) from repo root
cp .env.example .env          # edit SECRET_KEY if you want (default works for dev)
# .env DATABASE_URL is now sqlite:///./f1_predictions.db — no change needed for quick start

# 2) build & start both services (backend:5000 includes built frontend at /app, redis:6379)
#    first build takes ~160s backend (pip: xgboost/lightgbm/fastf1) + ~15s frontend (npm 205 pkgs) — now in one image
docker compose up --build -d

# 3) follow logs until you see “* Running on http://127.0.0.1:5000” (~5s)
docker compose logs -f backend   # Ctrl+C to stop tailing (containers keep running)

# 4) verify — single port hosts everything:
curl -s http://localhost:5000/health | jq        # → {"status":"healthy","version":"1.0.0"}
curl -s http://localhost:5000/api/v1/health | jq # → {"status":"healthy",…}
curl -s http://localhost:5000/api/v1/races | jq 'length'  # → 23
curl -s http://localhost:5000/ | grep -o "F1 Predict" | head -n1      # → legacy homepage 2090 lines (the “right” UI)
curl -s http://localhost:5000/app | grep -o "F1 Predictor 2026" | head -n1  # → React SPA at /app
curl -s http://localhost:5000/app/assets/index-*.css 2>&1 | head -c 50  # → @import or css
curl -s -X POST http://localhost:5000/api/v1/predictions \
  -H 'Content-Type: application/json' \
  -d '{"race_id":"au","session_type":"race","simulation_count":300}' | jq '.status'  # → success

# 5) open in browser (single port only):
# legacy (right) → http://localhost:5000/ , http://localhost:5000/dashboard/ , http://localhost:5000/standings/ , etc.
# React (frontend at same port) → http://localhost:5000/app , http://localhost:5000/app/dashboard , http://localhost:5000/app/standings , etc.
# API → http://localhost:5000/api/v1/races , http://localhost:5000/api/v1/openapi.json
# 5173 is NOT used — `curl http://localhost:5173` should refuse (expected after single-port consolidation)

# 6) stop (keeps images, removes containers + network; volumes f1_db/redis_data persist)
docker compose down
# to also wipe DB/cache: docker compose down -v && rm -f f1_predictions.db && rm -rf cache/fastf1_cache/*
```

What `docker-compose.yml:1` does: `backend` `build: Dockerfile:1` (`node:20-alpine` `npm run build` → `frontend/dist` + `python:3.11-slim` `pip -r requirements.txt` → `python main.py`) on `5000:5000`, `redis:7-alpine` on `6379:6379`, bridge `f1net`, volumes `./cache:/app/cache` + `f1_db:/app/data` + `redis_data:/data`, healthcheck `curl -f /health`. `ENV PYTHONUNBUFFERED=1`. No `frontend` service.

### B. Manual: Build Frontend + Run Backend (single port, two steps — one browsable port)

Prereq: Python 3.9+ (3.11 in `Dockerfile:1`, 3.14 tested), Node 20+ / npm 10+ (`node --version` `v20+`, `npm --version` `10+`).

**Step 1 — Build frontend** (`frontend/` is still `npm` + `TSX` + `Vite` — built artifacts are served by Flask on `5000`):

```bash
# from repo root
cd frontend
npm install                  # 205 packages, ~7s; if fails: rm -rf node_modules package-lock.json && npm install
npm run build                # tsc && vite build → 123 modules, 448kB JS (147kB gzip) → frontend/dist (base '/app/')
# optional watch during dev: npm run watch   # tsc --watch + vite build --watch → rebuilds on save, still browsed via http://localhost:5000/app after Flask reload
cd ..
# verify dist exists: ls -lh frontend/dist/  # should show index.html + assets/
```

**Step 2 — Run backend** (Flask on `5000` serves legacy + `/app` + `/api/v1`):

```bash
# from repo root

# 0) ensure 5000 free: ss -tlnp | grep 5000 (or lsof -i :5000) ; fuser -k 5000/tcp if needed
#    note: 5173 is no longer used — `ss -tlnp | grep 5173` should be empty

python3 -m venv .venv && source .venv/bin/activate
# Debian/Ubuntu PEP 668:
pip install -r requirements.txt
# if you get externally-managed-environment outside a venv:
pip install --break-system-packages -r requirements.txt
# Verify deps: python3 -c "import flask, sqlalchemy, redis, fastf1; print('deps ok')"

cp .env.example .env          # sqlite:///./f1_predictions.db — matches settings default
# optional: CORS_ORIGINS for cross-origin prod without same-origin proxy (not needed for single-port):
# echo 'CORS_ORIGINS=https://your-frontend.vercel.app' >> .env
# optional explicit DB migrate (usually auto; otherwise “no such table” warning is caught):
python3 scripts/migrate_db.py

# Run honoring $PORT if set (Render/Railway) else FLASK_PORT=5000:
python3 main.py
# or: PORT=5001 python3 main.py   # if 5000 busy
# you should see within 5s:
#   [OK] Database initialized
#   Live updater started with 300s interval (initial sync in background)
#   [OK] Flask application created
#   * Running on all addresses (0.0.0.0)
#   * Running on http://127.0.0.1:5000

# in another shell, verify immediately:
curl -s http://localhost:5000/health | jq
curl -s http://localhost:5000/api/v1/health | jq
curl -s http://localhost:5000/api/v1/races | jq 'length'   # → 23
curl -s http://localhost:5000/ | wc -l                     # → 2090 (legacy homepage — the “right” UI)
curl -s http://localhost:5000/app | grep -o "F1 Predictor 2026" | head -n1  # → React SPA
curl -s -X POST http://localhost:5000/api/v1/predictions \
  -H 'Content-Type: application/json' \
  -d '{"race_id":"au","session_type":"race","simulation_count":500}' | jq '.predictions.winner.predictions[0]'
# legacy still works (dual-run):
curl -s -X POST http://localhost:5000/dashboard/api/predict-session \
  -H 'Content-Type: application/json' -d '{"race_id":"au","session_type":"race","simulation_count":500}' | jq '.status'
# Ctrl+C to stop later: also stops live_updater thread
```

If `python3 main.py` still appears to hang: you are on the old `live_updater.py` — `git pull` and retry; `cat /tmp/backend.log` if you used `nohup`. Port `5000` busy → `ss -tlnp | grep 5000` then `fuser -k 5000/tcp` or change `FLASK_PORT=5001` in `.env`. `ModuleNotFoundError: No module named 'flask'` → you forgot `.venv` or `--break-system-packages`; run `python3 -m pip list | grep Flask` to check.

`frontend/vite.config.ts` `base: '/app/'` + `frontend/src/app/router.tsx` `basename: '/app'` ensure the built SPA's assets/hrefs are `/app/assets/...` and it can be served by Flask at `/app` with SPA fallback — no separate dev server. `VITE_API_BASE` in `frontend/.env.example:1` can override `api/client.ts:1` `BASE` for cross-origin if ever needed.

### C. Deploy (optional): still single image — Render/Railway/Fly

The same `Dockerfile` (multi-stage) now builds the frontend, so a single Render/Railway service on `5000` hosts everything. Set `DATABASE_URL` to Neon/Supabase if you want persistence (free SQLite is ephemeral), optional `REDIS_HOST/PORT/PASSWORD` (Upstash), plus `CORS_ORIGINS` if you later expose the API cross-origin. `frontend/vercel.json` + `render.yaml` remain for a split Vercel+Render topology if you prefer it, but the canonical local/docker path is now single-port via Flask.

Quick smoke after either mode:

```bash
# from repo root (either backend)
python3 -m pytest -q                               # 27 passed (API v1 + parity + legacy)
python3 -m pytest tests/test_api_v1.py tests/test_prediction_parity.py -v
# golden fixtures (deterministic, AI disabled):
PYTHONPATH=. python scripts/generate_golden_fixtures.py  # → tests/fixtures/golden/*.json (5 files)
# frontend build check:
cd frontend && npm run build && ls -lh dist/       # 123 modules, 448kB
```

---

## Backend Deep Dive

### Factory & Middleware (`dashboard/app.py:1`)

```python
create_app():
  CORS(app, supports_credentials=True)
  @app.before_request: g.request_id = X-Request-ID or uuid4; rate_limit_check() (100/hr stub backend/app/security/middleware.py:1)
  @app.after_request: add_security_headers() (from config/settings.py:SECURITY_HEADERS), X-Response-Time, echo X-Request-ID
  register legacy blueprints: landing (/), predictions (/dashboard), standings, h2h, constructors, analytics, reports
  register v1 blueprints: health, races, predictions, standings, h2h, constructors, analytics, reports, ai, openapi  (all under /api/v1)
  register monitoring blueprint (/metrics) if available
  error handlers 404/500 → {"error":{"code","message","details","request_id": rid}}
```

Dual-run: both `POST /dashboard/api/predict-session` (legacy `dashboard/blueprints/predictions.py:44`) and `POST /api/v1/predictions` (`backend/app/api/routes/predictions.py:35`) coexist and call the same engine. Cutover is `MIGRATION.md:23` step 22–23.

### Services (`backend/app/services/*`)

Thin orchestration, no algo change (`MIGRATION.md` Phase 1):

- `prediction_service.py:1` — validates `race_id`, normalizes `simulation_count`, builds `ai_config`, logs `race/session/weather/sims/gridHash`, calls `engine.predictor.generate_prediction`, returns result (adds `X-Prediction-Latency` header in route).
- `race_service.py:1` — `races:2026` cache key (3600s), lists `CALENDAR_2026`, `get_race_result` validates `completed`.
- `standings_service.py:1` — `standings:drivers:2026` / `standings:constructors:2026` (300s), tries `JolpicaClient.get_driver_standings(SEASON_YEAR)`, falls back to `data/season_2026.py`.
- `h2h_service.py:1` — `h2h:{A}:{B}` (3600s), `elo_calculator.get_h2h_probability`.
- `constructor_service.py:1`, `analytics_service.py:1`, `ai_service.py:1`, `report_service.py:1` — delegate to `data/team_data`, `engine.benchmark_suite`, `ai/provider`, `reports/*`.

### Schemas & Validation

`backend/app/api/schemas/prediction.py:1` (Pydantic `PredictionRequest`): `race_id` required, `session_type ∈ {race,qualifying,practice}`, `weather ∈ {dry,mixed,wet}`, `simulation_count 100–100000` (also clamped in `engine/predictor.py:127`). Frontend uses `zod` + `api/client.ts:1` typed `fetch` wrapper (throws `{code, request_id, details}` on non-2xx).

### Security

`security/auth.py:1` — `generate_jwt_token`, `decode_jwt_token`, `@require_auth` (reads `Authorization: Bearer`), `@require_role`. `backend/app/security/AUTH_PARITY.md:1` explains the fix: dormant `dashboard.py:1` / `health.py:1` required auth but were never registered; active `predictions.py:44` was open. v1 now **accepts anonymous but validates token if present** — reconcile without breaking the dashboard. Harden later with `require_auth` on selected v1 routes; API key for AI is never stored server-side (`frontend/src/features/ai-assistant/AISidebar.tsx:1`).

### Persistence & Cache

- `config/settings.py:1` (`pydantic-settings`) — `DATABASE_URL` default `sqlite:///./f1_predictions.db` (prod: `postgresql://…`), `REDIS_HOST/PORT/DB`, `JWT_*`, `LIVE_UPDATE_INTERVAL`, `CACHE_TTL_*`.
- `cache/redis.py:1` — `RedisCache` with TCP check + `DictCache` fallback; `get_cache()` singleton; `database/client.py:1` pools via `SQLAlchemy 2.0`.
- DB failure is non-fatal: `engine/predictor.py:356` catches `save_predictions_to_database` errors and still returns the prediction.

---

## Frontend Deep Dive

### Stack

`frontend/package.json:1` — `react 18`, `react-dom 18`, `react-router-dom 6`, `@tanstack/react-query 5`, `zod 3`, `chart.js 4` + `react-chartjs-2 5`, `vite 5`, `tailwind 3`.

### Entry & Styling

- `frontend/index.html:1` — sets `data-theme` from `localStorage f1-theme` before paint to avoid flash.
- `frontend/src/main.tsx:1` → `app/App.tsx:1` (`Providers` + `RouterProvider`) → `app/router.tsx:1` (`createBrowserRouter` → `AppShell` with 7 children) → `app/providers.tsx:1` (`QueryClient` defaults `retry:1, staleTime:30s`).
- `frontend/src/styles/variables.css:1` — CSS vars `--red`, `--bg`, `--surface` … light + `[data-theme="dark"]` overrides; `legacy.css:1` is **verbatim** `dashboard/static/css/styles.css:1` (1217 lines: nav, cards, gauge, grid editor, ai sidebar, charts) — `globals.css:1` imports both before `@tailwind` directives for pixel parity (`docs/UX_PARITY.md:1`).

### Routing

| Path | Component | Data |
|---|---|---|
| `/` | `pages/Home/index.tsx:1` | navy hero + CTA |
| `/dashboard` | `pages/Dashboard/index.tsx:1` | races + prediction + grid + charts + AI |
| `/standings` | `pages/Standings/index.tsx:1` | `useDriverStandings` + `useConstructorStandings` |
| `/h2h` | `pages/H2H/index.tsx:1` | `useDrivers` + `useH2HCompare` |
| `/constructors` | `pages/Constructors/index.tsx:1` | `fetchTeams` + `fetchPowerRankings` |
| `/analytics` | `pages/Analytics/index.tsx:1` | `fetchAccuracy`, weights GET/POST, targets |
| `/reports` | `pages/Reports/index.tsx:1` | note — export button on Dashboard |

`components/layout/AppShell.tsx:1` renders `TopNavigation.tsx:1` (`NavLink isActive` replaces Jinja `request.blueprint` check in `dashboard/templates/base.html:36`) + `<Outlet>` + footer `Season 2026 · Model v1.0`. `features/theme/ThemeProvider.tsx:1` syncs `document.documentElement[data-theme]` + `localStorage`.

### Dashboard Composition

`pages/Dashboard/index.tsx:1` composes:

- `components/dashboard/RaceSelector.tsx:1` — `useRaces()` → `GET /api/v1/races` (filtered `status != cancelled`).
- `components/dashboard/SessionSelector.tsx:1` — sessions `practice|qualifying|race` (mirrors `dashboard.js:13` `SESSIONS`), default target `podium|qualifying_q3|practice_pace`.
- `components/dashboard/WeatherSelector.tsx:1` — `dry|mixed|wet` + simCount `1k|5k|10k|50k`.
- `components/dashboard/PredictionControls.tsx:1` — builds `PredictPayload` (`race_id`, `session_type`, `sub_session`, `weather`, `grid_positions`, `feature_weights`, `simulation_count`, `ai_*`), for `race` without manual grid it first does a qualifying `q3` call to auto-fill grid (same as `dashboard.js:882` two-step), then race call; shows `Running…` + spinner; calls `onResult`.
- `features/manual-grid/GridEditor.tsx:1` — `useDrivers()` list, `P1–22` selects per code (parity with `grid_editor.js`), writes `dashboardStore.manualGrid`.
- `components/charts/PredictionCharts.tsx:1` — `Bar` + `Doughnut` of top 8 `percentage`.
- `prediction/PredictionResults.tsx:1` — tables per `target_id` (winner/podium/points…), `probability` 4 dp, `percentage` 2 dp, top 12 rows.
- `features/ai-assistant/AISidebar.tsx:1` — fixed `400px` slide-in, tabs `Settings|Chat`; `mode normal|ai`, `model gemini-2.0-flash-exp|gpt-4o|custom`, `apiKey` (type password, not stored), `weight` slider 0–100, `temperature` 0–2; chat posts to `POST /api/v1/ai/chat`.
- Export row — `api/reports.ts:1` `exportReport()` → `POST /api/v1/reports/export` (csv/json/pdf/share) → blob download.

Client store `stores/dashboardStore.ts:1` (`stores/create.ts:1` tiny external-store) holds `draft`, `session`, `subSession`, `targetId`, `manualGrid`, `gridPositions`, `gridSource`, `ai*` and syncs selected keys to `localStorage` (apiKey excluded).

### API Layer

`api/client.ts:1` — `req(path, init)` adds `X-Request-ID` (`crypto.randomUUID`), `Authorization` if `f1-jwt` present, parses JSON or returns `Response` for blobs; on non-2xx throws `Error` with `code/request_id/details` from `{"error":{…}}`. Specific modules `races.ts`, `predictions.ts` (`predictSession`, `aiChat`), `standings.ts`, `h2h.ts`, `constructors.ts`, `analytics.ts`, `reports.ts`.

Query hooks `hooks/useRaces.ts:1` etc. set `staleTime` and query keys matching cache keys (`["races"]`, `["standings","drivers",2026]`, `["h2h", A,B]`) per `docs/ARCHITECTURE.md`.

---

## API Reference

Base: `http://localhost:5000` (Flask). Legacy (Jinja-era, still served) + versioned:

**Legacy (used by old Jinja `dashboard.js:504` and kept for dual-run):**

```
GET  /dashboard/api/races
GET  /dashboard/api/race-result/<race_id>
POST /dashboard/api/predict-session
POST /dashboard/api/ai-chat
GET  /standings/api/driver-standings
GET  /standings/api/constructor-standings
GET  /h2h/api/drivers
POST /h2h/api/compare
GET  /constructors/api/teams
GET  /constructors/api/power-rankings
GET  /analytics/api/accuracy
GET  /analytics/api/feature-weights
POST /analytics/api/feature-weights
GET  /analytics/api/targets
POST /reports/api/export
GET  /health
```

**Versioned (`/api/v1`, typed, `docs/API_CONTRACTS.md:1`, OpenAPI `GET /api/v1/openapi.json`):**

```
GET  /api/v1/races
GET  /api/v1/races/<race_id>/result   (compat alias /api/v1/race-result/<id>)
POST /api/v1/predictions             (aliases /api/v1/predict, /api/v1/predict-session)
POST /api/v1/ai/chat
GET  /api/v1/standings/drivers
GET  /api/v1/standings/constructors
GET  /api/v1/h2h/drivers
POST /api/v1/h2h/compare
GET  /api/v1/constructors/teams
GET  /api/v1/constructors/power-rankings
GET  /api/v1/analytics/accuracy
GET  /api/v1/analytics/feature-weights
POST /api/v1/analytics/feature-weights
GET  /api/v1/analytics/targets
POST /api/v1/reports/export
GET  /api/v1/health
GET  /api/v1/openapi.json
GET  /api/docs                        # pointer to openapi.json
```

**Request example `predict`:**

```bash
curl -s http://localhost:5000/api/v1/predictions \
  -H 'Content-Type: application/json' -H 'X-Request-ID: demo-1' \
  -d '{
    "race_id":"au","session_type":"race","sub_session":"race",
    "weather":"dry","simulation_count":1000,
    "feature_weights":{"chaos_level":50},
    "grid_positions":{"VER":1,"NOR":2},
    "ai_mode":"normal"
  }' | jq '.predictions.winner.predictions[0]'
```

**Response shape (abridged):**

```json
{
  "race_id":"au","session_type":"race","sub_session":"race","weather":"dry",
  "grid_positions":{"VER":1,…},
  "predictions":{
    "winner":{"target_id":"winner","target_label":"Race Winner","confidence":0.82,
      "predictions":[{"driver_code":"VER","probability":0.245,"percentage":24.5},…]},
    "podium":{…},"points":{…}
  },
  "winner_probabilities":{"VER":0.245,…},
  "confidence_intervals":{"VER":{"lower":0.21,"upper":0.28},…},
  "model_drift_score":0.01,
  "timestamp":"2026-09-12T13:00:00.000000","status":"success"
}
```

**Headers:** `X-Request-ID` (echo), `X-Response-Time`, `X-Prediction-Latency`, `Cache-Control: public, max-age=300` (races) / `60` (standings), security headers `Content-Security-Policy`, `X-Frame-Options: DENY`, etc.

**Error contract (v1):** `{"error":{"code":"VALIDATION_ERROR","message":"race_id is required","details":{},"request_id":"…"}}` — `400` validation, `404` not found / not completed, `500` prediction failed. Legacy returns `{"error":"…"}` (kept for compat).

---

## Prediction Engine

`engine/predictor.py:97` `generate_prediction(race_id, session_type, sub_session, weather, grid_positions, feature_weights, simulation_count, ai_config)`:

1. Normalizes `session_type`/`weather`/`sub_session`, clamps `sim_count 100–100000` (`predictor.py:127`), builds `race_info` fallback, `base_sc +10 if wet`, collects `all_drivers = get_all_drivers()` (22).
2. **Race:** `MonteCarloSimulator(num_simulations=sim_count).simulate_race(race_id, grid, weather, safety_car_prob=sc_prob, chaos_level, num_simulations=sim_count)` (`monte_carlo.py:1` vectorised `argsort(-score)`); extracts `win/pod/points` probs; optional AI blend (`ai_client.get_prediction_insights` → `adjustments * ai_weight`); chaos smoothing `_apply_chaos_smoothing` (0 = preserve, 100 = 60% uniform blend); builds `winner|podium|points` summaries.
3. **Qualifying:** `GridModel` or fallback, pressure `Q1 0.9 / Q2 1.0 / Q3 1.1`, `strength*0.6 + d_strength*0.4 + wet/consistency + pressure` → `q3` + sub-session mirrors.
4. **Practice:** `session_multiplier FP1 0.95 / FP2 1.0 / FP3 1.05`, `strength*multiplier + wet + consistency`.
5. Post: `calibrate_probabilities`, `calculate_confidence_intervals`, `detect_model_drift`, `save_predictions_to_database` + `save_prediction_metadata` (caught on `OperationalError` → still returns; `predictor.py:356`).

Stochastic note: `_strength_based_grid` uses `np.random.default_rng()` without seed — deterministic parity needs fixed seeds/grid (`docs/PREDICTION_PARITY.md:1`).

---

## Data Sources & Fallbacks

| Source | Module | Live → Local Fallback | Cache |
|---|---|---|---|
| Calendar & circuit meta | `data/calendar_2026.py:1` `circuit_data.py` | 23 rounds (6 sprint), `status completed|upcoming` | — |
| Standings | `jolpica_client.py:1` → `season_2026.py` | `JolpicaClient.get_driver_standings(SEASON_YEAR)` live else local `get_driver_standings()` (`standings_service.py:1`) | `standings:*:2026` 300s |
| Session & h2h | `openf1_client.py`, `elo_calculator.py` | `get_h2h_probability(A,B)` | `h2h:{A}:{B}` 3600s |
| Telemetry | `fastf1_integration.py` | `cache/fastf1_cache/` TTL 1h | file |
| Historical archive | `huggingface_dataset.py` | optional | — |
| Pipeline normalization | `pipeline.py` `session_context.py` | strength/grid mapping | — |

All external failures degrade gracefully to local JSON (`data/constructors.json`, `drivers.json`, `season_2026.py`).

---

## Configuration

`.env.example` → `.env` (all via `config/settings.py:1` `pydantic-settings`):

```
SECRET_KEY=change-me
FLASK_HOST=0.0.0.0  FLASK_PORT=5000  FLASK_ENV=development  DEBUG=false
# Render/Railway/Fly inject $PORT at runtime — main.py honors it over FLASK_PORT (no code change needed)
PORT=                              # only set by host; leave blank locally
DATABASE_URL=sqlite:///./f1_predictions.db   # prod: postgresql://user:pass@host/db (Render free has no disk — SQLite resets on deploy)
REDIS_HOST=localhost  REDIS_PORT=6379  REDIS_DB=0  REDIS_PASSWORD=  # docker-compose sets REDIS_HOST=redis
CORS_ORIGINS=*                     # comma-separated allowlist for cross-origin prod: https://f1-predictor.vercel.app,https://f1-predictor-2026.vercel.app (vite proxy is same-origin, so * is fine locally)
SEASON_YEAR=2026  VERSION=1.0.0
CACHE_TTL_SECONDS=300  LIVE_UPDATE_INTERVAL=300
JWT_ALGORITHM=HS256  JWT_EXPIRATION_HOURS=24
RATE_LIMIT_ENABLED=true
HUGGINGFACE_API_KEY=  OPENAI_API_KEY=
VITE_API_BASE=                     # frontend: leave blank for vite/nginx proxy (same-origin); set to https://backend.onrender.com for cross-origin Vercel → Render without rewrites
```

Feature weights `config/feature_weights.py:1` — `chaos_level` 0–100 step 1 (default 50) etc. (`grid_weight` default 55). Constants `config/constants.py:1` — `TARGETS`, Pirelli compounds, points.

---

## Testing, Golden Fixtures & Parity

```bash
# backend
python -m pytest -q                          # 27 tests (v1+parity+legacy)
python -m pytest tests/test_api_v1.py -v
python -m pytest tests/test_prediction_parity.py -v
python -m pytest tests/test_predictor.py tests/test_dashboard_blueprints.py -v

# golden fixtures (deterministic inputs, AI disabled)
PYTHONPATH=. python scripts/generate_golden_fixtures.py   # → tests/fixtures/golden/*.json (5 files)
pytest tests/test_prediction_parity.py -v                # abs(old-new) < 1e-6 seeded or sums ≈1.0

# frontend
cd frontend && npm run build    # tsc && vite build → dist/ (438 kB JS)
```

`tests/test_api_v1.py:1` covers `/api/v1` + legacy dual-run, `X-Request-ID`, `X-Prediction-Latency`, error contract, OpenAPI, health, exports. `tests/test_prediction_parity.py:1` compares direct `generate_prediction()` vs `POST /api/v1/predictions` per golden fixture (structure, winner sums, driver ordering — top stays within 5 under Monte Carlo variance; seeded runs use `1e-6`).

---

## Docker & Production

- `Dockerfile:1` — **multi-stage** `node:20-alpine` (`npm run build` → `frontend/dist`, `base: '/app/'`) → `python:3.11-slim` (`pip -r requirements.txt` → `python main.py`) and serves `frontend/dist` at `/app` on the same `5000`. Also installs `libpango/libcairo/fonts-liberation` for WeasyPrint, honors `$PORT`, and `curl` for healthcheck. Single image, single port.
- `frontend/Dockerfile:1` + `frontend/nginx.conf:1` — legacy split-deploy path (`node` build → `nginx` on `80` proxying `/api` → `backend:5000`). Kept for reference if you prefer a separate `nginx` frontend (e.g., `docker-compose` with nginx), but the canonical `docker-compose.yml` now uses the single-image backend only.
- `docker-compose.yml:1` — `backend:5000` (multi-stage built frontend at `/app`) + `redis:6379` only — see [Run — Single Port](#a-docker-compose-one-command-single-port). No `frontend:5173`. Healthcheck `curl -f /health`. Requires Docker Desktop WSL integration if `docker: command not found` in WSL.
- `frontend/vercel.json` + `render.yaml` — optional split free-tier (Vercel `dist` rewrites `/api` → `https://YOUR-BACKEND-HOST.example.com` + Render `PORT`/`healthCheckPath`). Single-port (`Flask on 5000` serving both) works without them; use only if you want Vercel CDN for the SPA.

Production topology — single-port (canonical):

```
Browser ──→ Flask on 5000 (Jinja / + /dashboard/…  +  React /app  +  API /api/v1/*) ──→ Redis / PostgreSQL / F1 APIs
                     ^ single image (Dockerfile multi-stage) with frontend/dist at /app
                     ^ scales via $PORT / replica; Celery/RQ later for Monte Carlo
```

Legacy split (optional):

```
Browser ──→ Vercel (frontend, rewrites /api ──→) Render (Flask, $PORT) ──→ Redis/Postgres/F1 APIs
```

---

## Visual & Prediction Parity

- **Visual** `docs/UX_PARITY.md:1` — preserve `variables.css` + `legacy.css` (fonts, spacing, nav 40px, card radius `.75rem`, chart `220px`, table `13px`, dark `[data-theme]`) until screenshot regression (home, dashboard loaded/done/AI, standings, H2H, constructors, analytics, dark, mobile/tablet/desktop) passes.
- **Prediction** `docs/PREDICTION_PARITY.md:1` — engine is invariant; compare `old` vs `new` `result.json` (targets, ordering, probabilities, confidence, grid, metadata, source) with tolerance; seeded Monte Carlo equality, not naive rerun equality.

---

## Troubleshooting

- `ModuleNotFoundError: fastf1` → `pip install fastf1 requests-cache` (or `pip install --break-system-packages -r requirements.txt` on Debian PEP668). Check `python3 -m pip list | grep fastf1`.
- `externally-managed-environment` → `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` or `pip install --break-system-packages -r requirements.txt`.
- `no such table: predictions` on first run → `python3 scripts/migrate_db.py` or ignore — saves are caught, prediction still returns.
- `Redis host unreachable` → `DictCache` fallback logs `Using in-memory DictCache`; start `redis-server` or `docker compose up redis`. Manual uses `localhost:6379`, compose uses `redis:6379` (via `REDIS_HOST` env).
- `Hugging Face API key not configured` → expected without `.env` key (AI off).
- `Port 5000 looks like raw/unstyled HTML` → **fixed 2026-09-13**: `Content-Security-Policy` was `default-src 'self'` and silently blocked Tailwind/Chart.js/Fonts. Now allowlisted. If still raw, verify: `curl -I http://localhost:5000/ | grep -i content-security` should contain `cdn.tailwindcss.com`.
- `docker: command not found` in WSL → enable WSL Integration in Docker Desktop Settings → Resources → WSL Integration, then `wsl --shutdown` and restart.
- `Address already in use 5000` → `docker compose down` or `fuser -k 5000/tcp` or `PORT=5001 python3 main.py`. Note: `5173` is no longer used — `curl http://localhost:5173` should refuse; if it still listens, `pkill -f vite` / `fuser -k 5173/tcp` then `npm run build` + reload Flask.
- `http://localhost:5000/app` 404 → `frontend/dist` not built yet; run `cd frontend && npm run build` then restart Flask (`python3 main.py` picks it up).
- Frontend `404 /api/v1/races` → ensure Flask is on `5000`; `curl -s http://localhost:5000/api/v1/races | jq length` should be 23. For React at `/app`, `fetch('/api/v1/races')` is same-origin to `5000`, no CORS needed. If you set `VITE_API_BASE` cross-origin, set backend `CORS_ORIGINS`.
- `X-Request-ID` missing → `dashboard/app.py` `before_request` always sets it; for `/app` it is echoed as well.
- `npm run build` fails `tsc` → `cd frontend && npx tsc --noEmit` (should be clean) and `npm install` (205 pkgs).
- Previous `5173` references → removed; the only browsable port is `5000` (`/` legacy, `/app` React, `/api/v1/*` API).

---

## Contributing & Scripts

```bash
black . && flake8 .          # formatting (pyproject.toml: black line-length 100)
pytest --cov=engine           # coverage
python scripts/measure_accuracy.py
python scripts/calibrate_probabilities.py
python scripts/optimize_weights.py
python scripts/post_race_evaluation.py
python scripts/data_quality_report.py
```

Commit flow: update `dashboard/app.py` + `backend/app/*` (services/schemas/routes) + `frontend/src/*` in one migration step (per `docs/MIGRATION.md` Phase 0–25; now at Phase 23 cutover, Jinja kept as fallback). Final optional move: `Flask → FastAPI` sharing `engine/` unchanged.

---

*Engine is the product.* The migration changes delivery, not algorithms. See `docs/MIGRATION.md` for the full Strangler Fig order and `docs/API_CONTRACTS.md` for the frozen contract.
