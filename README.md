# F1 Predictor 2026 — Race Intelligence, Reimagined

One Vercel project, no outside services: a React/Vite frontend and a FastAPI backend that deploy together.

| Layer | Stack |
|---|---|
| Frontend (`frontend/`) | React 18 · TypeScript · Vite · Tailwind · TanStack Query · Zustand · Framer Motion · Lucide |
| Backend (`backend/`, served by `api/index.py`) | FastAPI · NumPy Monte Carlo engine · httpx · Pydantic |
| Data | Jolpica (live results/standings/calendar) and Open-Meteo (forecast), with a bundled offline snapshot as fallback |

## Deploy to Vercel
1. Push this folder to GitHub and **Import** it in Vercel (Root Directory = repo root).
2. `vercel.json` already sets the build command, output directory, Python function and rewrites. Click Deploy.
3. Optional environment variables: see `.env.example`. Set `SETTINGS_ADMIN_TOKEN` to enable saving in Settings → Backend Configuration. The API is same-origin with the frontend, so leave `CORS_ORIGINS` blank; add origins only if a separate host must call it (`"*"` allows any website).
4. Check `/health` and `/api/docs` on the deployed URL.

## Run locally

The backend runs in a virtual environment at the repo root (`.venv/`, git-ignored). Create it once — use the
Python version from `.python-version` — then activate it before any `pip`/`python`/`pytest` command.
```bash
# one-time setup (repo root)
python3.12 -m venv .venv
source .venv/bin/activate                      # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-dev.txt

# ── terminal 1: the API on :8000 (leave it running) ──
source .venv/bin/activate
cd backend && DATA_MODE=seed python -m uvicorn main:app --reload --port 8000   # drop DATA_MODE=seed for live data

# ── terminal 2: the web app ──
cd frontend && npm install && npm run dev      # http://localhost:5173 (proxies /api to :8000)
npm test                                       # renders every page against the API on :8000

# backend tests (terminal 3, venv activated)
cd backend && python -m pytest -q              # or: npm run test:api from the repo root
deactivate                                     # leave the venv
```
> Without activating, use `.venv/bin/python -m pytest -q` from `backend/` (or `npm run test:api`). A bare `pip install`
> targets your system Python — avoid it, or you are back to where you started.
>
> **Node version matters for `npm test`.** CI and Vercel run Node 22 (`engines` requires `^22`). On **Node 24**, jsdom's
> `AbortController` and Node's native `fetch` come from different realms, so `new AbortController().signal` is rejected
> with `Expected signal to be an instance of AbortSignal` and every data-driven page renders empty: all 6 tests fail.
> `npm run build` and `npm run dev` are unaffected (the browser's controller and `fetch` always share a realm). Use Node 22
> to run the frontend tests.

## What's inside
- **Dashboard control center:** all 23 rounds, Auto/Dry/Mixed/Wet weather, Practice / Qualifying / Sprint / Grand Prix sessions (labels adapt to each weekend's race day), weekend status with live UTC clock, session schedule and next-session countdown, selected-event facts, and a starting-grid editor (Auto-fetched or Manual P1–P22 with unique picks, Clear, Auto-fill by form, Reverse). Race, session and weather apply instantly; grid and engine changes apply on **Run Prediction**.
- **Visuals:** win/pole/podium/fastest-lap cards, finishing-position heatmap, constructor battle, grid→finish chart, Q1/Q2/Q3 advancement, practice pace distribution, race-day profile, strategy odds, confidence ring, CSV/JSON/PDF export.
- **Pages:** Dashboard, Predictions, Standings, Head2Head, Fantasy League, Guide, Settings.
- **Settings (11 sections):** Appearance (light/dark/system, accent, font size, roundness, density, custom colors, share link), Accessibility, Prediction Engine defaults, Backend Configuration (admin token), Reference Parameters, Dashboard Layout, Notifications, Profile, Advanced, Keyboard Shortcuts, Data & Privacy. Engine settings are sent with every prediction.

## API (`/api/v1`)
`GET /meta, /races, /races/next, /races/{id}/weather, /races/{id}/grid, /standings, /drivers, /recent, /search, /h2h, /fantasy/pool, /config` · `POST /predictions` · `GET /admin/verify`, `PUT /admin/config` (header `X-Admin-Token`). GET responses send `s-maxage` so Vercel's CDN absorbs traffic.

## Honest notes
- Ratings (team pace, driver skill, wet skill) and circuit traits are model priors in `backend/app/data/seed.json`, not facts. The model has not been backtested.
- Offline snapshot: calendar dates and session times are estimates; standings cover the 13 drivers with confirmed points after round 17. Live Jolpica data replaces all of this automatically; if it is unreachable the app falls back to the snapshot.
- Backend Configuration changes live in server memory and reset when the serverless instance recycles; use env vars for permanent changes.
- Images (hero car, Canada circuit/track photo, Verstappen/Norris avatars, logos) were cropped from the supplied mock-up. Other circuits/drivers show placeholders; drop files in `frontend/public/img/{circuits,tracks,drivers}/`. The F1 and team logos are trademarks: replace or license them before a public launch.
- Unofficial fan project, not affiliated with Formula 1, the FIA or any team.
