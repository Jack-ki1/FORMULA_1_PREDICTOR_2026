# Architecture — Decoupled Full-Stack (React + Flask API + Engine)

Target matches transformation_improvements.md final architecture:

```
Browser
  React + TypeScript + Vite + Tailwind + React Router + TanStack Query
    ↓ HTTPS/JSON (X-Request-ID, JWT)
Flask REST API (/api/v1 + legacy /dashboard/api/* for dual-run)
  ├─ API layer: validation, rate limiting, request_id, security headers, observability
  ├─ Service layer: backend/app/services/* (thin orchestration, logging, cache keys)
  └─ Domain engine: engine/* (predictor, monte_carlo, grid_model, probability_model preserved)
       ├─ Redis (race/standings/H2H/prediction cache)
       └─ SQLAlchemy → SQLite (dev) / PostgreSQL (prod)
  External F1 APIs: Jolpica, OpenF1, FastF1
```

## Frontend

- `frontend/src/app` App/Router/Providers (QueryClient)
- `frontend/src/pages/*` Home, Dashboard, Standings, H2H, Constructors, Analytics, Reports
- `frontend/src/components/*` layout, navigation, dashboard, prediction, charts, shared
- `frontend/src/features/*` manual-grid, ai-assistant, theme, exports
- `frontend/src/api/*` typed client (fetch + Zod-ready), query hooks
- `frontend/src/styles` variables.css (tokens), legacy.css (preserved verbatim from dashboard/static/css/styles.css), globals.css

State split per Phase 7/9:
- Server state (TanStack Query): races, drivers, standings, prediction, H2H, constructors, analytics
- Client state (small store): draft race/weather/simCount, session/subSession, manualGrid, AI mode/model/weight/temperature (mirrors localStorage, API key not persisted)

## Backend

- `dashboard/app.py` factory: legacy blueprints + v1 blueprints + middleware (request_id, security headers, timing, rate-limit stub, CORS)
- `backend/app/services/*` orchestration (no algorithm changes)
- `backend/app/api/schemas` Pydantic contracts
- `backend/app/api/routes/*` v1 endpoints (+ OpenAPI at /api/v1/openapi.json)
- `backend/app/security/middleware` request-id, rate-limit, headers
- `engine/*` retained 1:1 (MonteCarlo, GridModel, probability_model, calibration, elo, etc.)
- `database` SQLAlchemy, `cache/redis` Redis + DictCache fallback

## Deployment

`docker-compose.yml` runs backend:5000, frontend:80 (nginx proxy /api → backend), redis:6379. Frontend can scale independently; prediction workers could later move to Celery/RQ behind Flask API.

## Invariants

- Same inputs → same engine → same outputs (prediction parity harness in PREDICTION_PARITY.md)
- DB failure never breaks prediction delivery (predictor catches persistence errors)
- Manual grid takes precedence; GridModel → _strength_based_grid fallback with seeded noise noted for parity
