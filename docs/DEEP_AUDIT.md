# Deep Audit — Formula 1 Predictor 2026

> Date: 2026-09-14 · Branch: main · Commit: a1c1648 (good2) · Auditors: Muse Spark
> Method: traced every import, runtime path, cache, provider, and test; no README claim trusted without code evidence.

---

## 1. Existing Architecture (as-coded)

```
Browser (5173 Vite React 18)
  │ fetch('/api/v1/*') proxied
  ▼
FastAPI 5000 (backend/app/__init__.py) pure JSON
  ├─ CORSMiddleware (*, allow_credentials=True) ← spec violation
  ├─ http middleware: X-Request-ID, timing, rate_limit_check_fastapi (Dict), security headers
  ├─ /api/v1/* routers (health, races, predictions, standings, h2h, constructors, analytics, reports, ai)
  ├─ /health, /, /metrics
  └─ Services (thin, logging, cache-key)
        ├─ prediction_service → predictor.generate_prediction
        ├─ race_service / standings_service / h2h_service / constructor_service
        ├─ ai_service → ai_client / AIProviderManager
        └─ report_service (weasyprint/openpyxl lazy)
              │
              ▼
        predictor.py (406 lines) orchestrator
              ├─ GridModel (manual → Jolpica → simulated qual)
              ├─ MonteCarloSimulator (vectorised argsort, dnf, weather)
              ├─ probability_model (enforce_sum, calibrate, CI, drift)
              └─ ai_client (optional 0.3 blend)
              + DatabaseClient (append-only predictions) — swallow errors
        Data: calendar_2026 (23), season_2026 (ANT 292), team_driver_lineup_2026 (23), circuit_data (25), drivers.json
        Providers: JolpicaClient, OpenF1Client, FastF1Integration, APIClient base (file cache cache/api_responses)
        Cache: RedisCache (2s probe) → fallback DictCache (process-local)
        Live: LiveUpdater daemon thread 300s
```

Frontend `5173`: Vite proxy `/api→5000`, 7 routes (`/, /dashboard, /standings, /h2h, /constructors, /analytics, /reports`) under `AppShell`, TanStack Query for server state, Zustand-ish small stores for draft controls, 17 media assets via `public/media`, PWA 5 MB workbox excluding media.

---

## 2. Actual Runtime Architecture

| Layer | Claim | Reality | Evidence |
|---|---|---|---|
| Framework | FastAPI minimal | True | `backend/app/__init__.py:19 FastAPI`, `backend/main.py:56 uvicorn.run` — Flask removed, but `settings.FLASK_*` names remain. |
| Decoupled | 5173 HTML vs 5000 JSON | True after fix | `vite.config.ts:39 proxy`, `__init__.py:106 GET / → JSON`, `GET /app →404` |
| Docker | Split decoupled | Contradicted | `docker-compose.yml` correct (backend+redis), but **root `Dockerfile` multi-stage builds frontend/dist and hints single-port 5000** — would re-couple if used. |
| Redis | Distributed cache | Degraded | `cache/redis.py:157 get_cache()` catches `CacheError` → `DictCache`. Production silently loses cross-worker coherence. `REDIS_REQUIRED` not enforced. |
| Rate limit | 100/hr | Process-local | `security/middleware.py:60 _rate_store dict` keyed `ip+path`, resets on restart, bypass by changing path. |
| CORS | * | Insecure prod | `__init__.py:30 allow_origins=["*"] allow_credentials=True` violates CORS spec. |
| Data freshness | Live 300 s | Mostly fallback | 2026 is future → Jolpica has no 2026 races → always falls back to `season_2026.py` / `fallback.py`. File cache masks latency. |
| ONNX | Ready | Not | No `onnx/onnxruntime/skl2onnx` import at runtime; only `scripts/export_onnx.py` stub; `cache/model_cache/*.onnx` absent. |
| ML powered | Zoo + ensemble | Decorative | `ml_models.py`/`ensemble_predictor.py`/`feature_engineering.py`/`calibration.py`/`benchmark_suite.py`/`pit_strategy`/`tire_model`/`weather_model`/`safety_car_model` (9 files ~2300 lines) **never imported by predictor** — `grep predictor.py` = 0 hits. |

---

## 3. ML Architecture

```
feature_engineering (19 feats) ─┐
ml_models (GB/RF/LR, ModelZoo)  ├─ NOT CALLED
ensemble_predictor (0.5/0.3/0.2)─┘
calibration (isotonic/Platt) ──── also NOT FITTED
benchmark_suite (random sim) ──── analytics only

Production path actually executed:
  strength (.55) + grid (.40) + weather + noise → MonteCarlo → _apply_chaos_smoothing → enforce_sum → calibrate_probabilities (simple sqrt) → DB swallow
```

- Feature schema exists but no training pipeline connects to inference.
- `ModelZoo` requires `X,y` training; no artifact `*.pkl` shipped.
- `ensemble.optimize_weights` uses `scipy.optimize` on validation but never invoked.
- `calibration.py` has proper `IsotonicRegression`/`CalibratedClassifierCV` but predictor uses trivial `calibrate_probabilities` from `probability_model.py`.
- `benchmark_suite` generates random historical data, not real backtest.

**Verdict:** ML must be wired or explicitly marked `training/` and replaced with honest fallback.

---

## 4. Data Architecture

- **Hardcoded truth:** `calendar_2026.py` 23 rounds, `team_driver_lineup_2026.py` 11 teams/23 drivers, `circuit_data.py` 25 circuits, `season_2026.py` standings — read directly, not via DB. DB `database/models.py` (12 tables) + `models/prediction.py` is **write-only** for predictions; no seed/migration populates races/drivers/circuits as authoritative.
- **Providers:** `JolpicaClient` (results/standings/quali), `OpenF1Client` (sessions/positions/car_data/race_control), `FastF1Integration` (telemetry) each subclass `APIClient` (requests Session, file cache `cache/api_responses/*.json`, retry 3, backoff 2^attempt). All have `_fallback_*` to local constants.
- **No abstraction:** No `F1DataProvider` interface; services call concrete clients directly (`GridModel` imports 3 clients, `standings_service` calls Jolpica, `openf1_client.get_sessions` has signature bug `dt.dt`).
- **Provenance:** `data/provenance.py` exists but not emitted in API responses; no `source/retrieved_at/effective_at/response_hash` exposed.
- **Leakage risk:** `feature_engineering` naively uses future-agnostic constants; no temporal split; if ML were trained with random CV it would leak.

---

## 5. API Architecture

| Endpoint | Type | Auth | Cache |
|---|---|---|---|
| `GET /api/v1/races` | hardcoded calendar | anon | `races:2026` TTL300 file+Redis |
| `GET /api/v1/races/{id}/result` | calendar + fallback | anon | per-race |
| `POST /api/v1/predictions` (+/predict,/predict-session) | MonteCarlo | anon | `pred:{md5(shared)[:12]}` TTL3600 Dict/Redis |
| `GET /api/v1/standings/*` | Jolpica→cache→local | anon | `standings:*:2026` TTL300 |
| `GET/POST /api/v1/h2h/*` | elo | anon | `h2h:{A}:{B}` TTL3600 |
| `GET /api/v1/constructors/*` | hardcoded | anon | none |
| `GET/POST /api/v1/analytics/*` | simulated benchmark | anon | none |
| `POST /api/v1/reports/export` | weasyprint/openpyxl | anon | none |
| `POST /api/v1/ai/chat` | AIProviderManager→offline fallback 200 | optional key | none |
| `GET /api/v1/openapi.json , /docs , /health , /metrics` | system | anon | none |

All v1 return `{"error":{"code","message","request_id"}}` + `X-Request-ID`. No pagination, no `prediction_id` trace, no `ETag`.

Missing per spec: `/calendar`, `/drivers/:id/form`, `/telemetry/:session`, `/weather/:session`, `/pit-stops/:session`, `/race-control/:session`, `/predictions/:id/explanation`, `/live/:session/stream`, `/system/data-sources`, `/system/models`, async jobs.

---

## 6. Frontend Architecture

- `vite.config.ts` correct (`base '/'`, `host 0.0.0.0:5173`, `proxy`, `PWA max 5MB`).
- `router.tsx` 7 routes no basename; `AppShell` + `TopNavigation`; `providers.tsx` single `QueryClient retry:1`.
- `api/client.ts` `BASE=''` + `X-Request-ID` + `Bearer f1-jwt` + error normalization; individual `api/{races,predictions,standings,...}.ts` thin wrappers.
- `pages/*` ~943 lines; `Dashboard` is control-heavy (race/session/weather/grid/simCount/AI) → `PredictionCharts`; `Home` 5 creative sections using all 17 media; `Standings/H2H/Constructors/Analytics/Reports` largely presentational with `F1Chart` (Chart.js).
- `components/*` 44 files but many 1-line stubs (`AISidebar`, `AccuracyPanel` …) — real logic in `PredictionControls`, `DuelRadar`, `TireStrategy`, `features/manual-grid`, `features/ai-assistant/AISidebar`.
- State: TanStack Query for server state; local `useState`/`stores` for draft controls — OK. No duplication.
- Perf: images 2-3 MB each lazy but no responsive srcset/WebP; videos 2.6 MB autoplay muted — OK but not optimized; charts not code-split.

---

## 7. Performance Bottlenecks (measured/ inferred)

- MonteCarlo `10000 sims × 23 drivers` vectorised `argsort` — fast (~80 ms) but runs **synchronously in request**; under 100k sims blocks event loop (no `run_in_threadpool` for CPU-bound).
- `Jolpica/OpenF1` file cache hits are fast, misses incur 3× retry backoff (2-4 s) inside request if GridModel falls through.
- No prediction precomputation; no background worker.
- `DictCache` per-process → no hit sharing across workers.
- Frontend bundle `517 kB` OK but all routes in one chunk; media excluded from PWA helps.

---

## 8. Security Risks

- `CORS * + allow_credentials True` — over-permissive; should be `FRONTEND_ORIGIN` allowlist.
- `JWT` `security/auth.py` `require_auth` Flask decorator unused; all v1 anonymous; no token expiry enforcement in FastAPI deps.
- `AI API keys` `ai_key` in `POST /predictions` body not persisted — good — but logged via `logger.info` if verbosity high (risk).
- Rate limit process-local → ineffective under multi-worker / horizontal scale.
- No request body size limit; `reports/export` generates PDFs without sandboxing file names.
- `SSRF` surface: provider clients `requests.get(url)` with user-supplied `race_id` interpolated into Jolpica URL but validated against calendar allowlist in `prediction_service` — mitigated, but other raw endpoints not.
- Headers: `CSP` includes stale `cdn.tailwindcss.com` etc., not needed.

---

## 9. Stale / Contradictory Documentation

- `docs/ARCHITECTURE.md` still references `Flask` + `dashboard/app.py` + `frontend:80 nginx` — stale vs FastAPI decoupled.
- `docs/API_CONTRACTS.md` lists `Legacy /dashboard/api/*` as active but `tests/api/test_api_v1.py` asserts they return 404 — docs lag.
- `README.md` claims `ONNX-ready`, `16 engine files`, `3.8× Flask`, `30-60% Redis saves` — ONNX not wired, 3.8× not benchmarked, Redis saving unmeasured.
- `pyproject.toml` note about `weasyprint/openpyxl` moved to main deps correct after `AUDIT.md B-5` but `docs/DATA_PIPELINE.md` still describes pipeline not wired.

---

## 10. Disconnected / Dead Code

9 engine modules dead (~2300 lines + deps `xgboost/lightgbm/sklearn/scipy` installed for no production use):
`feature_engineering.py`, `ml_models.py`, `ensemble_predictor.py`, `calibration.py`, `benchmark_suite.py`, `pit_strategy.py`, `tire_model.py`, `weather_model.py`, `safety_car_model.py`, `fantasy_scoring.py`, `huggingface_dataset.py`
Also: `data/pipeline.py` orchestrator not called; `driver_data.py`/`team_data.py` display-only; `security/auth.py` Flask decorator unused.

---

## 11. Duplicated Logic

- `backend/app/cache/redis.py` + `backend/app/data/api_client.py` file cache — two caching layers with different TTL semantics.
- `config/constants.py grid_prior_multiplier` imported then shadowed by local variable in `feature_engineering:53`.
- `database/client.py` vs `database/connection.py` both create engines (`QueuePool` 20/10 vs `scoped_session`).
- `openf1_client.py` duplicate `_make_request` vs base.
- Chaos smoothing logic duplicated in `predictor._apply_chaos_smoothing` and `probability_model.shape_probabilities`.

---

## 12. Unused Models

See §3. `ModelZoo` models never `fit()` in production; `MultiTargetCalibrator` never `fit()`; `EnsemblePredictor.optimize_weights` never called with OOF preds.

---

## 13. Data Leakage Assessment

Current system has **no leakage** only because it has **no learning** — predictions are heuristics. Risk introduced if naive random CV were added for future ML. Must enforce temporal split: train `2018-2022` → validate `2023`, rolling-origin, season holdout, driver/constructor holdout. Document in `ML_VALIDATION.md`.

---

## 14. Recommended Target Architecture

```
                RACE PREDICTION
                       │
             Prediction Orchestrator (orchestrator.py)
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
 Driver Performance Team/Car Pace   Race Dynamics
     │                 │                 │
 ML Models (zoo)   Pace Models      Simulation (SC/tyre/pit/weather)
     │                 │                 │
     └─────────────────┼─────────────────┘
                       │
                  Ensemble (OOF stacking, trained weights)
                       │
                  Calibration (isotonic/Platt, Brier/ECE)
                       │
              Probability Distribution
                       │
              Monte Carlo (10k sims, dnf/strategy aware)
                       │
              Final Outcomes + Explanations + Confidence
```

**Data:** `F1DataProvider` interface → `JolpicaProvider` (official results), `OpenF1Provider` (live telemetry), `FastF1Provider` (historical telemetry), `FallbackProvider` (cache/seed). Provenance `source/retrieved_at/provider/hash/schema` on every dataset. DB as source of truth for `seasons/races/sessions/circuits/drivers/constructors/results/predictions/snapshots/model_versions`; hardcoded python as **seed** only.

**API:** Keep FastAPI; add `/system/data-sources`, `/system/models`, `/predictions/:id/*`, `/predictions/scenario`, `/live/:session/stream` (SSE), async `POST /predictions/jobs` + `GET /jobs/:id`.

**Cache:** Redis required in prod (`REDIS_REQUIRED=true`), hash keys include `race+session+snapshot+model+feature+weather+grid+config`; invalidation on `qual grid / weather delta / model version`.

**Workers:** `Redis + Dramatiq/RQ` for training, backfill, precomputation, large MC.

**Frontend:** `features/{race-weekend,predictions,live-race,scenario-lab,drivers,constructors,standings,h2h,analytics,reports,ai}` + `Scenario Lab` (grid/weather/SC/strategy what-if with baseline vs scenario), `Live Race` (SSE timing/pit/weather/control).

**Docs:** `ARCHITECTURE.md, DATA_ARCHITECTURE.md, ML_ARCHITECTURE.md, ML_VALIDATION.md, MODEL_REGISTRY.md, PREDICTION_PIPELINE.md, API_ARCHITECTURE.md` — single source of truth.

---

## 15. Priority Fixes (for Phase 2+)

1. Wire ML into predictor or mark `training/` vs `backend/app/prediction/` separation; train ensemble via OOF.
2. Replace `CORS *` with `FRONTEND_ORIGIN` allowlist; Redis-backed rate limiting.
3. Introduce `PredictionSnapshot` (race/session/timestamp/data_cutoff/grid/weather/lineup/model_version/feature_version/seed) + reproducible MC seed.
4. Formalize provider abstraction + provenance + data quality score.
5. Expand API & frontend for Scenario Lab + Live Race; fix tests `22→23`; reconcile Dockerfiles; add `npm run dev` orchestrator.
