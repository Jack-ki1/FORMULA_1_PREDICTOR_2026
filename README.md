# FORMULA 1 PREDICTOR 2026 — Intelligence Platform

> **F1 Intelligence Engine** — Monte Carlo + Elo + GridModel + live RSS news + Fantasy helper.  
> **Frontend** `http://localhost:5178` (Vite React, `text/html`) · **API** `http://localhost:5000` (FastAPI, `application/json`) — never same content. Decoupled.  
> **Status:** Heuristic Monte Carlo is production (2026 has no real results yet → `statistical_fallback`), ML ensemble wired but not yet validated on real history — see `docs/ML_VALIDATION.md`.

```
5178  Vite React 18 ──proxy /api ──► 5000  FastAPI ──► Orchestrator ──► Providers/DB/Redis
 │  React Router 6 routes              │  22 tests green (Monte Carlo + fallback)
 │  17 media via typed registry        │  Snapshot + provenance + calibration (when trained)
 └─ HTML (Home, Dashboard, etc)        └─ JSON (fantasy, news, settings, health)
```

Engine is `backend/app/engine/predictor.generate_prediction` — identical via `POST /api/v1/predictions` or direct import. Live data hits `fallback` constants for 2026 future races (provenance marked).

---

## 1. Quick Start (decoupled, ports distinct)

```bash
# Backend API only (5000) — pure JSON, never HTML
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt  # or -r requirements.txt
cp backend/.env.example .env  # DATABASE_URL, REDIS_HOST, SECRET_KEY
python3 scripts/migrate_db.py
python3 backend/main.py        # → http://localhost:5000/ (HTML landing for browsers, JSON for curl) and /health /docs

# Frontend only (5178) — new terminal
cd frontend
npm install
npm run dev                   # → http://localhost:5178/ (Vite, proxy /api → 5000)

# Or root orchestrator (requires concurrently)
npm install
npm run dev                   # runs both; frontend 5178, backend 5000
```

Verify distinct:

```bash
curl -s http://localhost:5000/ | jq        # → {"service":"F1 Predictor 2026 API", "mode":"pure API — frontend is decoupled on Vite dev server (5178), this is port 5000", ...} (JSON)
curl -s -H "Accept: text/html" http://localhost:5000/ | head -c 400  # → HTML landing "PORT 5000 — API ONLY"
curl -s http://localhost:5000/health | jq  # → {"status":"healthy"}
curl -s http://localhost:5000/docs | head -c 200  # → Swagger UI HTML (also /redoc, /api/v1/openapi.json)
curl -s http://localhost:5178/ | grep -o "<title>.*</title>"  # → F1 Predictor 2026 (React)
curl -s http://localhost:5178/api/v1/races | jq 'length'       # → 23 (proxied via Vite)
```

> Frontend `5178` vs API `5000` — never same content. If `5178` is busy, Vite will try next port; backend always 5000 unless `PORT` env overrides.

---

## 2. Repository Structure (current truth — Nov 2026)

```
FORMULA_1_PREDICTOR_2026/
├── backend/
│   ├── main.py (Uvicorn on $PORT else 5000)
│   ├── app/
│   │   ├── __init__.py (FastAPI factory, CORS allowlist, rate-limit Redis, /health, /metrics, content-negotiated /)
│   │   ├── api/routes/{health,races,predictions,standings,h2h,constructors,analytics,reports,ai,system,scenario,live,jobs,grid,news,settings}.py
│   │   ├── services/{prediction_service (snapshot+hash cache TTL3600), race_service, standings_service, h2h_service, ...}
│   │   ├── prediction/{orchestrator.py (ML+MC blend), snapshot.py, explainability.py}
│   │   ├── engine/{predictor, monte_carlo (vectorised argsort, seedable), grid_model (Q1→Q3 22→16→10 + official Jolpica), probability_model, elo, feature_engineering, ml_models, ensemble_predictor, calibration, ...}
│   │   ├── data/{calendar_2026 (23 rnds, 6 sprint), circuit_data, team_driver_lineup_2026 (23 drivers), providers/{base,jolpica,openf1,fastf1,fallback,registry}, season_2026 (14 completed), ...}
│   │   ├── cache/redis.py (RedisCache + DictCache fallback, REDIS_REQUIRED flag)
│   │   ├── security/middleware.py (Redis INCR per-route limits), config/settings.py, database/{models, client}
│   │   └── tests/{api,engine,integration}
│   └── requirements.txt
├── frontend/
│   ├── vite.config.ts (127.0.0.1:5178 proxy /api,/health,/metrics,/docs→5000, PWA 5MB, media excluded)
│   ├── public/media/ (17 assets: 2 mp4 +15 png/jpg — F1_monaco, Formula_One_race_at_dusk_1 etc)
│   └── src/
│       ├── app/router.tsx (routes: /, /dashboard|/predictions, /standings, /h2h, /fantasy|/teams|/constructors, /analytics|/analytics-news, /settings)
│       ├── pages/{Home (cinematic dusk + 6 new sections), Dashboard (single image, day→session, 16 modifies, 16 plots), Standings (12 plots), H2H (16 plots), Constructors→Fantasy, Analytics (model card + news), Settings}
│       ├── features/{manual-grid (GridEditor with official API), ai-assistant, theme}
│       ├── api/{client,races,predictions,grid,h2h,constructors,analytics,reports,news,settings, ...}
│       ├── lib/{media.ts (F1_MEDIA typed), chartConfigs/*}
│       └── components/{layout/AppShell, navigation/TopNavigation (Predictions, Standings, H2H, Fantasy, Analytics & News, Settings), ...}
├── training/
│   ├── datasets/{schema.py (feature-v8/dataset-v14), builder.py (temporal, no leakage — synthetic until backfill)}
│   ├── pipelines/train.py (OOF ensemble + isotonic, writes cache/model_cache)
│   └── model_registry/registry.py (champion/challenger)
├── scripts/{migrate_db, seed_2026_calendar, generate_golden_fixtures, export_onnx, ...}
├── docs/{ARCHITECTURE, ML_ARCHITECTURE, DATA_ARCHITECTURE, PREDICTION_PIPELINE, API_ARCHITECTURE, MODEL_REGISTRY, ML_VALIDATION, DEEP_AUDIT}
├── docker-compose.yml (backend:5000 + redis:6379; frontend via Vite/Vercel)
├── Dockerfile (legacy single-image, pure JSON backend)
├── pyproject.toml (pytest → backend/app/tests)
└── package.json (root concurrently dev — frontend 5178, backend 5000)
```

Removed not routed (but files remain on disk if you need): `frontend/src/pages/{LiveRace,ScenarioLab}` old standalone `Reports` page (now embedded in Dashboard). Use git history to restore.

---

## 3. Architecture (decoupled, research-backed 2026 regs)

- **Frontend** `5178`: React 18, Router 6, TanStack Query 5, Chart.js 4, Tailwind 3, PWA. `BASE=''` proxies to 5000; typed `F1_MEDIA` registry. Routes code-split; videos poster `night_race.png`, PWA precache 581 KiB. Single hero image per page, `Titillium Web` + `IBM Plex Mono` kept.
- **Backend** `5000`: FastAPI `create_app()` — CORS `FRONTEND_ORIGIN` allowlist (not `*`+credentials), `X-Request-ID/X-Response-Time`, per-route Redis rate limit (`predictions 60/h, ai 30/h, live 120/h`), security headers, `/metrics`, content-negotiated `/` (HTML for browsers, JSON for curl). Pure JSON otherwise.
- **Providers**: `F1DataProvider` → `JolpicaProvider` (official results) / `OpenF1Provider` (live telemetry, subscription-gated) / `FastF1Provider` (historical) / `FallbackProvider` (seed+cache). Federated via `Registry`; every dataset has `DataProvenance{source,provider,endpoint,retrieved_at,hash,cache_status}`.
- **Grid**: `GridModel` — real Jolpica qualifying first, else simulated Q1-Q3 (22→16→10), else manual P1-23 fallback. Exposed at `GET /api/v1/grid/{race_id}` for manual editor.
- **Cache**: Redis required in prod (`REDIS_REQUIRED=true`), in-memory `DictCache` only if `ENABLE_IN_MEMORY_FALLBACK=true` (dev). Prediction key hashes `race+session+snapshot+model+feature+weather+grid+config`.
- **DB**: SQLAlchemy → SQLite dev / Postgres prod. Tables: `predictions, session_data, prediction_metadata, races, drivers…`; seed from python constants, DB is truth for dynamic data.

**2026 regs (FIA Section C issue 18 + Formula1.com verified):** Active aero Straight (open, low drag) vs Corner (closed, high downforce) every lap, 50/50 PU (400kW ICE + 350kW MGU-K, MGU-H deleted, battery 4→8MJ+), 100% Advanced Sustainable fuel (>90% CO₂ cut), 768kg (-30kg), 3400mm (-200mm), 1900mm (-100mm), 6 PU manufacturers, cost cap $130m.

---

## 4. Prediction Intelligence

```
Race request
  → Resolve race/session/day (validated race_id must exist in CALENDAR_2026, sprint-aware: Friday FP1-3, Saturday Q1-3 (+Sprint if sprint weekend), Sunday Race)
  → Federated data + provenance (currently always fallback — 2026 has no real results yet)
  → PredictionSnapshot {race_id,session,timestamp,data_cutoff,grid,weather(rich),lineup,model/feature/dataset/calibration versions,seed,config_hash}
  → Feature engineering (30+ features: driver/constructor/circuit/session + 16 manual tunings: weather, chaos, wet, reliability, strategy, gridWeight, safetyCar, tyre, fuel, overtake, aeroMode, trackTemp, humidity, wind, pressure, driverConfidence …)
  → ML zoo (GB/RF/LR) → OOF ensemble (L-BFGS-B) → isotonic calibration — NOT YET ON REAL DATA
  → Monte Carlo (vectorised argsort, dnf/weather/SC aware, seed reproducible, 100-50k sims, clamped) ← production path today
  → Blend ML 45% + MC 55% (or statistical_fallback if no artifact, marked)
  → Calibration + enforce sum + confidence intervals + drift (PSI) + 16 plots
  → Explainability (feature-grounded reasons per driver)
  → Cache → API {prediction_id, snapshot, provenance, probabilities, dnf, explanations}
```

- **Heuristic engine is production**: Monte Carlo + hand-tuned `team_driver_lineup_2026.py` ratings (see §6). `predictor.py` calls `_try_ml_predictions` but `cache/model_cache/*.pkl` not shipped — fresh clone returns `statistical_fallback` until `python -m training.pipelines.train` is wired to real history (see `docs/ML_VALIDATION.md`).
- **Grid official first:** `GridEditor` tries `GET /api/v1/grid/{raceId}` (Jolpica live → simulated Q1-Q3 → manual fallback); manual P1-23 editor is fallback, duplicate P highlight, P1-23 for 23 drivers.
- **Reports simple:** `POST /api/v1/reports/export` with `csv|json|pdf|share` — one click, no how-it-works, embedded at Dashboard bottom, two tables per row.

---

## 5. API — `5000` pure JSON (5000 HTML only for `Accept: text/html` landing)

Base `http://localhost:5000`.

```
GET  /                  → JSON for curl / HTML landing for browser (PORT 5000 — API ONLY badge, decoupled note)
GET  /health, /api/v1/health, /metrics, /docs, /redoc, /api/v1/openapi.json

GET  /api/v1/races
GET  /api/v1/races/:id/result
GET  /api/v1/grid/:race_id → {grid, ordered, source: live|simulated, method, provenance} (for manual editor)
POST /api/v1/predictions (aliases /predict, /predict-session) → {predictions:{winner,podium,points}, winner_probabilities, snapshot, data_quality}
POST /api/v1/predictions/scenario  {race_id, scenario:{weather,grid_positions,...}} → {baseline, scenario, diff}
POST /api/v1/predictions/simulate
POST /api/v1/predictions/jobs → {job_id} ; GET /api/v1/jobs/:id
GET  /api/v1/live/:session → {mode, data:{pit_stops, race_control}, provenance}
GET  /api/v1/live/:session/stream (SSE text/event-stream)

GET  /api/v1/standings/drivers|constructors (Cache-Control: public, max-age=60)
GET  /api/v1/h2h/drivers ; POST /api/v1/h2h/compare → {win_probability}
GET  /api/v1/constructors/teams|power-rankings
GET  /api/v1/analytics/accuracy|feature-weights|targets
POST /api/v1/ai/chat → {response, provider} (offline-fallback 200, never 500)
POST /api/v1/reports/export

GET  /api/v1/system/data-sources → {jolpica, openf1, fastf1, fallback, cache, database}
GET  /api/v1/system/models → {registry, zoo, calibration, versions}
GET  /api/v1/system/health

GET  /api/v1/news → {news: [{title, source, date, url, image, summary}], source: live-bbc|live-rss|fallback, count} (Formula1.com RSS → BBC RSS → curated fallback)
GET  /api/v1/settings → {settings, overrides} ; GET /api/v1/settings/schema ; POST /api/v1/settings ; POST /api/v1/settings/reset
```

Errors always `{"error":{"code","message","details","request_id"}}` + `X-Request-ID`. Frontend 5178 proxies `/api`, `/health`, `/metrics`, `/docs`, `/redoc` to 5000 for dev.

---

## 6. Data & ML Training — status: heuristic production, ML not yet validated on real data

```bash
python -m training.pipelines.train   # builds SYNTHETIC dataset (rng.normal), OOF ensemble, calibration → cache/model_cache/*.pkl
cat training/model_registry/registry.json  # champion entry — metrics are SYNTHETIC until backfill lands
```

- **Today**: `training/datasets/builder.py` generates synthetic rows via `np.random.default_rng(42).normal(0.5, 0.15)` + driver `strength` signal — not real Jolpica/FastF1 backfill. Feature schema `feature-v8`, dataset `dataset-v14` are real, but labels are synthetic. Metrics (Brier/ECE/top1) are **not yet validated on real data** — see `docs/ML_VALIDATION.md` for the target validation protocol (temporal holdout, rolling-origin).
- **Next**: wire `builder.py` to backfill from `JolpicaClient` + `FastF1Provider` (see `docs/ML_ARCHITECTURE.md` §3.1), replace hand-typed `strength` with Elo/Glicko-2 from real results.
- `training_cutoff` is respected (no leakage). `python -m training.pipelines.train` temporal split `2018-2023 train → 2024+ valid` (never random CV).

---

## 7. Frontend Pages (current)

- **Home `/`** — hero `F1_monaco.mp4` poster `night_race.png`, `NextRaceCountdown`, `StartLights`, stat ticker, then **recreated below 10k sims**: Cinematic Dusk Break (second video `Formula_One_race_at_dusk_1.mp4` with Mode Override card, research-backed), Regulation Atlas (4 cards: Active Aero, PU 50/50, Sustainable Fuel, Smaller & Lighter), Prediction Playground (mini 4-race win-prob), Team Voyage (horizontal 7 liveries to `/fantasy`), Intelligence in Motion (6 numbers + live news teaser), CTA. No old RaceWeekend/Garage etc — thought outside, font kept (`f1-display` + `IBM Plex Mono`).
- **Predictions `/dashboard`** — single top image only (`circuit2.png`), row1: Race & Session (Grand Prix → day Friday/Saturday/Sunday → session dropdown FP1-3 / Q1-3 + Sprint if sprint weekend / Race) + Modify 16 tunings + sims 100-50k custom, row2: Manual Grid P1-23 (official `GET /grid/{race}` → simulated Q1-Q3 → manual fallback, duplicate highlight, 23 drivers) + green Run `Run Prediction — Green` (no API key), results: `PodiumReveal` + `TireStrategy` + **16 plots** (Win Top8, Podium, Points, Doughnut, Gauge, Win vs Grid, Radar, Scatter, Polar, Horizontal, Area, Grid vs Win, CI, DNF, Chaos, SC) tuned to predictions, tables two per row (`grid md:grid-cols-2`), Reports simple at bottom (CSV/JSON/PDF/Share → Create & Download, no how-it-works).
- **Standings `/standings`** — driver + constructor (11 teams) championship, 12 plots (progression dynamic by round slider 1-14, constructor doughnut, driver horizontal bar, constructor vertical, wins pie, podiums polar, gap line, wins, per-round area, stacked, radar, momentum), tables with P/W/P/Gap, constructors fixed (was grey, now `team_id` → `team` mapping).

- **H2H `/h2h`** — 16 plots (attributes, radar 5-axis, win bar, doughnut, form 8R, polar, trend area, scatter, grouped wet vs dry, pie, horizontal consistency, Elo 8R, bubble, stacked, insights table + gauge), green Compare button, accuracy via Elo 400, ideas in insights.
- **Fantasy `/fantasy` (was Teams `/teams`)** — `frontend/src/pages/Constructors` now Fantasy helper: hero $100M budget bar, scoring explainer (Qualifying 10→1, Race 25→1 DNF -20, Sprint 8→1 DNF -10, chips 6), builder 5 drivers (price `3+strength*0.27` 0.5 step) + 2 constructors (power→price) with images, team colors, price PPM, selection border, Boost 2× + 6 chips (Wildcard etc), Value Picks PPM ranking top8, Predicted bar (y horizontal), Insights (Best Captain/Value/Differential), Price Change Predictor, Plan Transfers — research via fantasy.formula1.com + FanAmp, Monte Carlo predicted points.
- **Analytics & News `/analytics`** — How it works, What it contains (6 stack), How to use (4 steps), **Live News** via `GET /api/v1/news` (Formula1.com RSS → BBC RSS → fallback, 6 cards), Model Card (Intended Use/Training Data/Limitations v12.4), 2026 Timeline (6 steps Jan 2024→Now), Tech Stack Deep Dive, feature weights interactive, drift — creative, research-backed.
- **Settings `/settings`** — Control Center — everything tunable: Quick (primary, sims, chaos + presets Conservative/Aggressive/Qualifying/Race/Dark/Light/Performance + Live preview card + perf estimator), Appearance (9 colors live), Search (global field/help/value + popup), Groups (10 via `/schema` + frontend Appearance/Quick/Accessibility), Field help per key, dirty amber, raw JSON, Export/Import, Save diff `POST /settings`, Reset, instant paint via `localStorage f1-settings-cache` (fast load <50ms vs 800ms).

Navigation: `Home → Predictions → Standings → H2H → Fantasy → Analytics & News → Settings` (previously `Teams`, `Reports` now embedded, `Live Race`/`Scenario Lab` removed but files remain for history).

---

## 8. Configuration (.env)

```
SEASON_YEAR=2026
SECRET_KEY=change-me
DATABASE_URL=sqlite:///./f1_predictions.db  (prod postgres://)
REDIS_HOST=localhost REDIS_PORT=6379 REDIS_REQUIRED=false ENABLE_IN_MEMORY_FALLBACK=true
CORS_ORIGINS=*  FRONTEND_ORIGIN=https://your-frontend.vercel.app  (prod allowlist)
MODEL_VERSION=12.4 FEATURE_VERSION=8 DATASET_VERSION=14 CALIBRATION_VERSION=3.1
LIVE_UPDATE_INTERVAL=300
AI_PROVIDER=huggingface HUGGINGFACE_API_KEY= OPENAI_API_KEY=
# + 80+ keys via GET /api/v1/settings (all patchable)
```

API keys never persisted; `ai_service` falls back to `200 offline-fallback` if no key. Colors live via `localStorage f1-settings-colors`, `f1-ui-prefs`, `f1-settings-cache`.

---

## 9. Testing & Golden Fixtures

```bash
python -m pytest -q                          # 22 passed (api 12 + parity 3 + predictor 4 + ai 2 + docs)
PYTHONPATH=. python scripts/generate_golden_fixtures.py  # → backend/app/tests/fixtures/golden/*.json (5)
cd frontend && npm run build                 # 564kB (177kB gzip) — chunk warning expected, PWA 581 KiB
curl -s http://localhost:5000/api/v1/system/data-sources | jq
curl -s http://localhost:5000/api/v1/news | jq .source  # → live-bbc or live-rss or fallback
curl -s -X POST http://localhost:5000/api/v1/predictions -H 'Content-Type: application/json' -d '{"race_id":"au","simulation_count":500}' | jq .winner_probabilities
curl -s http://localhost:5000/api/v1/grid/au | jq .source  # → live or simulated
```

Parity harness: `same input + same seed + same model → same result` within tolerance. Frontend 5178 proxies to 5000 for dev; 5000 HTML landing distinct via `Accept: text/html`.

---

## 10. Docker & Deploy (split, decoupled)

```bash
docker-compose up --build  # backend:5000 + redis:6379 (frontend via npm run dev or Vercel)
# or split:
# Frontend → Vercel (framework: vite, output dist 581 KiB)
# Backend → Render/Railway/Fly (uvicorn 0.0.0.0:5000)
# Redis → managed, Postgres → managed
```

`Dockerfile` legacy single-image (still builds frontend dist but backend remains pure JSON); prefer `docker-compose.yml` for decoupled. `render.yaml` for Render.

---

## 11. Docs

- `docs/ARCHITECTURE.md` — actual production topology (5178 HTML vs 5000 JSON)
- `docs/DATA_ARCHITECTURE.md` — providers + provenance
- `docs/ML_ARCHITECTURE.md` — zoo + OOF + calibration (heuristic production note)
- `docs/ML_VALIDATION.md` — temporal, no leakage
- `docs/PREDICTION_PIPELINE.md` — 13-stage pipeline (day→session, 16 modifies, grid official)
- `docs/MODEL_REGISTRY.md` — champion/challenger
- `docs/API_ARCHITECTURE.md` — contracts + security (5000 vs 5178)
- `docs/DEEP_AUDIT.md` — full audit trace (stale but kept for history)
- `GET /api/v1/settings/schema` — live schema

---

## 12. Troubleshooting

- `Port 5178 in use` → `ss -tlnp | grep 5178` or `npm run dev -- --port 5173` (vite.config 127.0.0.1:5178, package.json also 127.0.0.1:5178)
- `Port 5000 HTML shows API landing` vs `curl http://localhost:5000/ | jq` shows JSON — decoupled by `Accept` header, distinct from 5178
- `Fantasy blank` → hard refresh `Ctrl+Shift+R` to clear PWA cache (581 KiB), check `http://localhost:5000/api/v1/h2h/drivers` 200
- `Settings slow` → now instant via local cache (<50ms), then merges API; check `localStorage f1-settings-cache`
- `no such table` → `python3 scripts/migrate_db.py`
- `AI 500` → now `200 offline-fallback`; add key to `.env` or `/settings` → AI Provider
- `Unknown race_id` → `400`, use `au,mc,sg` etc. (23 rounds, 6 sprint)
- `CORS` → set `FRONTEND_ORIGIN` allowlist in prod (`*` with credentials rejected)
- `Redis required` → set `REDIS_REQUIRED=false` for dev (in-memory DictCache fallback)
- `Grid official not loading` → check `GET /api/v1/grid/au` → `source: live` or `simulated` (2026 future races are simulated)

---

Built as **Intelligence Engine** — *What is most likely, why, what could change it, and what if I change one condition?* — 2026 regs: 768kg, 50/50 PU, sustainable fuel, active aero every lap — research: FIA Section C issue 18, Formula1.com 12 changes, BBC Sport, fantasy.formula1.com.
