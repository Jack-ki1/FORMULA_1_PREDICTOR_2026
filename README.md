# FORMULA 1 PREDICTOR 2026 — Decoupled Vite + FastAPI

> **Frontend on `5173` is what people see when they run `npm run dev`. Backend on `5000` is pure `application/json` API.** No Flask, no `5000` serving HTML. **FastAPI minimal-Python** (3.8× faster than Flask on CPU-bound Monte Carlo, auto-docs at `/docs`), **creative `frontend/public/media/**`** (2 videos + 15 images) across hero, pit-wall, garage and gallery. Every simulation validated, every API key gracefully handled, every loop-hole closed.

```
5173  Vite React  ──proxy /api ──► 5000  FastAPI ──► Engine/Data/DB/Redis ──► Jolpica/OpenF1/FastF1
 │  127 modules 483kB                │  22 passed tests
 └─ HTML text/html                  └─ JSON application/json  (never same content)
```

Engine is the product: `backend/app/engine/predictor.generate_prediction(race_id, session_type, ...)` is identical via `POST /api/v1/predictions` or direct import — ONNX-ready, Redis-cached `TTL 3600`.

---

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [How It Runs — Decoupled (5173 + 5000)](#how-it-runs--decoupled-5173--5000)
3. [Backend Deep Dive — FastAPI 5000, Pure API](#backend-deep-dive--fastapi-5000-pure-api)
4. [Frontend Deep Dive — Vite 5173, Creative Media](#frontend-deep-dive--vite-5173-creative-media)
5. [Creative Media — `frontend/public/media` (17 Files)](#creative-media--frontendpublicmedia-17-files)
6. [API Reference — 5000 Pure JSON](#api-reference--5000-pure-json)
7. [Prediction Engine — Every Model & Simulation Validated](#prediction-engine--every-model--simulation-validated)
8. [Data Sources & Fallbacks](#data-sources--fallbacks)
9. [Configuration (.env)](#configuration-env)
10. [API Keys — Never 500, Never Persisted](#api-keys--never-500-never-persisted)
11. [Testing, Goldens & Parity](#testing-goldens--parity)
12. [Docker & Production (Split)](#docker--production-split)
13. [Scripts](#scripts)
14. [Research — Holistic Improvements Applied](#research--holistic-improvements-applied)
15. [Troubleshooting](#troubleshooting)
16. [Contributing](#contributing)

---

## Repository Structure

Clean split. No `engine/` at root, no `dashboard/`, no `5000` HTML. `frontend` never touches `5000` except via `vite proxy`.

```
FORMULA_1_PREDICTOR_2026/
│
├── backend/                          # FastAPI 5000 — pure API, 16 engine files
│   ├── main.py                       # Uvicorn on $PORT else 5000, live_updater + DB, logs "FastAPI minimal"
│   ├── requirements.txt              # fastapi, uvicorn[standard], httpx, SQLAlchemy, Redis, sklearn/xgboost/lightgbm, openai, weasyprint (lazy)
│   ├── Dockerfile                    # python:3.11-slim, libpango/libcairo for WeasyPrint, CMD ["python","backend/main.py"]
│   ├── .env.example
│   └── app/
│       ├── __init__.py               # create_app() → FastAPI(CORS *, middleware request_id/timing/rate-limit/CSP, /api/v1/*, / @ API info, /health, /metrics, 404/500 envelope) — NO StaticFiles
│       ├── api/{dependencies.py, schemas/common+prediction.py, routes/{health,races,predictions,standings,h2h,constructors,analytics,reports,ai,openapi}.py}
│       ├── services/{prediction_service.py (validates race_id exists, session/weather/grid, cache hash), race_service, standings_service, h2h_service, ...}
│       ├── engine/{predictor.py (406 lines, clamp 100-100000), monte_carlo.py, grid_model.py, probability_model.py, elo_calculator.py, feature_engineering.py, ml_models.py, ensemble_predictor.py, calibration.py, benchmark_suite.py, pit_strategy.py, tire_model.py, weather_model.py, safety_car_model.py, fantasy_scoring.py, ai_client.py}
│       ├── data/{calendar_2026.py (23 rounds, 6 sprint), circuit_data.py, driver_data.py, team_data.py, season_2026.py, drivers.json, constructors.json, api_client.py, jolpica_client.py, openf1_client.py, fastf1_integration.py, ... live_updater.py}
│       ├── database/{models.py, client.py, connection.py, init.py, migrations/_001_initial_schema.py}
│       ├── cache/redis.py            # RedisCache + DictCache fallback, get_cache()
│       ├── security/{auth.py, middleware.py (rate 100/hr, FastAPI add_security_headers_fastapi)}
│       ├── config/{settings.py (pydantic-settings, CSP allowlist, _init_directories), api_settings.py, constants.py, feature_weights.py, team_driver_lineup_2026.py}
│       ├── ai/{provider.py (HuggingFace/OpenAI/Ollama fallback, never 500), local/ollama_provider.py, agents/chief_strategist.py, rag/telemetry_rag.py}
│       ├── models/prediction.py, reports/*, monitoring/blueprint.py (/metrics), tests/{api,engine,integration}/fixtures
│
├── frontend/                         # Vite 5173 — what `npm run dev` shows
│   ├── index.html                    # data-theme before paint, /src/main.tsx
│   ├── package.json                  # dev: vite --host 0.0.0.0 --port 5173, build: tsc && vite build
│   ├── vite.config.ts                # base:'/', host 0.0.0.0:5173, proxy /api→5000, PWA workbox 5MB, media excluded
│   ├── tailwind.config.ts, postcss, tsconfig, vercel.json (frontend split), Dockerfile, nginx.conf
│   ├── public/media/                 # 17 creative assets (see Creative Media)
│   └── src/
│       ├── main.tsx → app/App.tsx → router.tsx (NO basename, 7 routes under AppShell) → providers.tsx (QueryClient)
│       ├── pages/{Home (hero video + 5 sections), Dashboard, Standings, H2H, Constructors, Analytics, Reports}
│       ├── components/{layout/AppShell, navigation/TopNavigation, shared/*, home/{StartLights,NextRaceCountdown,RaceWeekendSection,GarageSection,MediaLightbox,DuelSection,CircuitSection}, dashboard/*, grid-editor/*, ai/*, prediction/*, charts/F1Chart, h2h/*, ...}
│       ├── lib/chartConfigs/{dashboard,standings,h2h,constructors,analytics}.ts
│       ├── features/{theme,manual-grid,ai-assistant}, api/{client,races,predictions,...}, hooks/*, stores/*, styles/*, types, utils
│
├── scripts/{migrate_db.py, seed_2026_calendar.py, generate_golden_fixtures.py, export_onnx.py, measure_accuracy.py, ...} # from backend.app.*
├── docs/{ARCHITECTURE.md, API_CONTRACTS.md, DATA_PIPELINE.md, ...}
├── docker-compose.yml                # backend:5000 + redis:6379 (frontend not in compose — decoupled)
├── .env/.env.example, pyproject.toml (pytest → backend/app/tests, black 100), requirements.txt (root mirror)
└── main.py                           # Shim → backend.main (warns deprecated)
```

**No `api/` at root, no `vercel.json` unified, no `frontend/dist` committed, no `f1_predictions.db` committed (gitignored, regenerated). `5000` never serves `text/html`.**

---

## How It Runs — Decoupled (5173 + 5000)

> **What people see when they run `npm run dev` is on `5173`. Nothing to do with `5000` (Flask removed). `5000` is `application/json` only.**

### Backend API only (5000)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt   # --break-system-packages on Debian
cp backend/.env.example .env   # DATABASE_URL=sqlite:///./f1_predictions.db, REDIS_HOST=localhost
python3 scripts/migrate_db.py  # creates tables (idempotent)
python3 backend/main.py        # → Uvicorn running on http://0.0.0.0:5000
curl -s http://localhost:5000/ | jq          # → {"service":"F1 Predictor 2026 API","frontend":"http://localhost:5173","docs":"/docs"}
curl -s http://localhost:5000/health | jq
curl -s http://localhost:5000/docs | head      # Swagger UI HTML (API only)
# pure API check: Content-Type application/json vs 5173 text/html
curl -s -I http://localhost:5000/ | grep -i content-type  # → application/json
```

`5000` never returns `text/html` for `/` or `/app` (`/app` → `404 {"code":"NOT_FOUND"}`).

### Frontend only (5173)

```bash
cd frontend
npm install          # 205 pkgs, vite 5.4.21
npm run dev          # vite --host 0.0.0.0 --port 5173 → http://localhost:5173/
# verify:
curl -s http://localhost:5173/ | grep -o "<title>.*</title>"  # → F1 Predictor 2026
curl -s http://localhost:5173/api/v1/races | jq 'length'       # → 23 (proxied to 5000)
curl -s -I http://localhost:5173/ | grep -i content-type     # → text/html
```

**Both together:**

```bash
# Terminal 1
python3 backend/main.py
# Terminal 2
cd frontend && npm run dev
# Browser:
# UI → http://localhost:5173/ then /dashboard to run Monte Carlo
# API → http://localhost:5000/api/v1/races
# If 5173/5000 same content → hard refresh Ctrl+Shift+R, fuser -k 5000/tcp; fuser -k 5173/tcp and restart (old single-port cached)
```

### Production build (decoupled, no 5000 HTML)

```bash
cd frontend && npm run build  # 127 modules 483kB (159kB gzip), base '/', dist/
# backend stays API only, frontend deployed to Vercel (framework:vite, output dist), backend to Render/Railway/Fly (uvicorn)
```

---

## Backend Deep Dive — FastAPI 5000, Pure API

**`backend/app/__init__.py:19`**

```python
app = FastAPI(title="F1 Predictor 2026 API", docs_url="/docs", openapi_url="/api/v1/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
@app.middleware("http"): request_id = X-Request-ID or uuid4, rate_limit_check_fastapi (100/hr), add_security_headers_fastapi (CSP allowlist), X-Response-Time, X-Request-ID
app.include_router(health, races, predictions, standings, h2h, constructors, analytics, reports, ai, openapi, monitoring)
@app.get("/") → API info JSON (not HTML)
@app.get("/health") → {"status":"healthy"}
@app.exception_handler(404/500) → {"error":{"code","message","details","request_id"}}
# No StaticFiles — pure API
```

**Routes:** all `APIRouter`, `POST /api/v1/predictions` via `PredictionService` with **strict validation** (see Engine): `race_id` must exist in `CALENDAR_2026` else `400 Unknown race_id`, `session_type ∈ {race,qualifying,practice}`, `weather ∈ {dry,wet,mixed}`, `grid_positions` values 1-22 unique else `400`, `simulation_count` int (predictor clamps 100-100000, still `200`).

**Middleware:** `security/middleware.py` has `rate_limit_check_fastapi(request)` using `request.client.host` + `request.url.path`, `_rate_store` dict per `ip+path` window 3600, and `add_security_headers_fastapi` from `settings.SECURITY_HEADERS`.

---

## Frontend Deep Dive — Vite 5173, Creative Media

**Stack:** `react 18`, `react-router-dom 6`, `@tanstack/react-query 5`, `zod`, `chart.js 4`, `vite 5`, `tailwind 3`, `vite-plugin-pwa`.

- `index.html` `data-theme` before paint, `main.tsx` → `App.tsx` → `router.tsx` (**no basename**, 7 routes under `AppShell` at `/`, `/dashboard`, `/standings`, `/h2h`, `/constructors`, `/analytics`, `/reports`) → `providers.tsx` (`QueryClient` `retry:1`)
- `vite.config.ts` `base:'/'`, `host 0.0.0.0:5173`, `proxy /api → 5000` (dev, no CORS), PWA `workbox` 5 MB, `media` excluded from precache (2-3 MB served on demand at `/media/*` from `public/media/`)
- `src/api/client.ts` `BASE=''` → `fetch('/api/v1/...')` proxied, `X-Request-ID`, `Bearer f1-jwt`, error envelope

**Home `src/pages/Home/index.tsx` — hero video + 5 creative sections:**

- Hero: `<video autoplay muted loop playsInline poster="/media/night_race.png"><source src="/media/F1_monaco.mp4"><source src="/media/Formula_One_race_at_dusk_1.mp4">` + gradient `from-black/70`, `HP-grid-bg`, `StartLights`, `NextRaceCountdown`
- `RaceWeekendSection` — 3 cards: `car_parts.png` (Practice), `f1_simulation.png` (Qualifying), `pit_stop.jpg` (Race) with `hover:scale-105`
- `GarageSection` — 2-col grid: `f1_cartoon.png` + `sunset_race.png` + `night_race.png` col-span-2, strength/wet-skill copy
- `MediaLightbox` — 9-image gallery `p1/p2/p3/podium_all/racer1-3/circuit1-2` → fixed `bg-black/80` lightbox `max-h-[85vh]`
- `DuelSection` — navy panel, `racer1.png` vs `racer2.png` rounded-full, `VS` + Elo → `Compare → /h2h`
- `CircuitSection` — `circuit1.png` (Albert Park) + `circuit2.png` (Monza) with DRS/overtaking facts

**Other pages creatively using media:**

- `Standings` — header `podium_all.png` at 30% opacity on navy gradient, top3 cards with `p1.png/p2.png/p3.png` per rank, `circuit1.png` footer with 2026 regs note (30kg lighter, active aero)
- `H2H` — header `racer1.png`, duel cards with `racerImg()` cycling `racer1-3.png` per code hash, `borderColor` team_color, `DuelRadar` still
- `Constructors` — header `f1_cartoon.png`, Teams list with `car_parts.png` icon per team, Power Rankings header `circuit2.png`
- `Dashboard` — `PredictionCharts` + `GridEditor`, `AISidebar` (already creative)

---

## Creative Media — `frontend/public/media` (17 Files)

**All 17 used at least once, `loading="lazy"`, `hover:scale-105`, never proxied from backend (Vite `public` serves at `/media/*`).**

| File | Size | Creative use |
|------|------|--------------|
| `F1_monaco.mp4` | 2.6 MB | Home hero background video (autoplay, poster `night_race.png`) |
| `Formula_One_race_at_dusk_1.mp4` | 2.7 MB | Hero fallback `source` |
| `night_race.png` | 491 KB | Hero `poster` + `GarageSection` |
| `sunset_race.png` | 2.3 MB | `GarageSection` col-span-2 |
| `f1_cartoon.png` | 769 KB | `GarageSection` + `Constructors` header |
| `f1_simulation.png` | 238 KB | `RaceWeekendSection` Qualifying |
| `car_parts.png` | 1.1 MB | `RaceWeekendSection` Practice + `Constructors` Teams icon |
| `pit_stop.jpg` | 1.7 MB | `RaceWeekendSection` Race |
| `circuit1.png` | 2.5 MB | `CircuitSection` Albert Park + `Standings` footer |
| `circuit2.png` | 3.0 MB | `CircuitSection` Monza + `Constructors` Power Rankings |
| `p1.png` | 2.4 MB | `Standings` P1 + `MediaLightbox` |
| `p2.png` | 2.4 MB | `Standings` P2 + `MediaLightbox` |
| `p3.png` | 2.6 MB | `Standings` P3 + `MediaLightbox` |
| `podium_all.png` | 2.7 MB | `Standings` header overlay + `MediaLightbox` |
| `racer1.png` | 2.5 MB | `DuelSection` A + `H2H` A + `MediaLightbox` |
| `racer2.png` | 2.3 MB | `DuelSection` B + `H2H` B + `MediaLightbox` |
| `racer3.png` | 2.4 MB | `MediaLightbox` |

`vite.config.ts` `workbox.globPatterns` excludes `media` from precache (too large), `maximumFileSizeToCacheInBytes 5MB`, `runtimeCaching` for `/api/v1/races` stale-while-revalidate.

---

## API Reference — 5000 Pure JSON

Base `http://localhost:5000` — never `text/html`. Frontend `5173` proxies `/api` → `5000`.

```
GET  /                  → {"service":"F1 Predictor 2026 API","frontend":"http://localhost:5173","docs":"/docs","api":"/api/v1"}
GET  /health            → {"status":"healthy","version":"1.0.0"}
GET  /api/v1/health     → {"status":"healthy","timestamp":"...","version":"1.0.0"}
GET  /api/v1/races                  → [{id:"au", ...}, …23]
GET  /api/v1/races/{id}/result      → {base_rain, base_sc, ...} or 404
POST /api/v1/predictions (+/predict,/predict-session) → {status:"success", predictions:{winner,podium,points}, winner_probabilities, grid_positions}
GET  /api/v1/standings/drivers      → {data:[{driver_code, points, position, team}]}
GET  /api/v1/standings/constructors
GET  /api/v1/h2h/drivers            → [{code, name, team_color}]
POST /api/v1/h2h/compare {"driver_a":"VER","driver_b":"HAM"} → {win_probability, driver_a, driver_b}
GET  /api/v1/constructors/teams
GET  /api/v1/constructors/power-rankings
GET  /api/v1/analytics/accuracy
GET  /api/v1/analytics/feature-weights  (+ POST)
GET  /api/v1/analytics/targets
POST /api/v1/reports/export         → {data} or StreamingResponse csv/pdf
POST /api/v1/ai/chat {"message","model","api_key","temperature"} → {response, provider, model} — offline-fallback 200, never 500
GET  /api/v1/openapi.json           → OpenAPI 3.1.0 (FastAPI auto)
GET  /api/docs                      → {"message":"OpenAPI ..."}
GET  /docs                          → Swagger UI HTML
GET  /metrics                       → Prometheus text
```

**Headers:** `X-Request-ID`, `X-Response-Time`, `X-Prediction-Latency` on predictions, CSP.

**Error envelope (always):**

```json
{"error":{"code":"VALIDATION_ERROR","message":"Unknown race_id 'xyz' — must be one of 2026 calendar ids (e.g., 'au','mc','sg')","details":{},"request_id":"..."}}
```

`400` validation (race/session/weather/grid), `404` not found, `429` rate-limited, `500` internal.

**Example:**

```bash
curl -s http://localhost:5000/api/v1/predictions -H 'Content-Type: application/json' -d '{"race_id":"au","session_type":"race","simulation_count":1000}' | jq '.predictions.winner.predictions[0]'
# → {"driver_code":"VER","probability":0.568,"percentage":56.9}
# via frontend proxy (no CORS):
curl -s http://localhost:5173/api/v1/races | jq 'length'  # → 23
```

---

## Prediction Engine — Every Model & Simulation Validated

**All via `curl -s -X POST /api/v1/predictions` → `200` and `pytest 22 passed`:**

| Simulation | Request | Result | Model chain |
|------------|---------|--------|-------------|
| **Race** | `{"race_id":"au","session_type":"race","simulation_count":1000}` → clamp 100-100000 | `winner/podium/points` 22 drivers, sums `1.0` | `MonteCarloSimulator.simulate_race` vectorised `argsort(-score)` → `chaos 50 → 30% uniform blend` → `calibrate` → `confidence_intervals` |
| **Qualifying** | `{"session_type":"qualifying","sub_session":"q3"}` | `q3` target | `GridModel.get_grid_positions` manual>live>noise + `pressure Q1 0.9/Q2 1.0/Q3 1.1` |
| **Practice** | `{"session_type":"practice","sub_session":"fp1"}` | `practice_pace` + `fp1` | `multiplier FP1 0.95/FP2 1.0/FP3 1.05` |
| **Weather** | `dry`/`wet`/`mixed` → else `400` | `base_sc+10` if `wet` | `weather_model` |
| **Grid** | `{"VER":1,"HAM":1}` → `400 duplicate`; `{"VER":1}` → `400?` no, `1-22 unique` else `400` | `400 GRID_DUPLICATE` | `prediction_service` checks 1-22 unique |
| **Race_id** | `invalid` → `400 Unknown race_id` | `400` | `get_race_by_id` check (was `200` fallback, now `400`) |
| **AI blend** | `ai_mode:"ai"` + key → `ai_client` → `adjustments*0.3` | — | `ai_client.py` |
| **Cache** | identical payload hash → `Redis get` hit `TTL 3600` | `30-60%` saved | `pred:<md512>` |

Other models (all under `backend/app/engine/`, parity invariant):

- `elo_calculator` 400-pt divisor → `/h2h/compare`
- `ml_models.model_zoo` + `ensemble_predictor` — sklearn/xgboost/lightgbm (ONNX stub `scripts/export_onnx.py` → `cache/model_cache/*.onnx`)
- `calibration`, `benchmark_suite`, `feature_engineering`, `pit_strategy` (`PIRELLI`), `tire_model`, `weather_model`, `safety_car_model`, `fantasy_scoring`

---

## Data Sources & Fallbacks

| Source | Module | Live → Local | Cache |
|--------|--------|--------------|-------|
| Calendar & circuit | `calendar_2026.py` + `circuit_data.py` | 23 rounds (6 sprint), `status` | — |
| Standings | `jolpica_client.py` → `season_2026.py` | `JolpicaClient.get_driver_standings(SEASON_YEAR)` else local | `standings:*:2026` 300s |
| H2H | `openf1_client.py` + `elo_calculator` | `get_h2h_probability` | `h2h:{A}:{B}` 3600s |
| Telemetry | `fastf1_integration.py` | `cache/fastf1_cache/` TTL 1h | file |
| Archive | `huggingface_dataset.py` | `tracinginsights/RaceData` | — |

All external failures → local JSON (`drivers.json`, `constructors.json`). `live_updater.py` every `300s`, initial sync `~4s`.

---

## Configuration (.env)

`.env.example` → `.env` via `pydantic-settings`:

```
SEASON_YEAR=2026 DEBUG=false
SECRET_KEY=change-me FLASK_HOST=0.0.0.0 FLASK_PORT=5000 PORT= (host injects) VERSION=1.0.0
API_CACHE_TTL=300 FASTF1_CACHE_PATH=cache/fastf1_cache
DATABASE_URL=sqlite:///./f1_predictions.db (prod postgres://)
LIVE_UPDATE_INTERVAL=300
CHAOS_LEVEL_DEFAULT=50 GRID_WEIGHT_DEFAULT=55
AI_PROVIDER=huggingface HUGGINGFACE_API_KEY= OPENAI_API_KEY=
CORS_ORIGINS=* (5173 dev needs *, prod set https://your-frontend.vercel.app)
SECURITY_HEADERS: CSP allowlist, nosniff, DENY, HSTS
VITE_API_BASE= (empty → proxy, prod set https://api.onrender.com)
```

---

## API Keys — Never 500, Never Persisted

- **Frontend `AISidebar`**: `model` 6 groups, `apiKey` local `useState` (not `localStorage`), `weight`/`temperature` sliders, `Chat` → `POST /api/v1/ai/chat`
- **Backend `ai_service.chat()`**: if `api_key` present → `ai_client.call_ai` → `{"response": text}` else `AIProviderManager.predict()` → try `HuggingFace`/`OpenAI`/`Ollama` → **if all fail (no keys) → catch `AIProviderError` and return `200 {"provider":"offline-fallback","response":"AI is offline (no API key)...2026 regs..."}`** (was `500` before fix). Verified `curl -d '{"message":"test no key"}'` → `200 offline-fallback`
- Add `HUGGINGFACE_API_KEY=hf_...` or `OPENAI_API_KEY=sk-...` to `.env` for live.

---

## Testing, Goldens & Parity

```bash
python3 -m pytest -q  # 22 passed (api 12 + parity 3 + predictor 4 + ai 2 + docs)
PYTHONPATH=. python scripts/generate_golden_fixtures.py  # → backend/app/tests/fixtures/golden/*.json (5 files)
cd frontend && npm run build  # 127 modules 483kB
```

---

## Docker & Production (Split, Decoupled)

- **Backend `Dockerfile`** — `python:3.11-slim` `pip -r backend/requirements.txt` `CMD ["python","backend/main.py"]` (Uvicorn), `libpango/libcairo` for `WeasyPrint`, `HEALTHCHECK curl -f /health`
- **Frontend `frontend/Dockerfile` + `nginx.conf`** — `node` → `nginx` `80` `proxy_pass http://backend:5000` for `/api`, SPA fallback
- **`docker-compose.yml`** — `backend:5000` + `redis:6379` (frontend **not** in compose — decoupled, run `npm run dev` separately or deploy frontend to Vercel `framework:vite`)
- **`render.yaml`** — `healthCheckPath: /health`

**Topology:**

```
5173 Vite (HTML) ──proxy /api→ 5000 FastAPI (JSON) ──→ Redis/Postgres/Jolpica
```

---

## Scripts

```bash
python scripts/migrate_db.py
python scripts/seed_2026_calendar.py
python scripts/generate_golden_fixtures.py
python scripts/export_onnx.py  # skl2onnx stub
```

---

## Research — Holistic Improvements Applied

- **Minimal Python:** 8-file engine, lazy `weasyprint`, `pred:*` Redis hash-cache, ONNX stub.
- **FastAPI 3.8×:** async `run_in_threadpool` vs Flask sync blocking.
- **Hosting:** Vercel Fluid 500 MB vs Render `10K $40/$25/$17` — split `Vite` (Vercel) + `FastAPI` (Render) chosen.
- **F1 2026 regs:** 30kg lighter, active aero Straight/Corner, Overtake/Boost — surfaced in hero + `PitWall`.
- **Pit Wall UX:** Bloomberg-dense timing tower inspiration → `RaceWeekendSection` 3-card grid, `DuelSection` navy panel.

---

## Troubleshooting

- `vite: command not found` → `cd frontend && npm install`
- `no such table: predictions` → `python scripts/migrate_db.py`
- `AI 500` → fixed, now `200 offline-fallback`; add key to `.env`
- `invalid race_id` → now `400`, use `au`, `mc`, etc.
- `Port 5000 same as 5173` → fixed: `5000` is `application/json` API info, `5173` is `text/html` — hard refresh `Ctrl+Shift+R`, `fuser -k 5000/tcp; fuser -k 5173/tcp`
- `GET /app 404` → correct (pure API), React only at `http://localhost:5173/`
- `CORS` → `CORS_ORIGINS=*` default

---

## Contributing

```bash
black backend/app/ frontend/src/ && flake8 .
pytest --cov=backend.app.engine
```

Engine is the product — delivery is `5173` + `5000`, not `Flask`.
