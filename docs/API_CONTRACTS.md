# API Contracts — /api/v1 (Versioned) + Legacy

Legacy Jinja endpoints remain for dual-run (see MIGRATION.md Phase 3):

```
Legacy (Jinja-era, still active):
  GET  /dashboard/api/races
  GET  /dashboard/api/race-result/<race_id>
  POST /dashboard/api/predict-session
  POST /dashboard/api/ai-chat
  GET  /standings/api/driver-standings
  GET  /standings/api/constructor-standings
  GET  /h2h/api/drivers
  POST /h2h/api/compare
  GET  /constructors/api/teams
  GET  /constructors/api/power-rankings
  GET  /analytics/api/accuracy
  GET  /analytics/api/feature-weights
  POST /analytics/api/feature-weights
  GET  /analytics/api/targets
  POST /reports/api/export
```

Versioned contract (new React frontend, OpenAPI at /api/v1/openapi.json):

```
V1 (authoritative, typed):
  GET  /api/v1/races
  GET  /api/v1/races/<race_id>/result   (also /api/v1/race-result/<id> for compat)
  POST /api/v1/predictions              (alias /api/v1/predict , /api/v1/predict-session)
  POST /api/v1/ai/chat
  GET  /api/v1/standings/drivers
  GET  /api/v1/standings/constructors
  GET  /api/v1/h2h/drivers
  POST /api/v1/h2h/compare
  GET  /api/v1/constructors/teams
  GET  /api/v1/constructors/power-rankings
  GET  /api/v1/analytics/accuracy
  GET  /api/v1/analytics/feature-weights
  POST /api/v1/analytics/feature-weights
  GET  /api/v1/analytics/targets
  POST /api/v1/reports/export
  GET  /api/v1/health
  GET  /api/v1/openapi.json
```

## Error Contract

All v1 endpoints return `{"error":{"code":string,"message":string,"details":object,"request_id":string}}` with `X-Request-ID` header (echoed). Legacy endpoints return `{"error": "..."}` — kept for backward compat.

## Request Validation

Pydantic schemas (`backend/app/api/schemas/prediction.py`):
- race_id: str required
- session_type: race|qualifying|practice
- weather: dry|mixed|wet
- simulation_count: 100–100000 (clamped in engine)
- feature_weights: {chaos_level:0-100,…}
- AI keys never persisted server-side; weight 0–1, temperature 0–2.

## Headers

- X-Request-ID: client may send; server echoes; always present.
- X-Response-Time / X-Prediction-Latency: latency observability.
- Cache-Control: `public, max-age=300` for races, `max-age=60` for standings.
- Security headers from config.settings.SECURITY_HEADERS.

## Cache Keys (Redis)

```
races:2026
standings:drivers:2026
standings:constructors:2026
h2h:{A}:{B}
prediction:{race}:{session}:{hash}  (implicit via service)
```

## Authentication

JWT bearer (`Authorization: Bearer <token>`) via security/auth.py (`require_auth`, `require_role`). Active v1 endpoints currently allow anonymous but validate token if present — consistent with Phase 1 decision to reconcile auth after cutover. See SECURITY_ENHANCEMENTS.md.
