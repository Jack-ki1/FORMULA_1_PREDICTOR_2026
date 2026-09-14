# Architecture — Decoupled Full-Stack (React + FastAPI + Intelligence Engine)

```
Browser (5173 Vite React 18, TanStack Query)
  │ fetch('/api/v1/*') proxied in dev, Vercel rewrite in prod
  ▼
FastAPI 5000 (pure JSON, CORS allowlist via FRONTEND_ORIGIN)
  ├─ Middleware: X-Request-ID, X-Response-Time, Redis rate limit (per-route), security headers
  ├─ /api/v1/*  (versioned)
  │   ├─ races, standings, h2h, constructors, analytics, reports, ai
  │   ├─ predictions (+ /scenario, /simulate, /jobs)
  │   ├─ live/{session} (+ /stream SSE)
  │   └─ system/{data-sources, models, health}
  ├─ /health, /, /metrics (Prometheus)
  └─ Services (thin, validated) → Prediction Orchestrator
        └─ ML zoo + Ensemble (OOF) + Calibration (isotonic/Platt) + Monte Carlo
  Data Providers (abstracted):
    F1DataProvider → JolpicaProvider (results/standings) / OpenF1Provider (live telemetry) / FastF1Provider (historical) / FallbackProvider (seed+cache)
    + provenance {source, provider, retrieved_at, response_hash, cache_status}
  Cache: Redis required in prod (REDIS_REQUIRED=true), DictCache fallback only if ENABLE_IN_MEMORY_FALLBACK=true (dev)
  DB: SQLAlchemy → SQLite dev / Postgres prod — predictions/snapshots/provenance persisted; races/drivers/circuits seeded from python constants but DB is truth for dynamic data
  Workers: sync for <10k sims; async jobs queue for large MC/training (POST /predictions/jobs → GET /jobs/:id)
```

Frontend: `src/app` (router, providers) + `src/features/*` (predictions, scenario-lab, live-race, standings, h2h, analytics, reports, ai) + `src/api/*` typed client + `src/lib/media.ts` typed assets.

Invariants preserved: prediction parity (engine deterministic via seed), DB failure never breaks prediction, manual grid precedence, 17 media assets via typed registry.

Deploy: `Vercel (frontend Vite) + Render/Railway/Fly (FastAPI) + managed Redis + Postgres` — or `docker-compose.yml` (backend:5000 + redis:6379, frontend via npm run dev).
