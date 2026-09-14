# Data Architecture

- Providers abstracted via `F1DataProvider` (see `backend/app/data/providers/base.py`).
- Concrete: `JolpicaProvider` (results/standings/quali, live→fallback), `OpenF1Provider` (live telemetry, pit, race control), `FastF1Provider` (historical telemetry), `FallbackProvider` (local seed).
- Federated via `ProviderRegistry` (`backend/app/data/providers/registry.py`): priority live→OpenF1, historical→FastF1/OpenF1, official→Jolpica, static→fallback. Never randomly switches; provenance recorded.
- Provenance: every dataset carries `DataProvenance {source, provider, endpoint, retrieved_at, response_hash, schema_version, cache_status, latency_ms}`; exposed via `GET /api/v1/system/data-sources` and per-prediction `snapshot.provenance`.
- Cache: Redis (production required if `REDIS_REQUIRED=true`), file cache `cache/api_responses` as L2. Keys hash race+session+snapshot+model+feature+weather+grid+config; invalidated on data/model version change, not naive TTL 3600.
- DB: `backend/app/database/models.py` (seasons, races, sessions, circuits, drivers, constructors, results, predictions, snapshots, provenance). Seed from `calendar_2026.py` / `team_driver_lineup_2026.py` (now seed, not truth).
- Quality: `data_quality {score, grid, weather}` per prediction; `Data readiness 92%` breakdown shown in UI.
