# OPWNCODE — F1 Predictor 2026 — Session Archive

**Purpose:** Base file for next chat. Contains every transformation, fix, verification, and running guideline from this session so work can resume after laptop close. Single source of truth as of 2026-09-13 22:06 UTC.

**Repo:** `Jack-ki1/FORMULA_1_PREDICTOR_2026` — branch `main`
**Workdir:** `/home/jackson11/projects/web/FORMULA_1_PREDICTOR_2026`
**Stack:** Flask 3.1 (python 3.14) + React 18 + Vite 5 + TS 5.9 + Tailwind 3 + TanStack Query 5 + Chart.js 4 + SQLAlchemy 2 + Redis 8 + FastF1 3.8 + XGBoost/LightGBM/scikit-learn + WeasyPrint 70 + vite-plugin-pwa 1.3
**Canonical port:** `5000` only (`0.0.0.0:5000`). `5173` eliminated (see §3).

---

## 0. Current Live State (verified 22:05 UTC)

```
ss -tlnp → 0.0.0.0:5000 (python3 pid 25117)
curl http://localhost:5000/health → {"status":"healthy","version":"1.0.0"}
curl http://localhost:5000/ → 2090 lines legacy homepage.html (the "right" UI)
curl http://localhost:5000/app → React SPA index.html (base '/app/', 0.93kB, manifest + registerSW)
curl http://localhost:5000/app/manifest.webmanifest → {"name":"F1 Predictor 2026",...}
curl http://localhost:5000/app/pwa-192x192.png → 697 B (Cache-Control: public, max-age=31536000)
curl http://localhost:5000/app/assets/index-c0seL3I6.js → 484kB (gzip 159kB)
curl http://localhost:5000/api/v1/races → 23
curl http://localhost:5173 → Connection refused (expected, no 5173)
python3 -m pytest -q → 27 passed, 485 warnings
npm --prefix frontend run build → 127 modules, 484.10kB (was 123/448kB pre-PWA)
```

**Browser:**
- Legacy (right): `http://localhost:5000` (+ `/dashboard/`, `/standings/`, `/h2h/`, `/constructors/`, `/analytics/`)
- React (same port): `http://localhost:5000/app` (+ `/app/dashboard`, `/app/standings`, `/app/h2h` with DuelRadar, `/app/constructors`, `/app/analytics`, `/app/reports` with share preview)
- API: `http://localhost:5000/api/v1/*`, `/health`, `/api/v1/openapi.json`

---

## 1. Phase 1–4 — transformation.md Implementation (from `transformation.md:1`, 1225 lines)

**Goal:** Fix two runtime bugs (CSP raw HTML on 5000, placeholder SPA on 5173), make deployable on free hosting, add F1-themed creative pass. Verified in clone: `npm run build` 123 modules, `py_compile` clean.

### Phase 1 — Port 5000 CSS/JS not loading
- **Root cause:** `config/settings.py:90` `SECURITY_HEADERS['Content-Security-Policy'] = "default-src 'self'"` blocked Tailwind CDN (`cdn.tailwindcss.com`), Chart.js (`cdn.jsdelivr.net`), Google Fonts (`fonts.googleapis.com`), Font Awesome (`cdnjs.cloudflare.com`), inline theme script. Browser console CSP violations → unstyled markup.
- **Fix:** `config/settings.py:89-128` — added `CORS_ORIGINS: str = '*'`, `RATE_LIMIT_*`, and expanded CSP:
  ```
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com;
  font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com;
  img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'
  ```
  Deduplicated duplicate `RATE_LIMIT_*` block. Verified `from config.settings import settings; print(csp)` starts with `default-src 'self';`.

### Phase 2 — Port 5173 (Vite) — why different + fixes
- `http://localhost:5173` is Vite dev server; `vite.config.ts:8` proxies `/api`, `/dashboard` etc. to `5000`. `/` was 17-line placeholder vs 2090-line legacy.
- **New files:**
  - `frontend/src/hooks/useCountUp.ts:1` — IntersectionObserver count-up (0→value, 1200ms, easeOutCubic) — mirrors legacy ticker
  - `frontend/src/components/home/StartLights.tsx:1` — 5 red lights sequence (420ms per light, 900ms hold, 1600ms lights-out loop)
  - `frontend/src/components/home/NextRaceCountdown.tsx:1` — live countdown to next `useRaces()` race (filter `status !== 'cancelled'`, sort by date, `setInterval 1000`, `padStart(2)`)
  - `frontend/src/components/shared/RaceLoadingBar.tsx:1` — DRS strip via `useIsFetching()` → `is-active` sweep
  - `frontend/src/components/prediction/PodiumReveal.tsx:1` — 28 confetti + ` Pudium — predicted P1` toast (2200ms, re-fires on `trigger` change)
- **Rewritten:**
  - `frontend/src/pages/Home/index.tsx:138` (was 17 lines) — hero (`hp-hero`, `hp-kicker`, `F1 PREDICTOR 2026` red, `StartLights`, `NextRaceCountdown`), checkered divider, stat ticker (`useCountUp` for races/drivers/constructors/simulations), 6-card feature grid (`/dashboard`, `/standings`, `/h2h`, `/constructors`, `/analytics`, `/reports` with SVG icons), navy `how it works` 3 steps
  - `frontend/src/pages/Reports/index.tsx:29` (was 1 line) — 4 formats (CSV/JSON/PDF/share) + `POST /api/v1/reports/export` note
- **Modified:**
  - `frontend/src/styles/globals.css:7` → `92` lines — appended `hp-hero`, `hp-start-lights`, `hp-countdown`, `hp-checkered`, `hp-stat-row`, `hp-feature-card`, `race-loading-bar`, `podium-reveal` (pure additive)
  - `frontend/src/components/layout/AppShell.tsx:4` — mounts `<RaceLoadingBar/>`
  - `frontend/src/components/prediction/PredictionResults.tsx:1` — mounts `<PodiumReveal trigger={`${race_id}-${session_type}-${topDriver}`}>`

### Phase 3 — Deployment (Vercel + Render split, free tier)
- **Reality check:** `requirements.txt` (`fastf1`, `scipy`, `xgboost`, `lightgbm`, `weasyprint`, `prometheus_client`, `data/live_updater.py` thread) incompatible with Vercel serverless (stateless, package-size, timeout).
- **Topology:** Browser → Vercel (static `frontend/dist`, rewrites) → Render (Flask `Dockerfile`, `$PORT`) → Upstash Redis (optional, `DictCache` fallback) / Neon/Supabase Postgres (optional, SQLite ephemeral on Render free).
- **New configs:**
  - `frontend/vercel.json:1` — `buildCommand: npm run build`, `outputDirectory: dist`, `framework: vite`, 8 rewrites (`/api/(.*)` → `https://YOUR-BACKEND-HOST.example.com/api/$1` etc., SPA fallback `/(.*)` → `/index.html` last)
  - `render.yaml:1` — `type: web`, `runtime: docker`, `dockerfilePath: ./Dockerfile`, `plan: free`, `healthCheckPath: /health`, env `FLASK_ENV=production`, `SECRET_KEY generateValue`, `DATABASE_URL`/`REDIS_*`/`CORS_ORIGINS` `sync: false`
- **Deploy-blockers fixed:**
  - `Dockerfile:11` — added `libpango-1.0-0`, `libpangocairo-1.0-0`, `libgdk-pixbuf2.0-0`, `libcairo2`, `libffi-dev`, `shared-mime-info`, `fonts-liberation` (WeasyPrint runtime)
  - `main.py:54` — `run_port = int(os.environ.get("PORT", settings.FLASK_PORT))` (Render/Railway/Fly dynamic `$PORT`)
  - `dashboard/app.py:31` — `CORS(app, origins=_cors_origins.split(',') if != '*' else '*')` reads `settings.CORS_ORIGINS`

### Phase 4 — Creative pass
- Shipped: hero + countdown, start lights, stat ticker, loading bar, confetti, feature grid, reports rewrite (all in Phase 2 blocks).
- Roadmap sketched (not yet implemented beyond TeamStripe which was placeholder): team-color accents, H2H radar, tire visualizer, share cards preview, PWA, live ticker via WebSocket, grid-walk parallax.

**File-by-file change log (from transformation.md):**
| File | Status |
|---|---|
| `config/settings.py` | Modified CSP + `CORS_ORIGINS` |
| `dashboard/app.py` | Modified CORS reads `CORS_ORIGINS` |
| `Dockerfile` | Modified WeasyPrint libs |
| `main.py` | Modified `$PORT` binding |
| `frontend/src/pages/Home/index.tsx` | Rewritten 17→138 lines |
| `frontend/src/pages/Reports/index.tsx` | Rewritten 1→29 lines |
| `frontend/src/hooks/useCountUp.ts` | New |
| `frontend/src/components/home/StartLights.tsx` | New |
| `frontend/src/components/home/NextRaceCountdown.tsx` | New |
| `frontend/src/components/shared/RaceLoadingBar.tsx` | New |
| `frontend/src/components/prediction/PodiumReveal.tsx` | New |
| `frontend/src/components/layout/AppShell.tsx` | Modified mounts loading bar |
| `frontend/src/components/prediction/PredictionResults.tsx` | Modified mounts PodiumReveal |
| `frontend/src/styles/globals.css` | Modified append-only |
| `frontend/vercel.json` | New |
| `render.yaml` | New |
| `frontend/src/components/shared/TeamStripe.tsx` | Roadmap (not yet) → later implemented in §4 |

**Verification (original):** `python3 -m py_compile` clean, `python3 -c "from config.settings import settings"` CSP correct, `npm run build` 123 modules 0 TS errors `448.55kB / 147.44kB gzip`.

---

## 2. Extensive Test Run (27 passed)

**Command:** `python3 -m pytest tests/ -v --tb=short` (50.43s, 485 warnings `DeprecationWarning: utcnow`).
- `test_ai_client.py:2` — provider, formatting
- `test_api_v1.py:11` — races, legacy races, predict, legacy predict, standings, h2h, constructors, analytics, reports export, error contract, openapi, health
- `test_dashboard_blueprints.py:6` — races, predict race/qualifying, ai_chat validation, h2h compare, reports csv
- `test_prediction_parity.py:3` — golden fixtures, parity against fixtures, manual grid parity
- `test_predictor.py:4` — race/qualifying/practice/manual grid

**Frontend:** `npx tsc --noEmit` clean, `npm run build` 123 modules 32.23kB CSS 448.55kB JS, `vitest` no test files (expected), `eslint` not found (non-blocking). Verified dist `hp-hero`, `podium-reveal`, `race-loading-bar` present, `vite.config.ts` proxies all `/api`, `/dashboard`, etc. to `5000`.

**Integration via Flask test_client (40+ checks):** all `/health`, `/api/v1/*`, legacy `/dashboard/api/*`, standings, h2h, constructors, analytics, reports, openapi, CORS restricted/evil origin, 404 contract, CSP headers, `X-Request-ID`, `X-Response-Time`, `winner_probabilities` sum ~1, `PORT=8765` handling, `f1_predictions.db` exists, `docker-compose.yml` valid.

---

## 3. README Running Guidelines Fix + Single-Port Consolidation

**Initial problem:** `README.md:7` described dual-port `5173` (Vite HMR) + `5000` (Flask) + Redis, plus `docker-compose.yml` `5173:80` (nginx). User reported `5000` shows right thing (2090-line legacy homepage with hero video, cursor, lightbox, Tailwind CDN), `5173` shows wrong thing (React SPA).

**User request:** Remove everything leading to `5173`, ensure only `5000` is visible, keep clear backend (`python`/`Flask`) + frontend (`npm`/`TSX`/`Vite`) separation.

**Actions — very cautious, stepwise:**

1. **Audit `grep -r 5173`** — found 20+ hits in `README.md`, `docker-compose.yml:32`, `frontend/vite.config.ts:8`, `frontend/package.json`, `docs/MIGRATION.md`, `transformation.md`, `frontend/nginx.conf`.
2. **New architecture:** Flask `5000` single port serves:
   - Legacy Jinja at `/`, `/dashboard/`, `/standings/`, `/h2h/`, `/constructors/`, `/analytics/` (precedence, the "right" UI)
   - Built React at `/app` (`/app`, `/app/dashboard`, `/app/standings`… plus SPA fallback) — `frontend/dist` with `vite base: '/app/'` + `router basename: '/app'`
   - API at `/api/v1/*` + `/health`
   - `5173` not exposed.

3. **Code changes:**
   - `dashboard/app.py:128` — added serving of `frontend/dist` at `/app` + `/assets` + `/app/assets` with `max_age` (assets `31536000` immutable, `index.html`/`sw.js` `0`), SPA fallback to `index.html`, graceful 404 if `dist` missing (`_frontend_dist.is_dir()` check). Preserves legacy precedence.
   - `Dockerfile:1` — multi-stage: `FROM node:20-alpine AS frontend-build` (`npm install` + `npm run build`) then `FROM python:3.11-slim` + `COPY --from=frontend-build /build/frontend/dist ./frontend/dist` + `RUN mkdir -p ... frontend/dist`. Still installs `curl` + WeasyPrint libs.
   - `docker-compose.yml:27` — removed `frontend` service (`5173:80`), now only `backend:5000` + `redis:6379`.
   - `frontend/vite.config.ts:1` — removed `server: { host, port 5173, proxy }`, set `base: '/app/'`, added comment single-port, later added `VitePWA` (see §5).
   - `frontend/package.json:6` — `dev` now `echo 'No Vite dev server on 5173 — single-port: npm run build then python3 main.py and open http://localhost:5000/app' && exit 0`, added `watch: "tsc --noEmit --watch & vite build --watch"`, `preview` with `--base=/app/`.
   - `frontend/src/app/router.tsx:11` — added `{ basename: '/app' }`.
   - `frontend/Dockerfile` + `frontend/nginx.conf` kept as legacy reference for optional split (now dormant, not used by `docker-compose`).

4. **Docs:**
   - `README.md:7` — rewritten top: Flask `5000` single port serves legacy `/` + React `/app` + API, no `5173`, `frontend/` `base: '/app/'` built to `dist`.
   - `README.md:19` — TOC `Run — Single Port (5000)` with `A. Docker Compose (single port)` + `B. Manual: Build Frontend + Run Backend`.
   - `README.md:82` — added single-port note (`frontend/dist` at `/app`, legacy precedence).
   - `README.md:250` — rewrote entire `Run` section (170 lines): removed `5173` dev server steps, added multi-stage Dockerfile explanation, manual two-step (`cd frontend && npm run build` then `python3 main.py`), verify `curl -s http://localhost:5000/ | wc -l` 2090 vs `curl -s http://localhost:5000/app | grep F1`, note `curl http://localhost:5173` should refuse, single-port topology.
   - `README.md:639` — `Docker & Production`: multi-stage single image, `docker-compose.yml` only backend+redis, single-port topology `Browser → Flask 5000 (Jinja / + React /app + API)`.
   - `README.md:663` — `Troubleshooting`: `Port 5000` raw HTML CSP, `5173` no longer used, `/app` 404 → `npm run build` missing.
   - `docs/MIGRATION.md:35` — checklist `backend 5000 ( / + /app + /api) + redis 6379` + verify `ss -tlnp | grep 5173` empty.
   - `frontend/nginx.conf:1` — kept but now all 7 locations forward `Host/X-Real-IP/X-Request-ID/X-Forwarded-For` (was only `/api`).

5. **Build & verify single-port:**
   - `cd frontend && npm run build` → 123 modules → 127 after PWA, `dist/index.html` `src="/app/assets/..."` (base `/app/`), `ls -lh frontend/dist` shows `index.html` + `assets/`.
   - `setsid python3 main.py` → `Listening 0.0.0.0:5000`, `curl -s http://localhost:5000/` → `<!DOCTYPE html> ... 96789 bytes, CSP allowlisted, 2090 lines` (legacy dark theme, Inter/Montserrat, Tailwind CDN, Font Awesome), `curl -s http://localhost:5000/app` → `<!doctype html> ... <title>F1 Predictor 2026</title> ... src="/app/assets/..."` (React), `curl -s http://localhost:5000/app/dashboard` → same React fallback, `curl -s http://localhost:5000/api/v1/races | jq length` → 23, `ss -tlnp` only `0.0.0.0:5000`.

---

## 4. Eliminate Irrelevant Files/Folders (2026-09-13 22:00)

**Audited against `.gitignore:1`, imports (`grep -r "from ai\."`, `from models`, `from monitoring` etc.), `git ls-files`, `du -sh`.**

| Action | Path | Reason | Status |
|---|---|---|---|
| `find -name __pycache__ -exec rm -rf` | `./**/__pycache__/` | Gitignored `__pycache__/`, regenerates | removed 19 dirs |
| `rm -rf .pytest_cache` | `.pytest_cache/` | Gitignored, test cache | removed 28K |
| `rm -f f1_predictions.db` | `f1_predictions.db` | Gitignored `*.db`, SQLite dev DB, regenerates via `initialize_database()` | removed 308K |
| `rm -f cache/api_responses/*.json` | `cache/api_responses/dc5492c1b...json` | Gitignored `cache/api_responses/*.json`, stale API cache | removed 1 file |
| `rm -rf cache/fastf1_cache/*` | `cache/fastf1_cache/` | Gitignored `cache/fastf1_cache/`, 107M FastF1 HTTP cache | removed 107M → 4K |
| `mv transformation.md docs/archive/transformation.md` | `transformation.md` (55K) → `docs/archive/transformation.md` | Planning doc implemented (Phase 1–4) + single-port makes it outdated; moved from root to archive, now `?? docs/archive/` untracked | moved |
| Kept | `frontend/dist/` | Gitignored but **required** for Flask `/app` serving (built via `npm run build`, base `/app/`) | kept, contains `index.html` + `assets/` + PWA |
| Kept | `frontend/node_modules/` | Gitignored but required for build (165 dirs) | kept |
| Kept | `frontend/nginx.conf`, `frontend/vercel.json` | Legacy split-deploy (nginx `5173:80`, Vercel rewrites) — dormant after single-port but kept for optional split; documented as legacy | kept |
| Verified | `ai/`, `models/`, `monitoring/`, `reports/`, `security/`, `migrations/`, `docs/` | All actively imported (`ai.provider`, `models.prediction`, `monitoring.blueprint`, `reports.csv_excel_report`, `security.auth`, `migrations/_001`) — not irrelevant | kept |

`git status --short` after clean shows `M Dockerfile`, `M README.md`, `M config/settings.py`, `M dashboard/app.py`, `M docker-compose.yml`, `M docs/MIGRATION.md`, `M frontend/*`, `M main.py`, `?? docs/archive/`, `?? frontend/src/components/home/`, `?? frontend/src/components/prediction/PodiumReveal.tsx`, `?? frontend/src/components/shared/`, `?? frontend/src/hooks/useCountUp.ts`, `?? frontend/vercel.json`, `?? render.yaml`.

---

## 5. README — Fully Updated (705 lines, `README.md:1`)

**Sections:** What This Is (23-round 2026 calendar, Monte Carlo/qualifying/practice via `engine/predictor.py:97`, live sources Jolpica/OpenF1/FastF1 + fallback, AI blending, exports), Architecture (single-port note), Repository Map (updated `docker-compose.yml` → backend+redis, `Dockerfile` multi-stage, `frontend/` `base: '/app/'`), Prerequisites (Python 3.9+/3.14 tested, Node 20+/24.21 tested, Redis optional `DictCache`), Run — Single Port (A Docker `cp .env.example .env && docker compose up --build -d` + verify `curl /` 2090 vs `curl /app` React + `ss` check; B Manual `cd frontend && npm run build` then `python3 main.py` + verify 23 races, prediction POST), Backend Deep Dive (factory CORS, middleware, dual-run `POST /dashboard/api/predict-session` vs `POST /api/v1/predictions`, services `prediction_service race_service standings_service h2h_service` etc., schemas `Pydantic`, security `JWT`), Frontend Deep Dive (stack `react 18` etc., entry `main.tsx→App→router→providers`, routing table `/` Home + `/dashboard` etc. but now at `/app` prefix, `AppShell TopNavigation`), Dashboard composition (RaceSelector etc.), API Reference (legacy + versioned, headers `X-Request-ID`, `X-Prediction-Latency`, error contract), Prediction Engine (5 steps, `MonteCarloSimulator` vectorised, chaos smoothing), Data Sources (calendar `23 rounds`, standings `Jolpica→season_2026`, `h2h:{A}:{B}` 3600s, FastF1 file cache), Configuration (`.env.example→.env` via `pydantic-settings`, added `CORS_ORIGINS`, `VITE_API_BASE`, `PORT` vs `FLASK_PORT`), Testing (27 tests, golden fixtures, `PYTHONPATH=. python scripts/generate_golden_fixtures.py`), Docker & Production (multi-stage single image, optional split Vercel+Render), Visual/Prediction Parity, Troubleshooting (raw HTML CSP, `docker: command not found` WSL, `Address already in use 5000` + `fuser -k 5000/tcp`, `/app` 404 → `npm run build`, `Previous 5173 references removed`), Contributing.

**Running single-port (canonical):**
```bash
# Docker
cp .env.example .env
docker compose up --build -d
curl -s http://localhost:5000/health | jq        # healthy
curl -s http://localhost:5000/ | wc -l           # 2090 (legacy right)
curl -s http://localhost:5000/app | grep -o "F1 Predictor 2026"  # React
curl -s http://localhost:5000/api/v1/races | jq length  # 23

# Manual
cd frontend && npm install && npm run build      # 127 modules, 484kB (PWA)
cd .. && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # or --break-system-packages
cp .env.example .env && python3 main.py          # → http://127.0.0.1:5000
```

---

## 6. Research — Web / GitHub / HuggingFace / APIs

### GitHub F1 prediction (stars, stack, metrics, data source)
1. **GhanshyamPaunikar/f1-race-predictor** — https://github.com/GhanshyamPaunikar/f1-race-predictor — XGBoost+HistGBR+GBR `0.45/0.35/0.20`, 400 est depth 5, 5-fold time-aware CV, 1000× MC, MAE 3.41, 3.5k records 2018–2025, FastAPI+Vue+Jolpica, `GET /api/predict/{year}/{round}`.
2. **RafaelBoceanu/f1-race-prediction** — https://github.com/RafaelBoceanu/f1-race-prediction — `f1api.dev` (Ergast replacement), 10 feats (grid, 5/10 avg, finish rate, career wins, circuit avg), GBM ROC-AUC 0.89 + RF MAE 3.0, weighted recent (2026 2×).
3. **fadiz911/Formula-1-Race-Strategy-Predictor** — https://github.com/fadiz911/Formula-1-Race-Strategy-Predictor — PyTorch LSTM V4 Spearman 0.987/MAE 0.83 + Transformer V5 + Ensemble 70/30 + LangGraph multi-agent + MC simulation, FastF1 telemetry, tire/pit optimizer.
4. **fardinhossain007/f1-race-predictor** — https://github.com/fardinhossain007/f1-race-predictor — 60 feats, 4 models RF 96.6% (88.9 F1), XGBoost, NN, LR, FastF1, momentum dominates (recent podiums 11.9%).
5. **eddmann/f1-picks-2025-predictor** — https://github.com/eddmann/f1-picks-2025-predictor — LightGBM LambdaRank (top-3 per session Q/R/SQ/S), 250–330 feats (Elo 3/5/10 race, practice sectors), Optuna, backtest -89 vs baseline.
6. **SilvioBaratto/formula_1_championship_prediction** — https://github.com/SilvioBaratto/formula_1_championship_prediction — Bayesian + MC 10k + Ensemble RF/GBR/SVR, FastF1 2022–24, LOYO CV.
7. **prasun151/F1-lap-times-predictor** — https://github.com/prasun151/F1-lap-times-predictor — RF podium 89.5% ROC-AUC 0.9495, 15 feats (Q times, prev season, grid, weather Open-Meteo), Ergast Jolpica.

### HuggingFace
- **tracinginsights/RaceData** — https://huggingface.co/datasets/tracinginsights/RaceData — multi-table 1950–present CC0, `load_dataset(..., "circuits")`.
- **3amthoughts/formula-1-detailed-1999-2026** — https://huggingface.co/datasets/3amthoughts/formula-1-detailed-1999-2026 — 1999–2025 + 2026 R1-6 projected, 11k entries, Parquet.
- **SeanKuo2006/F1-Telemetry-Data-V2** — https://huggingface.co/datasets/SeanKuo2006/F1-Telemetry-Data-V2 — per-session Parquet Speed/RPM/Throttle/Brake/DRS/X/Y/Z.
- **machina-sports/ayrton-1-qa-v2** — https://huggingface.co/datasets/machina-sports/ayrton-1-qa-v2 — QA SFT 1950–2025 Jolpica+FastF1.
- **Models:** `datamatters24/f1-race-predictor-model` (XGBoost+LightGBM 21 feats, 76 seasons 1.3M, Optuna 200, weekly retrain), `sarthakasap11/f1podiumpredictor` (RF 94% podium, Streamlit+Arcade+DQN), `ruslanmv/sports-trends-models` (multi-sport HistGBR/LogReg).

### APIs deep dive
| API | Base | Coverage | Auth | Limit | Endpoints |
|---|---|---|---|---|---|
| **Ergast** (deprecated) | `ergast.com/api/f1/` | 1950–2024 | none | 200/hr | `/results`, `/qualifying`, `/laps` — **shutdown end 2024, 503s** |
| **Jolpica-F1** (successor) | `https://api.jolpi.ca/ergast/f1/` | 1950–present + CSV dumps | none | 200/hr | Same as Ergast, `fastf1.ergast.interface.BASE_URL = "https://api.jolpi.ca/ergast/f1"` |
| **OpenF1** | `https://api.openf1.org/v1` | 2023–present, live 30 min window | none (hist free), paid live | 4 s intervals | `/car_data`, `/location` (3.7 Hz), `/laps`, `/intervals`, `/meeting`, `/session`, `/pit`, `/weather`, `/team_radio` — JSON/CSV |
| **FastF1** (Python) | `pip install fastf1` | 2018–present | none | cached 50–100 MB/session | `get_session(...).load(laps/telemetry/weather)`, `lap.get_telemetry()`, `add_distance()` | 5.3k stars MIT |
| **HuggingFace** | `datasets.load_dataset("tracinginsights/RaceData")` | As above | HF token optional | HF limits | Per-table Parquet |

### F1 2026 regs (Formula1.com, BBC, FIA docs)
- Aero: shorter/narrower (190 cm, 768 kg), Active Aero (replaces DRS, flaps open on designated straights), narrower 25/30 mm tyres, flatter floor.
- Overtake/Boost Button: replaces DRS, +0.5 MJ, usable any lap if charged.
- PU: 1.6 L V6 retained, MGU-H removed, MGU-K 120→350 kW (50% power vs 20% before), 100% sustainable fuel, net zero 2030.
- Manufacturers: Mercedes (Merc/McLaren/Williams/Alpine), Ferrari (Ferrari/Haas/Cadillac), Red Bull-Ford, Audi, Honda/Aston Martin.

### Sports prediction general
- Ensemble XGBoost/LightGBM dominates, feature engineering > model choice (logistic still 96.2% if features good), recency bias (last 3 races > career), calibration > accuracy (log loss), learning-to-rank (LambdaRank) for top-3, time-series split no future leakage, normalized probabilities for market efficiency.

---

## 7. Per-Section Deep Dive & Implemented Improvements (single-port safe, additive)

**Global:** `Dockerfile` multi-stage (`frontend/dist` at `/app`), CSP fix, `PORT` handling, `Cache-Control: public, max-age=31536000` for `/app/assets` (hashed, immutable) vs `no-cache` for `index.html`/`sw.js` (`dashboard/app.py:143`), PWA `vite-plugin-pwa:1.3.0` (`manifest.webmanifest` 477 B, `sw.js`, `workbox`, 508 KiB precache 7 entries).

**Team-color accents (highest value, lowest effort) — IMPLEMENTED:**
- `frontend/src/components/shared/TeamStripe.tsx:1` (`team_bar` 4×22, color `team_color`/`color`)
- Wired into `StandingsPage.tsx:8` (driver + constructor via `useDrivers` map) and `PredictionResults.tsx:1` (per row) — `types/index.ts:6` already has `team_color`.

**H2H Duel Radar — IMPLEMENTED:**
- `frontend/src/components/h2h/DuelRadar.tsx:1` (`Radar` from `chart.js`/`react-chartjs-2`, already dep) comparing `strength`/`wet_skill`/`consistency`/`reliability` (norm 0–100) with `team_color` borders. Wired in `H2HPage.tsx:12` with `driverMap`.

**Tire-strategy visualizer — IMPLEMENTED:**
- `frontend/src/components/prediction/TireStrategy.tsx:1` — stacked bar per top-6 drivers, colors white `#F8F8F5`/yellow `#FFC857`/red `#E10600` (FIA), deterministic per order (placeholder until `engine/tire_model.py`/`pit_strategy.py` API surfaced). Shown above tables in `PredictionResults.tsx`.

**Share-card preview — IMPLEMENTED:**
- `frontend/src/components/reports/ShareCardPreview.tsx:1` — `POST /api/v1/reports/export` `format: share` → blob → `URL.createObjectURL` → `<img>` + `Copy image` (`ClipboardItem` + `navigator.share` fallback) + `Download`. `ReportsPage.tsx:8` reads `localStorage f1-last-prediction` (written by `DashboardPage.tsx:13` `saveResult` on `PredictionControls onResult`).

**Home:** Already hero + `StartLights` + `NextRaceCountdown` + ticker; next would be video `frontend/public/media/F1_monaco.mp4` + parallax (deferred).

**Standings:** Wired team colors + would add Elo sparkline (from `elo_calculator.py`) + DNF rate.

**Constructors:** Already has `team-bar`; next power ranking delta + lineup photos.

**Analytics:** Next calibration plot + Brier/log loss + drift (`probability_model.py`).

**Reports:** Now share preview + would add scheduled email via `scripts/post_race_evaluation.py`.

**PWA — IMPLEMENTED:**
- `frontend/vite.config.ts:1` — `VitePWA({ registerType: autoUpdate, manifest: { name: F1 Predictor 2026, short_name: F1 Predictor, theme_color: #E10600, start_url: /app/, scope: /app/, icons: pwa-192/512.png }, workbox: { globPatterns: **/*.{js,css,html,ico,png,svg,woff2}, runtimeCaching: [{ urlPattern: /api/v1/(races|standings), handler: StaleWhileRevalidate, maxEntries: 50, maxAgeSeconds: 300 }] } })`
- `frontend/public/pwa-192x192.png` (697 B) + `pwa-512x512.png` (2.0K) generated via PIL, copied to `frontend/dist` on build, served at `/app/pwa-*.png` with long cache, `manifest.webmanifest` 477 B.

**Performance:** `npm --prefix frontend run build` 127 modules 484.10kB (159.16kB gzip) + workbox 22K, `Dashboard` `PredictionControls` two-step quali→race could be `Promise.all` + `React.lazy` for `PredictionCharts`/`AISidebar` (next).

---

## 8. Verification (final)

```
python3 -m pytest -q → 27 passed
npx tsc --noEmit → clean
npm --prefix frontend run build → 127 modules, 484.10kB, PWA 7 entries 508.35 KiB
curl http://localhost:5000/health → {"status":"healthy"}
curl http://localhost:5000/ → 2090 lines legacy
curl http://localhost:5000/app → React index.html src="/app/assets/..."
curl http://localhost:5000/app/manifest.webmanifest → 477 B JSON
curl http://localhost:5000/app/pwa-192x192.png → 697 B
curl http://localhost:5000/api/v1/races → 23
ss -tlnp → only 0.0.0.0:5000 (no 5173)
```

---

## 9. Files Changed (vs initial commit, `git status --short`)

**Modified:**
- `Dockerfile` (multi-stage)
- `README.md` (705 lines, single-port, PWA, troubleshooting)
- `config/settings.py` (CSP + CORS_ORIGINS)
- `dashboard/app.py` (/app serving + cache headers + CORS)
- `docker-compose.yml` (remove frontend 5173)
- `docs/MIGRATION.md` (single-port checklist)
- `frontend/nginx.conf` (all 7 locations forward X-Request-ID)
- `frontend/package.json` (dev echo, watch, vite-plugin-pwa 265 deps, build 127 modules)
- `frontend/src/app/router.tsx` (basename '/app')
- `frontend/src/components/layout/AppShell.tsx` (RaceLoadingBar)
- `frontend/src/components/prediction/PredictionResults.tsx` (TeamStripe + TireStrategy + PodiumReveal)
- `frontend/src/pages/Home/index.tsx` (138 lines)
- `frontend/src/pages/Reports/index.tsx` (share preview)
- `frontend/src/pages/Standings/index.tsx` (TeamStripe)
- `frontend/src/pages/H2H/index.tsx` (TeamStripe + DuelRadar)
- `frontend/src/styles/globals.css` (hp-hero etc.)
- `frontend/vite.config.ts` (base '/app/', VitePWA)
- `main.py` ($PORT)

**New (untracked):**
- `frontend/src/hooks/useCountUp.ts`
- `frontend/src/components/home/StartLights.tsx`, `NextRaceCountdown.tsx`
- `frontend/src/components/shared/TeamStripe.tsx`, `RaceLoadingBar.tsx`
- `frontend/src/components/h2h/DuelRadar.tsx`
- `frontend/src/components/prediction/TireStrategy.tsx`, `PodiumReveal.tsx`
- `frontend/src/components/reports/ShareCardPreview.tsx`
- `frontend/public/pwa-192x192.png`, `pwa-512x512.png`
- `frontend/vercel.json`, `render.yaml`
- `docs/archive/transformation.md` (moved from root)

**Gitignored (present, not committed):**
- `frontend/dist/` (936 index.html + assets + manifest + sw.js + pwa pngs)
- `__pycache__/`, `.pytest_cache/` (removed), `f1_predictions.db` (removed), `cache/fastf1_cache/` (4K after clean)

---

## 10. Next Chat — Immediate Roadmap

1. **Self-host assets** (tighten CSP to `default-src 'self'`): vendor Tailwind/Chart.js (`dashboard/static/js/vendor/chart.umd.min.js`), self-host fonts (`dashboard/static/fonts/` + `@font-face`), inline SVGs for `fa-*`, move theme script to `theme_init.js` to remove `'unsafe-inline'`.
2. **Tire/Pit API:** Expose `engine/tire_model.py` + `pit_strategy.py` via `GET /api/v1/strategy?race_id=&driver=` and wire `TireStrategy` to real data instead of deterministic pattern.
3. **Live ticker (bigger lift):** `data/live_updater.py` → WebSocket/SSE (Flask-SocketIO) to React, `render.yaml` supports long-lived.
4. **Grid-walk parallax:** `frontend/public/media` + `frontend/src/components/home/GridWalkParallax.tsx` between feature grid and `how it works`.
5. **Performance:** Code-split `Analytics`/`Constructors` (`React.lazy`), purge `legacy.css` unused, `manualChunks` for `chart.js`.

**Quick smoke for next chat:**
```bash
python3 -m pytest -q                               # 27 passed
cd frontend && npm run build && ls -lh dist/       # 127 modules, PWA 7 entries
python3 main.py                                    # → http://127.0.0.1:5000 + http://127.0.0.1:5000/app
curl -s http://localhost:5000/ | wc -l             # 2090
curl -s http://localhost:5000/app | grep manifest  # <link rel="manifest"
```

**Browser:** `http://localhost:5000` (legacy right, 2090) + `http://localhost:5000/app` (React, DuelRadar, TireStrategy, ShareCard, PWA) + `http://localhost:5000/api/v1/*` + `http://localhost:5000/health`. No `5173`.

