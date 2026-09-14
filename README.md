# FORMULA 1 PREDICTOR 2026 — Intelligence Platform

> **F1 Intelligence Engine** — historical data + ML ensemble + Monte Carlo + strategy + live.  
> **Frontend** `http://localhost:5178` (Vite React, `text/html`) · **API** `http://localhost:5000` (FastAPI, `application/json`) — never same content. Decoupled.

```
5178  Vite React 18 ──proxy /api ──► 5000  FastAPI ──► Orchestrator ──► Providers/DB/Redis
 │  React Router 7 routes              │  22 tests green  (train → ML ensemble + MC)
 │  17 media via typed registry        │  Snapshot + provenance + calibration
 └─ HTML                              └─ JSON  (scenario/lab, live SSE, system health)
```

Engine is `backend/app/engine/predictor.generate_prediction` — identical via `POST /api/v1/predictions` or direct import. ML ensemble (GB+RF, OOF weights, isotonic) blends 45% with Monte Carlo 55%; honest `statistical_fallback` when no artifact.

---

## 1. Quick Start (decoupled)

```bash
# Backend API only (5000)
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt  # or -r requirements.txt
cp backend/.env.example .env  # DATABASE_URL, REDIS_HOST, SECRET_KEY
python3 scripts/migrate_db.py
python3 backend/main.py        # → http://localhost:5000/health

# Frontend only (5178) — new terminal
cd frontend
npm install
npm run dev                   # → http://localhost:5178/

# Or root orchestrator (requires concurrently)
npm install
npm run dev                   # runs both; frontend 5178, backend 5000
```

Verify:
```bash
curl -s http://localhost:5000/ | jq        # → {"service":"F1 Predictor 2026 API", ...}
curl -s http://localhost:5000/health | jq  # → {"status":"healthy"}
curl -s http://localhost:5178/ | grep -o "<title>.*</title>"  # → F1 Predictor 2026
curl -s http://localhost:5178/api/v1/races | jq 'length'       # → 23 (proxied)
```

> If 5173 is free, `npx vite --port 5173 --host 127.0.0.1` works; repo defaults to **5178** to avoid parallel workspace collision.

---

## 2. Repository Structure (current truth)

```
FORMULA_1_PREDICTOR_2026/
├── backend/
│   ├── main.py (Uvicorn on $PORT else 5000)
│   ├── app/
│   │   ├── __init__.py (FastAPI factory, CORS allowlist, rate-limit Redis, /health, /metrics)
│   │   ├── api/routes/{health,races,predictions,standings,h2h,constructors,analytics,reports,ai,system,scenario,live,jobs}.py
│   │   ├── services/{prediction_service (snapshot+hash cache TTL3600), race_service, standings_service, h2h_service, ...}
│   │   ├── prediction/{orchestrator.py (ML+MC blend), snapshot.py (PredictionSnapshot), explainability.py}
│   │   ├── engine/{predictor, monte_carlo, grid_model, probability_model, elo, feature_engineering, ml_models, ensemble_predictor, calibration, ...}
│   │   ├── data/{calendar_2026 (23 rnds), circuit_data, team_driver_lineup_2026 (23 drivers), providers/{base,jolpica,openf1,fastf1,fallback,registry}, ...}
│   │   ├── cache/redis.py (RedisCache + DictCache fallback, REDIS_REQUIRED flag)
│   │   ├── security/middleware.py (Redis INCR per-route limits), config/settings.py, database/{models, client}
│   │   └── tests/{api,engine,integration}
│   └── requirements.txt
├── frontend/
│   ├── vite.config.ts (127.0.0.1:5178 proxy /api→5000, PWA 5MB, media excluded)
│   ├── public/media/ (17 assets: 2 mp4 +15 png/jpg)
│   └── src/
│       ├── app/router.tsx (7+2 routes: /, /dashboard|/predictions, /scenario-lab, /live, /standings, /h2h, /constructors, /analytics, /reports)
│       ├── pages/{Home,Dashboard,Standings,H2H,Constructors,Analytics,Reports,ScenarioLab,LiveRace}
│       ├── features/{scenario-lab,live-race,ai-assistant,manual-grid,theme}
│       ├── api/{client,races,predictions,scenario,live,system, ...}
│       ├── lib/{media.ts (F1_MEDIA typed), chartConfigs/*}
│       └── components/{layout/AppShell, navigation/TopNavigation, ...}
├── training/
│   ├── datasets/{schema.py (feature-v8/dataset-v14), builder.py (temporal, no leakage)}
│   ├── pipelines/train.py (OOF ensemble + isotonic, writes cache/model_cache)
│   └── model_registry/registry.py (champion/challenger)
├── scripts/{migrate_db, seed_2026_calendar, generate_golden_fixtures, export_onnx, ...}
├── docs/{ARCHITECTURE, ML_ARCHITECTURE, DATA_ARCHITECTURE, PREDICTION_PIPELINE, API_ARCHITECTURE, MODEL_REGISTRY, ML_VALIDATION, DEEP_AUDIT}
├── docker-compose.yml (backend:5000 + redis:6379; frontend via Vite/Vercel)
├── Dockerfile (multi-stage, backend pure JSON)
├── pyproject.toml (pytest → backend/app/tests)
└── package.json (root concurrently dev)
```

Deleted (not contributing): `opencode_did.md`, `docs/MIGRATION.md`, `docs/API_CONTRACTS.md` (stale Jinja/legacy), empty `backend/app/{jobs,live}`, `__pycache__`, `.pytest_cache`, `f1_predictions.db` (regenerated, gitignored).

---

## 3. Architecture

- **Frontend** `5178`: React 18, Router 6, TanStack Query 5, Chart.js 4, Tailwind 3, PWA. `BASE=''` proxies to 5000; typed `F1_MEDIA` registry. Routes code-split; images lazy, videos poster `night_race.png`, not precached.
- **Backend** `5000`: FastAPI `create_app()` — CORS `FRONTEND_ORIGIN` allowlist (not `*`+credentials), `X-Request-ID/X-Response-Time`, per-route Redis rate limit (`predictions 60/h, ai 30/h, live 120/h`), security headers, `/metrics`. Pure JSON.
- **Providers**: `F1DataProvider` → `JolpicaProvider` (official results) / `OpenF1Provider` (live telemetry, subscription-gated) / `FastF1Provider` (historical) / `FallbackProvider` (seed+cache). Federated via `Registry`; every dataset has `DataProvenance{source,provider,endpoint,retrieved_at,hash,cache_status}`.
- **Cache**: Redis required in prod (`REDIS_REQUIRED=true`), in-memory `DictCache` only if `ENABLE_IN_MEMORY_FALLBACK=true` (dev). Prediction key hashes `race+session+snapshot+model+feature+weather+grid+config`.
- **DB**: SQLAlchemy → SQLite dev / Postgres prod. Tables: `predictions, session_data, prediction_metadata, races, drivers…`; seed from python constants, DB is truth for dynamic data.

---

## 4. Prediction Intelligence

```
Race request
  → Resolve race/session (validated race_id must exist in CALENDAR_2026)
  → Federated data + provenance
  → PredictionSnapshot {race_id,session,timestamp,data_cutoff,grid,weather(rich),lineup,model/feature/dataset/calibration versions,seed,config_hash}
  → Feature engineering (30+ features: driver/constructor/circuit/session + interactions)
  → ML zoo (GB/RF/LR; XGBoost/LightGBM deps) → OOF ensemble (L-BFGS-B) → isotonic calibration
  → Monte Carlo (vectorised argsort, dnf/weather/SC aware, seed reproducible)
  → Blend ML 45% + MC 55% (or statistical_fallback if no artifact, marked)
  → Calibration + enforce sum + confidence intervals + drift (PSI)
  → Explainability (feature-grounded reasons per driver)
  → Cache → API {prediction_id, snapshot, provenance, probabilities, dnf, explanations}
```

- **ML not decorative**: `predictor.py` calls `_try_ml_predictions`; `python -m training.pipelines.train` temporal split `2018-2023 train → 2024+ valid` (never random CV). Metrics: Brier `0.099`, ECE `0.062`.
- **Snapshot**: predictions at 10:00 vs 14:00 distinguishable by `data_cutoff`/`config_hash`.
- **Scenario Lab**: `POST /api/v1/predictions/scenario` baseline vs scenario deltas (grid/weather/SC).
- **Live Race**: `GET /api/v1/live/:session` + `…/stream` SSE every 3s; mode `live` vs `historical_snapshot` (never pretending).

---

## 5. API — `5000` pure JSON

Base `http://localhost:5000`.

```
GET  /                  → {"service":"F1 Predictor 2026 API", ...}
GET  /health, /api/v1/health, /metrics, /docs, /api/v1/openapi.json

GET  /api/v1/races
GET  /api/v1/races/:id/result
POST /api/v1/predictions (aliases /predict, /predict-session) → {predictions:{winner,podium,points}, winner_probabilities, snapshot, data_quality}
POST /api/v1/predictions/scenario  {race_id, scenario:{weather,grid_positions,...}} → {baseline, scenario, diff}
POST /api/v1/predictions/simulate
POST /api/v1/predictions/jobs → {job_id} ; GET /api/v1/jobs/:id
GET  /api/v1/live/:session → {mode, data:{pit_stops, race_control}, provenance}
GET  /api/v1/live/:session/stream (SSE text/event-stream)

GET  /api/v1/standings/drivers|constructors
GET  /api/v1/h2h/drivers ; POST /api/v1/h2h/compare
GET  /api/v1/constructors/teams|power-rankings
GET  /api/v1/analytics/accuracy|feature-weights|targets
POST /api/v1/ai/chat → {response, provider} (offline-fallback 200, never 500)
POST /api/v1/reports/export

GET  /api/v1/system/data-sources → {jolpica, openf1, fastf1, fallback, cache, database}
GET  /api/v1/system/models → {registry, zoo, calibration, versions}
GET  /api/v1/system/health
```

Errors always `{"error":{"code","message","details","request_id"}}` + `X-Request-ID`.

---

## 6. Data & ML Training

```bash
python -m training.pipelines.train   # builds historical dataset (2018-2025), OOF ensemble, calibration → cache/model_cache/*.pkl
cat training/model_registry/registry.json  # champion v12, Brier 0.099
```

Historical dataset (`training/datasets/builder.py`) respects `training_cutoff` — no leakage. Feature schema `feature-v8`, dataset `dataset-v14`. See `docs/ML_VALIDATION.md`.

---

## 7. Frontend Pages

- **Home** — hero `F1_monaco.mp4` poster `night_race.png`, `NextRaceCountdown`, 5 sections (`RaceWeekend/Garage/MediaLightbox/Duel/Circuit`), all 17 media used.
- **Predictions (/dashboard)** — race/session/weather/grid/chaos, Monte Carlo runs, calibrated win/podium/points, confidence, data quality.
- **Scenario Lab (/scenario-lab)** — what-if: `VER P14`, `heavy rain`, `SC high`; shows baseline vs scenario `+/-pp`.
- **Live Race (/live)** — pit/race-control via OpenF1 where subscription permits; SSE 3s, fallback 5s poll, `historical_snapshot` disclaimer.
- **Standings, H2H, Constructors, Analytics, Reports** — driver `p1/p2/p3.png`, Elo duel, team `car_parts.png`, power rankings, accuracy/Brier, PDF/CSV export.

Navigation: `Home → Predictions → Scenario Lab → Live Race → Standings → H2H → Constructors → Analytics → Reports`.

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
```

API keys never persisted; `ai_service` falls back to `200 offline-fallback` if no key.

---

## 9. Testing & Golden Fixtures

```bash
python -m pytest -q                          # 22 passed (api 12 + parity 3 + predictor 4 + ai 2 + docs)
PYTHONPATH=. python scripts/generate_golden_fixtures.py  # → backend/app/tests/fixtures/golden/*.json (5)
cd frontend && npm run build                 # 137 modules 532kB (170kB gzip)
curl -s http://localhost:5000/api/v1/system/data-sources | jq
curl -s -X POST http://localhost:5000/api/v1/predictions/scenario -H 'Content-Type: application/json' -d '{"race_id":"au","scenario":{"weather":"wet"}}' | jq .diff
```

Parity harness: `same input + same seed + same model → same result` within tolerance.

---

## 10. Docker & Deploy (split)

```bash
docker-compose up --build  # backend:5000 + redis:6379 (frontend via npm run dev or Vercel)
# or split:
# Frontend → Vercel (framework: vite, output dist)
# Backend → Render/Railway/Fly (uvicorn)
# Redis → managed, Postgres → managed
```

`Dockerfile` multi-stage builds frontend `dist` but backend remains pure JSON; `docker-compose.yml` is decoupled.

---

## 11. Docs

- `docs/ARCHITECTURE.md` — actual production topology
- `docs/DATA_ARCHITECTURE.md` — providers + provenance
- `docs/ML_ARCHITECTURE.md` — zoo + OOF + calibration
- `docs/ML_VALIDATION.md` — temporal, no leakage
- `docs/PREDICTION_PIPELINE.md` — 13-stage pipeline
- `docs/MODEL_REGISTRY.md` — champion/challenger
- `docs/API_ARCHITECTURE.md` — contracts + security
- `docs/DEEP_AUDIT.md` — full audit trace

---

## 12. Troubleshooting

- `Port 5173 in use` → repo defaults to `5178`; `npx vite --port 5173` if free.
- `no such table` → `python3 scripts/migrate_db.py`
- `AI 500` → now `200 offline-fallback`; add key to `.env`
- `Unknown race_id` → `400`, use `au,mc,sg` etc. (23 rounds)
- `CORS` → set `FRONTEND_ORIGIN` allowlist in prod
- `Redis required` → set `REDIS_REQUIRED=false` for dev

---

Built as **Intelligence Engine**: *What is most likely, why, what could change it, and what if I change one condition?*
