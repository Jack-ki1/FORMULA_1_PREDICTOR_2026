# @f1-predictor/api-types

TypeScript types generated directly from `apps/api`'s OpenAPI schema via
[openapi-typescript](https://openapi-ts.dev/). This is the "contract"
between `apps/web` and `apps/api` described in PLAN.md §6 — regenerate
it whenever a router's request/response shape changes, and TypeScript
will flag every frontend call site that's now out of sync, instead of
that drift being discovered at runtime.

## Regenerate

```bash
# with apps/api running locally on :8000
cd apps/api && uvicorn main:app --port 8000 &
cd packages/api-types && npm run generate

# or against a deployed API
API_URL=https://your-app.vercel.app/api npm run generate:remote
```

## Current status

`apps/web/lib/api-client.ts` currently hand-writes its response
interfaces rather than importing from here — they were written directly
against the same routers this package's types are generated from, so
they match today, but nothing enforces that going forward. Wiring
`apps/web` to import `paths`/`components` from this package instead
(e.g. via `openapi-fetch`, which types every call against the `paths`
type below) removes that drift risk entirely. Left as the natural next
step rather than done speculatively in the initial build — see PLAN.md
§6 and the root README's "What's next" section.
