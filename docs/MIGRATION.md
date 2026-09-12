# Migration — Strangler Fig Plan (25 Steps)

Authoritative order from transformation_improvements.md:

```
01 Freeze existing production behavior (legacy Jinja remains at /dashboard/* etc.)
02 Create golden prediction fixtures (scripts/generate_golden_fixtures.py → tests/fixtures/golden/*.json)
03 Extract PredictionService (backend/app/services/prediction_service.py wraps generate_prediction)
04 Define API schemas/contracts (backend/app/api/schemas + /api/v1/openapi.json)
05 Standardize authentication (JWT bearer, require_auth reconciled; v1 allows anon but validates if present)
06 Add API integration tests (tests/test_api_v1.py — v1 + legacy dual-run)
07 Create frontend/ (Vite + React + TS + Tailwind + Router + TanStack Query + Zod + Chart.js)
08 Rebuild global shell/navigation (AppShell, TopNavigation, ThemeToggle — legacy.css preserved)
09 Recreate dashboard UI (RaceSelector, SessionSelector, WeatherSelector, PredictionControls)
10 Connect race/driver APIs (useRaces, useDrivers via /api/v1)
11 Connect prediction API (usePrediction via /api/v1/predictions; manual grid precedence preserved)
12 Rebuild prediction results/charts (PredictionResults, PredictionCharts — Bar/Doughnut)
13 Rebuild manual grid (GridEditor — select P1-22 per code, mirrors grid_editor.js)
14 Rebuild AI sidebar/chat (AISidebar — mode/model/weight/temperature + chat tab; key not persisted)
15 Rebuild standings (StandingsPage — driver + constructor via /api/v1/standings/*)
16 Rebuild H2H (H2HPage — compare via /api/v1/h2h/compare)
17 Rebuild constructors (ConstructorsPage — teams + power rankings)
18 Rebuild analytics/settings (AnalyticsPage — accuracy, weights GET/POST, targets)
19 Rebuild exports (exportReport via /api/v1/reports/export — pdf/csv/json; share-card via generator)
20 Run visual regression (compare base.html vs React AppShell — legacy.css pixel reference)
21 Run prediction parity tests (tests/test_prediction_parity.py — deterministic seeded runs)
22 Run old/new dual-stack (both /dashboard/api/* and /api/v1/* serve same engine)
23 Production cutover (frontend dist via nginx proxy /api → Flask; backend health at /health + /api/v1/health)
24 Retire Jinja frontend (keep as fallback until parity signed off)
25 Optimize backend independently (PostgreSQL, Redis tuning, Celery worker for Monte Carlo)
```

## Cutover Checklist

- [ ] `docker-compose up --build` — frontend 5173/80, backend 5000, redis 6379
- [ ] `pytest tests/test_api_v1.py tests/test_prediction_parity.py -v`
- [ ] Manual: compare Jinja dashboard vs React dashboard with same race/session/weather/grid
- [ ] Verify X-Request-ID, error contract, latency headers, cache keys
