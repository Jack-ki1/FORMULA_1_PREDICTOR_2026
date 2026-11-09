# F1 Predictor 2026 — Race Intelligence Platform

> Full-stack Formula 1 2026 prediction and race-weekend intelligence app: Vite + React + TypeScript frontend, FastAPI + NumPy Monte Carlo backend, deployable as a single Vercel project with no external databases or paid services required.

**Repository:** `git@github.com:Jack-ki1/FORMULA_1_PREDICTOR_2026.git`  
**Primary branch context in this workspace:** `feat/weekend-views`  
**Working directory:** project root (contains `frontend/`, `backend/`, `api/`, `vercel.json`)  
**License/status:** unofficial fan project (see [Legal / trademarks](#legal--trademarks))

---

## Table of contents

1. [Project overview](#project-overview)
2. [What the app does](#what-the-app-does)
3. [Architecture at a glance](#architecture-at-a-glance)
4. [Tech stack](#tech-stack)
5. [Repository / folder structure](#repository--folder-structure)
6. [File-by-file guide (important files)](#file-by-file-guide-important-files)
7. [Backend design](#backend-design)
8. [Frontend design](#frontend-design)
9. [Prediction model and simulation inputs](#prediction-model-and-simulation-inputs)
10. [Data sources, caching, and offline behavior](#data-sources-caching-and-offline-behavior)
11. [Driver roster (2026 grid used by this project)](#driver-roster-2026-grid-used-by-this-project)
12. [Appearance and color customization](#appearance-and-color-customization)
13. [Local development](#local-development)
14. [Testing and quality checks](#testing-and-quality-checks)
15. [Environment variables](#environment-variables)
16. [API reference summary](#api-reference-summary)
17. [Deployment to Vercel](#deployment-to-vercel)
18. [Troubleshooting](#troubleshooting)
19. [Known limitations and honest notes](#known-limitations-and-honest-notes)
20. [Contributing / maintenance workflow](#contributing--maintenance-workflow)
21. [Legal / trademarks](#legal--trademarks)

---

## Project overview

F1 Predictor 2026 is a race-weekend simulator and analytics dashboard for the 2026 Formula 1 season. It lets a user select a Grand Prix, choose a session type (practice, qualifying, sprint qualifying, sprint, or race where applicable), adjust simulation and model parameters, optionally set a manual starting grid, and run a Monte Carlo prediction.

The UI is **run-gated**: changing controls updates draft state, but prediction results are shown only after an explicit **Run Prediction** action. This avoids accidental recomputation, makes parameter changes deliberate, and keeps stale/fresh result state visible.

The backend exposes a JSON API consumed by the frontend. It can operate in live mode (preferring upstream race data providers when reachable) or offline/snapshot mode using bundled seed data. This makes local development and demos reliable even without network access.

### Goals

- Provide an interactive, explainable race-prediction experience (not a black-box single number).
- Show multiple outcome views: win/podium/top-10 probabilities, expected finish, DNF risk, confidence, strategy odds, qualifying progression, and session-specific plots.
- Support weekend context: calendar, race metadata, sprint detection, weather/track context, and starting-grid options.
- Keep deployment simple: one Vercel project, frontend build output + Python API function.
- Be robust to missing live data: use fallbacks and clear UI states instead of crashing.

### Non-goals / boundaries

- Not an official F1/FIA product.
- Not a betting system; probabilities are model outputs with uncertainty.
- Not a real-time telemetry ingestion platform.
- Not backtested as a production forecasting model; ratings and priors are configurable assumptions.

---

## What the app does

### Dashboard / prediction control center

- Select any configured 2026 round.
- View race/weekend metadata and session context.
- Choose session: `practice`, `qualifying`, `sprint_qualifying` (sprint weekends), `sprint` (sprint weekends), or `race`.
- Choose weather mode and simulation parameters (sim count, chaos, grid weight, reliability, strategy aggression, safety car influence, model/form weights, etc., subject to UI exposure).
- Configure starting grid mode (auto/fetched where available, or manual ordering workflow depending on page controls).
- Run prediction explicitly; stale draft/applied differences are surfaced.
- View result panels and charts only when results are available.

### Session-aware visualizations

The dashboard includes grouped/session-specific plots (via `SessionPlots`) and summary panels:

- Race win/share and outcome summaries.
- Team win-share donut (combined constructor win probability) with legend/key and distinct colors.
- Qualifying/practice/race-oriented plot groups depending on session.
- Strategy odds and confidence indicators.
- Results panel with tabs (Results / Qualifying / Strategy) showing driver rows inline.

### Standings

- Drivers and Constructors tabs.
- Live/current totals where available.
- Fallback visualizations when round-by-round history is unavailable (e.g., points ladder/cumulative fallback, contribution/wins fallbacks).
- Share-of-total-points donut with visible legend/description.

### Head-to-Head

- Compare two drivers.
- Breakdown table (season/model metrics such as points, wins, podiums, qualifying/win/podium/pole probabilities, expected finish, head-to-head indicators as available).
- Multiple comparative plots showing both drivers.

### Fantasy

- Driver pool display (name, team, avatar/logo/code/price/expected points where provided by API/pool).
- Pick workflow (team selection constraints as implemented).
- Evaluation/analysis cards (optimal/comparison/progress/change visuals) using backend fantasy evaluation.
- Works with incomplete picks: backend returns pool/analysis context and validity/issues state.

### Settings

- Theme/mode and appearance controls.
- Accent color and **project color tuning** (core UI, status colors, chart palette, tooltip colors) persisted in browser settings state.
- Engine/prediction defaults (seeded into draft controls as designed).
- Layout/accessibility options (density, reduced motion/high contrast/dyslexia/underline links where enabled).
- Data/privacy utilities and optional API base/timeout/debug behavior (subject to environment/build guards).

### Guide / informational pages

- Static/help content for interpreting outputs and using controls (implementation-specific).

---

## Architecture at a glance

```text
Browser (React SPA)
  ├─ pages/* (Dashboard, Standings, Head2Head, Fantasy, Settings, Guide)
  ├─ components/* + charts/* (UI and visualization primitives)
  ├─ lib/store.ts (Zustand: settings, draft params, applied params, run gate)
  ├─ lib/hooks.ts (TanStack Query hooks -> API)
  ├─ lib/api.ts (typed fetch client)
  └─ lib/appearance.ts (applies settings/CSS variables to document)

            │  HTTP (/api/v1/* in dev/prod routing)
            ▼

FastAPI app (backend/app + api/index.py entry)
  ├─ routes.py / routes_models.py (validation + endpoints)
  ├─ service.py (orchestration: data + model + response shaping)
  ├─ engine.py (Monte Carlo / prediction logic)
  ├─ providers/* (live data access/fallback behavior)
  ├─ cache.py / config.py (TTL, limits, source priority)
  └─ data/seed.json (offline snapshot: drivers, teams, calendar, priors)

            │
            ▼
Upstream providers (when live): Jolpica/Open-Meteo (as configured)
Fallback: bundled seed snapshot
```

### Request flow (prediction)

1. User adjusts dashboard controls -> `draft` state updates in Zustand.
2. User clicks **Run Prediction** -> `run()` copies/sanitizes draft into `applied`.
3. `usePrediction(applied)` (React Query) calls `POST /api/v1/predictions`.
4. Backend validates request (race/session/sub/sims/grid/weights as applicable).
5. Backend loads race/driver/team/context data (live or seed fallback).
6. Engine runs simulation and computes distributions/metrics.
7. Frontend renders result state: `none | hidden | stale | fresh` depending on draft/applied/data.
8. Charts/components receive normalized prediction payload and render with fallbacks for missing fields.

---

## Tech stack

### Frontend (`frontend/`)

| Area | Technology | Purpose |
|---|---|---|
| Framework | React 18 | Component UI |
| Language | TypeScript | Static typing |
| Build tool | Vite | Dev server + production build |
| Styling | Tailwind CSS + global CSS variables | Utility styling + theme tokens |
| Server state | TanStack Query | Fetching/caching/retries/loading states |
| Client state | Zustand (+ persist) | Draft/applied params, settings, fantasy picks |
| Charts | Recharts 3.x + custom primitives | Bars/lines/donuts/radar/scatter/gauge/range visuals |
| Icons | Lucide React | UI icons |
| Animation | Framer Motion (available in stack) | Motion/transitions where used |
| Testing | Vitest + Testing Library + jsdom + MSW | Component/smoke tests and API mocking |

### Backend (`backend/`, `api/`)

| Area | Technology | Purpose |
|---|---|---|
| API framework | FastAPI | HTTP routes, validation integration, docs |
| Validation | Pydantic models | Request/response schemas and constraints |
| Simulation | NumPy | Monte Carlo sampling/vectorized computation |
| HTTP client | httpx (and/or provider deps) | Upstream/live data access |
| Server | Uvicorn (local dev) | ASGI server |
| Tests | pytest | API/engine regression tests |

### Deployment

- **Vercel** single project.
- Frontend built from `frontend/` into static output (configured by `vercel.json`).
- Python serverless function entry at `api/index.py` exposes the FastAPI app.
- Rewrites/proxy behavior route `/api/*` and app paths as configured.

---

## Repository / folder structure

```text
F1_PREDICTOR_26_27_FULL_PROJECT/
├── README.md                  # Project documentation (this file)
├── vercel.json                # Vercel build/runtime/routing config
├── .env.example               # Example environment variables
├── .python-version            # Preferred Python version hint
├── api/
│   └── index.py               # Vercel Python entrypoint for FastAPI app
├── backend/
│   ├── main.py                # Local/dev ASGI app entry (uvicorn target)
│   ├── requirements.txt       # Runtime backend dependencies
│   ├── requirements-dev.txt   # Dev/test backend dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py          # Settings, limits (e.g., MAX_SIMS), env config
│   │   ├── routes.py          # API route handlers
│   │   ├── routes_models.py   # Pydantic request/response models
│   │   ├── service.py         # Business logic / orchestration
│   │   ├── engine.py          # Monte Carlo prediction engine
│   │   ├── cache.py           # Caching helpers/TTL behavior
│   │   ├── data/
│   │   │   └── seed.json      # Offline snapshot: teams/drivers/circuits/calendar/priors
│   │   └── providers/         # Live data provider integrations/fallback logic
│   └── tests/
│       ├── test_api.py        # API endpoint tests
│       └── test_engine*.py    # Engine/model tests (if present)
├── frontend/
│   ├── index.html             # Vite HTML entry
│   ├── package.json           # Frontend scripts/dependencies
│   ├── package-lock.json
│   ├── vite.config.ts         # Vite config (dev proxy/build/test setup)
│   ├── tailwind.config.js     # Tailwind theme/token mapping
│   ├── postcss.config.js      # PostCSS/Tailwind pipeline
│   ├── tsconfig*.json         # TypeScript config
│   ├── public/                # Static assets served as-is
│   └── src/
│       ├── main.tsx           # React bootstrap
│       ├── App.tsx            # App shell/routing/layout
│       ├── index.css          # Global styles + CSS variables + theme rules
│       ├── lib/
│       │   ├── api.ts         # Typed API client and endpoint wrappers
│       │   ├── hooks.ts       # React Query hooks (prediction/meta/races/standings/etc.)
│       │   ├── store.ts       # Zustand store: settings, draft/applied, run gate
│       │   ├── appearance.ts  # Applies settings to CSS variables/document dataset
│       │   └── util.ts        # Shared helpers/formatters
│       ├── pages/
│       │   ├── Dashboard.tsx  # Main prediction workflow
│       │   ├── Standings.tsx  # Drivers/constructors standings + charts
│       │   ├── Head2Head.tsx  # Driver comparison
│       │   ├── Fantasy.tsx    # Fantasy pool/picks/evaluation
│       │   ├── Settings.tsx   # Settings UI
│       │   └── Guide.tsx      # Help/guide content (if present)
│       ├── components/
│       │   ├── Control.tsx    # Session/race controls, run action, sanitization
│       │   ├── Panels.tsx     # Results/Confidence/strategy-related panels
│       │   ├── SessionPlots.tsx # Session/grouped plots and fallbacks
│       │   ├── Visuals.tsx    # Additional visual components
│       │   ├── SideCards.tsx  # Side information cards
│       │   └── ui.tsx         # Shared UI primitives
│       ├── charts/
│       │   ├── DonutChart.tsx
│       │   ├── VBar.tsx / HBar.tsx / StackedBar.tsx
│       │   ├── LineSeries.tsx / ScatterXY.tsx
│       │   ├── RadarChart.tsx / Histogram.tsx / RangeBar.tsx
│       │   ├── DivergingBar.tsx / Gauge.tsx
│       │   └── ChartCard.tsx / index exports
│       └── test/
│           ├── setup.ts       # Vitest/jsdom/MSW setup
│           ├── server.ts      # MSW handlers
│           ├── smoke.test.tsx # UI smoke tests
│           └── fixtures/*.json# Mock API/data fixtures
├── changes/                   # Change notes/spec artifacts (workspace-specific)
└── ai.md                      # Implementation summary notes (workspace-specific)
```

> Note: some generated/local folders (e.g., `frontend/node_modules/`, `.venv/`, build outputs) are expected during development but should not be committed.

---

## File-by-file guide (important files)

### Root

- **`vercel.json`**: Defines how Vercel builds the frontend and serves the Python backend; includes rewrites so SPA routes and `/api` requests work in production.
- **`.env.example`**: Documents supported environment variables. Copy values into local `.env`/shell or Vercel project settings as needed.
- **`.python-version`**: Helps local tooling/selectors choose a compatible Python version.
- **`README.md`**: Operational and architectural documentation.

### `api/`

- **`api/index.py`**: Thin entrypoint that imports/exposes the FastAPI application for Vercel’s Python runtime.

### `backend/`

- **`backend/main.py`**: Local/dev entry module for running Uvicorn (e.g., `python -m uvicorn main:app`).
- **`backend/app/config.py`**: Central config. Important limits/defaults live here (for example `MAX_SIMS`, source priority defaults, cache/timeout settings). Also influences `/meta` response values.
- **`backend/app/routes_models.py`**: Pydantic request models (e.g., prediction/H2H/fantasy inputs). This is where payload validation and defaults are enforced before service logic.
- **`backend/app/routes.py`**: HTTP endpoint definitions. Maps URL paths/methods to service calls and response models.
- **`backend/app/service.py`**: Core orchestration layer. Typical responsibilities:
  - normalize/resolve race and session context;
  - load driver/team/calendar/standings data;
  - call engine;
  - shape API responses for frontend charts/tables;
  - provide fallbacks when live history/fields are missing;
  - handle fantasy evaluation and H2H compatibility fields.
- **`backend/app/engine.py`**: Monte Carlo model implementation. Converts inputs (ratings, grid, weather, reliability, chaos, etc.) into simulated outcomes and aggregate probabilities/metrics.
- **`backend/app/providers/`**: Data provider integrations and selection/fallback logic. Used to prefer live data when configured and available.
- **`backend/app/cache.py`**: Response/data caching utilities to reduce repeated upstream calls and improve latency.
- **`backend/app/data/seed.json`**: Bundled offline snapshot and model priors. This file is critical for deterministic local behavior and fallback mode. It must stay consistent with the intended driver/team/calendar model.
- **`backend/tests/test_api.py`**: API-level tests for endpoints/contracts/regressions.

### `frontend/src/lib/`

- **`api.ts`**: Typed client for backend endpoints. Central place to adjust request/response shapes and endpoint paths.
- **`store.ts`**: Zustand state:
  - `s` (settings, persisted),
  - `draft` (editable controls),
  - `applied` (last run parameters),
  - `run()` run-gating,
  - fantasy picks and reset/replace helpers.
- **`hooks.ts`**: Query hooks wrapping API calls (`usePrediction`, `useH2H`, `useFantasyEvaluate`, standings/races/meta hooks, etc.). Query enablement/keys encode run-gating and dependency rules.
- **`appearance.ts`**: Applies settings to `document.documentElement` style/CSS variables and `data-*` attributes (mode, accent, font scale, radius, density, accessibility flags, custom project colors).
- **`util.ts`**: Formatting and helper utilities shared across pages/components.

### `frontend/src/pages/`

- **`Dashboard.tsx`**: Main workflow page. Connects controls, run state, prediction query, and result panels/plots.
- **`Standings.tsx`**: Championship tables and fallback-friendly charts.
- **`Head2Head.tsx`**: Two-driver comparison UI + comparative charts.
- **`Fantasy.tsx`**: Driver pool rendering, pick management, evaluation visualizations.
- **`Settings.tsx`**: Appearance/engine/layout/accessibility/data controls. Includes project color tuning UI.
- **`Guide.tsx`**: Explanatory content for users (if present in current build).

### `frontend/src/components/`

- **`Control.tsx`**: Session selector and run controls. Contains sanitization logic so invalid sprint/session/sub combinations are corrected (especially when race changes).
- **`Panels.tsx`**: Result/strategy/confidence panels, including tabbed result presentation.
- **`SessionPlots.tsx`**: Centralized plot composition by session/type, including Team Win-Share donut and robust fallbacks.
- **`Visuals.tsx`, `SideCards.tsx`, `ui.tsx`**: Shared presentation/layout primitives.

### `frontend/src/charts/`

Reusable chart primitives built on Recharts/SVG/HTML. These components should:

- accept nullable/missing data safely,
- render a clear empty state,
- size responsively (avoid invisible zero-height charts),
- expose readable tooltips/legends where useful,
- avoid interfering overlays that break hover/click.

**Tooltip style note:** chart tooltips are styled with the project’s tooltip theme variables (default requested look: sky-blue background, red text), configurable via Settings color tokens.

### `frontend/src/test/`

- **`setup.ts`**: Test environment bootstrap.
- **`server.ts`**: MSW handlers for API endpoints used by UI tests.
- **`fixtures/*.json`**: Controlled mock payloads. Keep these aligned with backend contracts and the 22-driver roster.
- **`smoke.test.tsx`**: End-to-end-ish render smoke coverage for key pages/workflows.

---

## Backend design

### FastAPI app structure

The backend follows a simple layered structure:

1. **Routes/models** validate transport-level input.
2. **Service** resolves domain context and coordinates dependencies.
3. **Engine** computes predictions.
4. **Providers/cache/config** supply data and operational behavior.

This separation keeps UI contract changes (routes/models) from leaking into simulation math, and keeps provider/data-source behavior isolated.

### Validation rules (important)

- `sims` must be within configured bounds (UI exposes a practical range; backend enforces max via config, e.g. `MAX_SIMS`).
- Sprint-only sessions are rejected for non-sprint weekends:
  - `sprint`
  - `sprint_qualifying`
- Practice `sub` values must be valid for the selected race/session context.
- Grid/manual overrides (when provided) should reference valid driver codes and be normalized consistently.

The frontend also **sanitizes draft inputs** (race/session/sub) before run/request where possible to prevent avoidable 400 errors.

### Prediction response shape (conceptual)

The exact schema is defined by backend models/service output, but prediction responses generally include:

- race metadata (id/name/round/circuit/sprint/weather context),
- driver-level results (code/name/team, win/podium/top10 probabilities, expected finish/points-like metrics, DNF risk, confidence/interval-related values as implemented),
- qualifying/practice-derived structures when relevant,
- strategy/scenario distributions,
- grid/conversion helpers used by charts,
- diagnostics/meta useful for UI rendering.

Frontend components should treat optional fields defensively and use fallbacks.

### Standings, H2H, and fantasy services

- **Standings:** merges live/seed totals; may provide history when available. Frontend includes fallback charts for missing history.
- **H2H:** compares two drivers using available season and/or model outputs. Compatibility fields (e.g., `points`/`season_points` aliases) may be included to avoid frontend breakage.
- **Fantasy evaluate:** returns pool/optimal picks/evaluation metrics even when user picks are incomplete; response includes validity/issues state rather than failing early.

### Caching and performance

- GET-like data can be cached with short/medium TTLs depending on source volatility.
- Live upstream calls should be bounded by timeouts.
- Simulation cost scales with `sims` and model complexity; keep max sims bounded and UI responsive.
- Vercel CDN caching headers (where used) help absorb repeated reads.

---

## Frontend design

### State model

The app uses a **draft vs applied** pattern:

- **`draft`**: current control values being edited by the user.
- **`applied`**: parameters used for the last explicit run.
- **`applied = null`** initially: no results shown until user runs.
- **`run(draft)`**: applies sanitized/selected parameters and triggers prediction query via applied state.

This pattern prevents UI confusion when users tweak sliders/session selectors but haven’t requested a new simulation.

### Result state UX

Components should distinguish:

- **none**: never run / no applied params.
- **hidden**: data exists conceptually but UI chooses not to show (context-dependent).
- **stale**: draft changed after last applied run.
- **fresh**: applied params match current run context and data is current.

Use clear prompts/skeletons/empty cards (`AwaitRun`, `No data available yet`) instead of blank panels.

### Data fetching

TanStack Query hooks in `lib/hooks.ts`:

- key queries by relevant parameters (race id, applied params, selected drivers, fantasy picks);
- enable prediction/H2H/fantasy queries only when prerequisites exist;
- expose loading/error/data states to pages/components;
- can be configured with retries/stale times appropriate for live vs static data.

### Visualization principles

- Every chart handles empty arrays and null values.
- Donuts/bars include legends or labels when color meaning matters.
- Tooltips should remain readable in dark/light/custom themes.
- Team colors are used when available; fallback palettes provide distinct hues (important for Team Win-Share donut).
- Chart containers must have explicit/responsive height to avoid Recharts sizing warnings/invisible renders.

### Accessibility and settings

Settings are applied globally via CSS variables and document attributes:

- theme mode (light/dark/system),
- accent colors,
- font scale and corner radius,
- density and compact tables,
- high contrast / reduced motion / dyslexia-friendly font / underline links (where implemented),
- data-saver/imagery toggles (where implemented),
- custom project colors (core/status/chart/tooltip tokens).

---

## Prediction model and simulation inputs

> The model is an internal Monte Carlo-style estimator using configurable priors and race/session modifiers. It is designed for interactive exploration, not authoritative forecasting.

### Typical input categories

- **Race selection:** round/race id, sprint/non-sprint context, circuit traits.
- **Session selection:** practice, qualifying, sprint qualifying, sprint, race.
- **Simulation controls:** number of simulations (`sims`), randomness/chaos factor.
- **Performance priors:** team pace, driver skill, wet skill, reliability, current points/form proxies (from seed/live context).
- **Grid influence:** auto or manual starting positions and grid weighting.
- **Environment modifiers:** weather mode (auto/dry/mixed/wet), safety-car tendency, overtaking difficulty/track characteristics.
- **Strategy/variance modifiers:** strategy aggression, degradation/SC sensitivity (as exposed).

### Typical output categories

- Win, podium, top-10, points-finish probabilities.
- Expected finishing position / ranking distributions.
- DNF probability / attrition effects.
- Qualifying progression odds (Q1/Q2/Q3 style outputs where applicable).
- Strategy distribution/scenario likelihoods.
- Team-aggregate metrics (e.g., win share).
- Confidence indicators based on simulation/sample spread.

### Calibration / honesty

- Raw probabilities are generally simulation-derived frequencies or model transforms; they are **not** externally calibrated betting odds.
- Circuit traits and ratings in seed data are priors/assumptions.
- Live data improves realism for current-season context but does not guarantee correctness.
- Use results comparatively (A vs B under same assumptions) rather than as certainties.

---

## Data sources, caching, and offline behavior

### Modes

- **Live-preferred mode (default/configurable):** attempt upstream provider fetches; cache responses; fall back to seed snapshot on failure.
- **Seed/offline mode:** use `backend/app/data/seed.json` only (useful for local dev/tests and deterministic demos).

### Local seed mode example

```bash
cd backend
DATA_MODE=seed python3 -m uvicorn main:app --reload --port 8000
```

(Exact env var names may vary; check `backend/app/config.py` and `.env.example`.)

### Fallback behavior

The frontend and backend are designed to degrade gracefully:

- missing round history -> show totals/ladder/contribution charts instead of cumulative history;
- missing qualifying/live grid -> allow simulated or manual workflows;
- incomplete fantasy picks -> evaluate endpoint returns pool/analysis and validation issues;
- missing optional chart fields -> render “No data available yet” placeholders.

---

## Driver roster (2026 grid used by this project)

The project seed/fixtures are aligned to the following **22-driver** 2026 lineup (code — driver — team):

| Code | Driver | Team |
|---|---|---|
| ANT | Kimi Antonelli | Mercedes |
| RUS | George Russell | Mercedes |
| HAM | Lewis Hamilton | Ferrari |
| LEC | Charles Leclerc | Ferrari |
| NOR | Lando Norris | McLaren |
| PIA | Oscar Piastri | McLaren |
| VER | Max Verstappen | Red Bull Racing |
| HAD | Isack Hadjar | Red Bull Racing |
| LAW | Liam Lawson | Racing Bulls |
| LIN | Arvid Lindblad | Racing Bulls |
| GAS | Pierre Gasly | Alpine |
| COL | Franco Colapinto | Alpine |
| ALB | Alexander Albon | Williams |
| SAI | Carlos Sainz | Williams |
| BEA | Oliver Bearman | Haas |
| CAM | Rafael Câmara | Haas |
| HUL | Nico Hulkenberg | Audi |
| BOR | Gabriel Bortoleto | Audi |
| ALO | Fernando Alonso | Aston Martin |
| STR | Lance Stroll | Aston Martin |
| PER | Sergio Perez | Cadillac |
| BOT | Valtteri Bottas | Cadillac |

If future roster changes are needed, update all layers consistently:

1. `backend/app/data/seed.json` (canonical offline roster/prior fields)
2. provider normalization/mappings (if live sources use different IDs/codes)
3. frontend fixtures (`frontend/src/test/fixtures/*`)
4. MSW handlers/tests (`frontend/src/test/server.ts`, smoke tests)
5. backend tests (`backend/tests/*`) and any hardcoded counts/driver assumptions
6. UI assumptions that render 22 rows/slots

---

## Appearance and color customization

### Theme tokens

Global colors and layout tokens are primarily driven by CSS variables in `frontend/src/index.css`, applied/overridden at runtime by `frontend/src/lib/appearance.ts` from persisted settings.

Key token groups include:

- **Core UI:** background/ink, surfaces, borders, text, muted text, accent/accent highlight.
- **Status colors:** success, warning, danger, info.
- **Chart palette:** chart color tokens (used by chart primitives/default series/fills where wired).
- **Tooltip colors:** tooltip background/text (default tuned to sky-blue background + red text per UI requirement; user-configurable).
- **Layout/accessibility:** font scale, radius, density/table compactness, and accessibility-related document flags.

### Settings UI

The Settings page exposes appearance controls and a project-color editor. Color pickers write to `settings.colors` and `applyAppearance` maps supported keys to CSS variables.

When adding a new customizable color:

1. Add key to `Settings["colors"]` in `frontend/src/lib/store.ts`.
2. Map key -> CSS variable in `frontend/src/lib/appearance.ts`.
3. Define default variable in `frontend/src/index.css` (dark/light as needed).
4. Add picker/label/default in `frontend/src/pages/Settings.tsx`.
5. Use the variable in components/charts (prefer tokens over hardcoded literals).

---

## Local development

### Prerequisites

- **Python:** use the version indicated by `.python-version` (commonly 3.12 for this project layout).
- **Node.js:** use Node 22 for frontend tests/CI parity when possible (Node 24 can break jsdom+fetch/AbortController realm expectations in tests).
- **npm:** comes with Node.

### 1) Backend setup

```bash
# from repo root
python3.12 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-dev.txt
```

Run API (terminal 1):

```bash
source .venv/bin/activate
cd backend
DATA_MODE=seed python -m uvicorn main:app --reload --port 8000
```

Useful local URLs:

- API root/docs (if enabled): `http://localhost:8000/docs`
- Health endpoint (if implemented): `http://localhost:8000/health`
- Versioned API: `http://localhost:8000/api/v1/...`

### 2) Frontend setup

```bash
# terminal 2
cd frontend
npm install
npm run dev
```

Vite dev server (default): `http://localhost:5173`  
Dev config should proxy `/api` to the backend on port 8000 (see `frontend/vite.config.ts`).

### 3) Typical dev workflow

1. Start backend (`:8000`) and frontend (`:5173`).
2. Open Dashboard, select a race, adjust session/params.
3. Click **Run Prediction** (no auto-run on control changes).
4. Verify charts/tables render for race, qualifying, and sprint-capable rounds.
5. Check Settings changes (theme/colors) apply immediately.
6. Run tests/typecheck/build before commits.

---

## Testing and quality checks

### Backend tests (pytest)

```bash
# repo root, with venv active
cd backend
python -m pytest -q
```

Or without activating:

```bash
cd backend
../.venv/bin/python -m pytest -q
```

### Frontend typecheck

```bash
cd frontend
npx tsc --noEmit
```

### Frontend unit/smoke tests (Vitest)

```bash
cd frontend
npm test
```

> Prefer Node 22 for `npm test` in this project setup. Build/dev may still work on newer Node versions.

### Frontend production build

```bash
cd frontend
npm run build
```

### Pre-merge / pre-push checklist

- [ ] Backend tests pass.
- [ ] Frontend typecheck passes.
- [ ] Frontend tests pass (Node 22 recommended).
- [ ] Frontend build succeeds.
- [ ] Seed data, fixtures, and MSW handlers are consistent with schema/roster changes.
- [ ] No secrets committed (`.env`, tokens, credentials).
- [ ] Vercel config still routes API + SPA correctly.
- [ ] README/docs updated for behavior changes.

---

## Environment variables

See `.env.example` for the authoritative list. Common categories:

### Backend/runtime

- `DATA_MODE` / source-priority related settings: choose live-first vs seed-only behavior (names depend on config implementation).
- `CACHE_TTL` / `LIVE_INTERVAL`: cache and refresh tuning.
- `MAX_SIMS` (if exposed): upper bound for simulation count.
- `SETTINGS_ADMIN_TOKEN`: enables protected backend settings/admin operations (if implemented).
- `CORS_ORIGINS`: comma-separated origins for cross-origin API calls. Leave blank for same-origin Vercel/frontend-backend setup; set explicitly only when needed.

### Frontend/build-time

- `VITE_*` variables (if any): client-visible configuration. Do not place secrets in `VITE_` variables.
- API base/path overrides: prefer same-origin `/api/v1` defaults unless deploying frontend/backend separately.

### Security notes

- Never commit real tokens.
- Admin tokens should be configured in Vercel project environment settings, not in source.
- Treat all user-editable client settings as untrusted; backend must revalidate prediction inputs.

---

## API reference summary

Base path (typical): `/api/v1`

> Exact schemas live in `backend/app/routes_models.py` and route handlers. Use `/docs` (FastAPI Swagger UI) locally when available.

### Common GET endpoints

| Endpoint | Purpose |
|---|---|
| `/api/v1/meta` | App/model metadata (e.g., limits such as max sims, feature flags) |
| `/api/v1/races` | Race calendar/list for season |
| `/api/v1/races/next` | Next upcoming race (if implemented) |
| `/api/v1/races/{id}/weather` | Weather context/forecast or fallback |
| `/api/v1/races/{id}/grid` | Grid/starting-order info (live/derived/fallback) |
| `/api/v1/drivers` | Driver roster/details |
| `/api/v1/standings` | Driver/constructor standings |
| `/api/v1/recent` | Recent results/events |
| `/api/v1/search` | Search helper (drivers/races/etc.) |
| `/api/v1/fantasy/pool` | Fantasy driver pool/pricing/metadata |
| `/api/v1/config` | Public/runtime config for frontend |

### Common POST endpoints

| Endpoint | Purpose | Notes |
|---|---|---|
| `/api/v1/predictions` | Run Monte Carlo prediction | Validates race/session/sub/sims/grid; rejects invalid sprint session on non-sprint weekends |
| `/api/v1/h2h` | Head-to-head comparison | Returns comparable metrics for two drivers; may include compatibility aliases |
| `/api/v1/fantasy/evaluate` | Evaluate fantasy picks/team | Can return pool/optimal/analysis even with incomplete picks |

### Admin endpoints (token-gated, if enabled)

| Endpoint | Purpose |
|---|---|
| `/api/v1/admin/verify` | Verify admin token/header |
| `/api/v1/admin/config` | Update runtime backend config (subject to implementation and persistence model) |

### Caching behavior

GET responses may set cache headers (e.g., `s-maxage`) so Vercel’s CDN can cache safe, repeatable reads. POST prediction/evaluation requests are compute operations and should not be CDN-cached as user-specific mutations in the same way.

---

## Deployment to Vercel

### Standard deployment

1. Push repository to GitHub.
2. In Vercel, **Import Project** from the repo.
3. Use repository root as the project root (unless intentionally restructuring).
4. Confirm build settings align with `vercel.json`:
   - frontend install/build in `frontend/`
   - static output directory as configured
   - Python API function from `api/index.py`
   - rewrites for `/api/*` and SPA routes
5. Add environment variables in Vercel Project Settings (only what you need; start from `.env.example`).
6. Deploy.
7. Validate:
   - homepage loads SPA,
   - `/api/v1/meta` responds,
   - dashboard can run a prediction,
   - standings/H2H/fantasy endpoints respond.

### Production checklist

- [ ] `SETTINGS_ADMIN_TOKEN` set only if admin config features are needed.
- [ ] CORS restricted appropriately (same-origin preferred).
- [ ] No debug logging of secrets.
- [ ] Frontend build passes in CI/local.
- [ ] Backend tests pass.
- [ ] Seed snapshot is valid JSON and roster-complete.
- [ ] Large asset/chunk warnings reviewed (Recharts chunk may be sizable).

### Vercel/serverless caveats

- In-memory caches reset on cold starts/instance recycling.
- Long-running background jobs are not part of this architecture.
- Keep simulation counts bounded (`MAX_SIMS`) to control CPU/time.
- Upstream provider failures should degrade to seed/fallback responses.

---

## Troubleshooting

### `Session 'sprint' is only available on sprint weekends`

Cause: selected race is not a sprint weekend, but session/sub state still requested sprint.

Fixes:
- Use frontend sanitization (Control/store) when changing races.
- Ensure backend calendar `sprint` flags are correct in seed/live mapping.
- Run prediction only with sanitized draft values.

### Prediction never shows results

Cause: run-gated state means draft changes do not fetch results until applied.

Checks:
- Click **Run Prediction**.
- Confirm `applied` params are set (UI should move from `AwaitRun` state).
- Inspect network request to `POST /api/v1/predictions`.
- Check backend logs/response for validation errors.

### Chart is blank/invisible

Common causes:
- no data / all-zero/filtered dataset (expected -> empty state),
- container height is zero (layout/CSS regression),
- Recharts `ResponsiveContainer` parent has no dimensions,
- payload field names changed.

Checks:
- verify component renders empty fallback text,
- inspect computed height in DevTools,
- confirm API payload contains expected arrays/keys.

### Donut tooltip unreadable

Tooltip theme uses CSS variables (`--tt-bg`, `--tt-fg`). Defaults are sky-blue background and red text; users can override in Settings. If custom colors produce poor contrast, reset custom colors in Settings.

### Frontend tests fail on Node 24 (`AbortSignal` realm issue)

Use Node 22 for Vitest/jsdom environment parity:

```bash
# example with nvm
nvm install 22
nvm use 22
cd frontend && npm test
```

### Backend `ModuleNotFoundError` / wrong Python environment

Activate the repo virtualenv or use its interpreter explicitly:

```bash
source .venv/bin/activate
cd backend && python -m pytest -q
```

### CORS errors in local/prod

- Local dev should proxy `/api` through Vite (same-origin in browser).
- Production should be same-origin via Vercel rewrites.
- Set `CORS_ORIGINS` only for legitimate separate frontend origins; avoid `"*"` unless intentionally public.

---

## Known limitations and honest notes

- **Model priors are assumptions:** team/driver ratings and circuit traits are not ground truth.
- **No formal backtesting claim:** accuracy metrics are not presented as validated historical performance.
- **Offline snapshot ages quickly:** seed standings/calendar/results may lag real season progress.
- **Live providers can fail/rate-limit:** fallback logic is best-effort; fields may be missing.
- **Serverless state is ephemeral:** in-memory cache/admin runtime changes may reset.
- **Large chart bundles:** Recharts can create sizable chunks; code-splitting/manual chunks may be added if needed.
- **Accessibility/visual customization:** project color tuning is powerful but user-selected combinations can reduce contrast; reset-to-defaults should remain easy.
- **Licensing/assets:** team/F1 marks and imagery may require replacement/licensing before public/commercial distribution.

---

## Contributing / maintenance workflow

### Branching and commits

- Work on a feature branch (e.g., `feat/...`).
- Keep commits focused and messages descriptive.
- Do not commit generated artifacts, local envs, or secrets.
- Run tests/typecheck/build before pushing.

### Suggested change process

1. Update backend schema/service/engine (if behavior/data changes).
2. Update frontend API types/hooks/components.
3. Update MSW handlers and fixtures.
4. Update/extend tests.
5. Update README/docs.
6. Verify Vercel deployment behavior.

### Safe roster/data updates

When changing drivers/teams/calendar:

- maintain stable IDs/codes used across backend and frontend;
- preserve compatibility aliases only when needed, then migrate consumers;
- update every fixture and test that hardcodes counts/names/codes;
- run full backend/frontend checks.

---

## Legal / trademarks

This is an **unofficial fan-made project**. It is **not affiliated with, endorsed by, or connected to** Formula 1, Formula One Management, the FIA, or any Formula 1 team.

Formula 1, F1, team names, car names, logos, and related marks are trademarks of their respective owners. Any included images, logos, or likeness references in local assets may be placeholders or sourced for development/demo purposes; review, replace, or obtain appropriate rights before any public release.

---

## Appendix: quick command reference

```bash
# Backend (repo root)
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
cd backend && DATA_MODE=seed python -m uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
npx tsc --noEmit
npm test
npm run build

# Backend tests
cd backend
python -m pytest -q
```

---

## Appendix: UI behavior checklist (manual QA)

- [ ] Dashboard loads without prediction until Run Prediction.
- [ ] Race/session/sub sanitize correctly on race change.
- [ ] Sprint/sprint qualifying unavailable or corrected for non-sprint rounds.
- [ ] Run Prediction produces fresh results and stale state appears after draft edits.
- [ ] Team Win-Share donut shows distinct colors and a visible key/legend.
- [ ] Donut chart hover tooltip uses readable sky-blue/red style (or custom tooltip colors).
- [ ] Standings tabs render charts/tables with fallbacks when history missing.
- [ ] H2H renders breakdown + comparative plots for selected drivers.
- [ ] Fantasy pool shows driver names/details and evaluation cards render.
- [ ] Settings color pickers update UI/chart/status/tooltip tokens.
- [ ] Mobile/narrow layout keeps charts scroll-safe/readable.
