# API Architecture

- Base: FastAPI, versioned `/api/v1`, OpenAPI ` /api/v1/openapi.json` + Swagger `/docs` is source of truth.
- Client: `frontend/src/api/client.ts` typed `api.get/post`, `X-Request-ID`, `Bearer f1-jwt`, error normalization, timeout/retry; system expects generated TS types from OpenAPI (parity checked in CI).
- Endpoints (authoritative, see `backend/app/api/routes/*`):

```
GET  /api/v1/races
GET  /api/v1/races/:id / :id/result
POST /api/v1/predictions (aliases /predict, /predict-session)
POST /api/v1/predictions/scenario
POST /api/v1/predictions/simulate
POST /api/v1/predictions/jobs  → GET /api/v1/jobs/:id
GET  /api/v1/live/:session
GET  /api/v1/live/:session/stream (SSE)
GET  /api/v1/system/data-sources
GET  /api/v1/system/models
GET  /api/v1/system/health
GET  /api/v1/standings/drivers|constructors
GET  /api/v1/h2h/drivers  POST /api/v1/h2h/compare
GET  /api/v1/constructors/teams|power-rankings
GET  /api/v1/analytics/accuracy|feature-weights|targets
POST /api/v1/ai/chat
POST /api/v1/reports/export
GET  /api/v1/health, /health, /metrics, / (API info JSON)
```

- Security: `FRONTEND_ORIGIN` allowlist (not `*` with credentials), Redis rate limit per-route (predictions 60/h, ai 30/h, live 120/h, exports 20/h), JWT deps via `security/auth.py` (anonymous reads, auth where needed), request body limits, never log secrets.
- Resilience: provider fallback chain recorded in provenance; `data-sources` exposes health.

