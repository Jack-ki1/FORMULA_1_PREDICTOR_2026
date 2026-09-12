# Transformation & Improvements Plan

_Audited by walking the full tree (no sampling), running `npm install`, `npm run build`,
`npm run lint`, `npm run test`, and `npm audit` against a clean clone, and reading
every non-vendored source file. Repo: `mevest-africa-vault-a4a74639`, branch `main`,
HEAD `837b262`. All line/file references are exact as of that commit._

## Verdict

Not deployable as a real financial product today, despite the repo's own
`TRANSFORMATION_IMPLEMENTATION.md` declaring "PRODUCTION-READY." It's a reasonably
polished UI shell wired to a real, correctly-configured Supabase backend for auth and
CRUD, sitting on top of a market-data layer that is 100% dependent on scraping an
undocumented Yahoo Finance endpoint with zero fallback, and a live-price system that
silently stops working for any ticker outside a ~20-symbol hardcoded list. The
biggest risk isn't a single bug — it's that the project's own documentation actively
misrepresents what's implemented (invented UI code, invented "multi-provider
fallback," invented "code-splitting"), which means nobody can safely plan future work
off that doc. Ship nothing until the admin bypass default is removed from the bundle,
`portfolio-snapshot` is authenticated, and the pricing engine is fixed or the "live
price" claim is removed from the UI.

## Critical Issues (fix before anything else)

- [ ] **Hardcoded admin bypass with default credentials shipped in the client bundle
  and published in plaintext in `README.md` and `TRANSFORMATION_IMPLEMENTATION.md`**
  — `frontend/src/context/AuthContext.tsx:19-20`. `ADMIN_EMAIL`/`ADMIN_PASSWORD`
  default to `admin@mevest.africa` / `MevestAdmin@2026` via
  `import.meta.env.VITE_ADMIN_EMAIL || '...'`. Vite bakes these into the production
  JS regardless of `.env`, so the fallback string is in `dist/assets/*.js` on every
  build that doesn't override it. Combined with the two docs printing the same
  credentials verbatim, any visitor to the public GitHub repo can "log in" as admin.
  **Why it's critical:** it doesn't currently touch real Supabase data (the mock
  session's `access_token` is the literal string `'mock-admin-access-token'`, which
  fails `supabase.auth.getUser()` in `ai-insights/index.ts:getUserId`), but the
  project's own roadmap (`TRANSFORMATION_IMPLEMENTATION.md §14`) proposes making
  `admin@mevest.africa` "a real DB-backed admin with a `user_roles` table" — the day
  someone does that against this same email/password pattern, it's a full
  authentication bypass on a wealth-management app with a password already public.
  **Fix:** delete the bypass entirely, or at minimum remove the hardcoded default
  (require `VITE_ADMIN_PASSWORD` to be set with no fallback, fail closed if absent),
  strip it from both docs, and never let a "mock" session share a code path with
  anything that could later gain real privileges.

- [ ] **`portfolio-snapshot` edge function has no authentication of any kind and runs
  with the `service_role` key** — `backend/supabase/functions/portfolio-snapshot/index.ts`.
  `config.toml:52` sets `verify_jwt = false` (as it does for all 6 functions), and
  unlike `ai-insights`, this function never calls `getUserId`/`auth.getUser` — it goes
  straight to `supabase.from('holdings').select('user_id, symbol, shares, cost_basis')`
  with no `.eq()` filter, i.e. every user's holdings, then upserts
  `portfolio_snapshots` for every user in the table. Any unauthenticated request to
  this URL (its path is guessable/discoverable from the six function names) triggers
  a full-table job billed against the service role, with Yahoo Finance calls fanned
  out per unique symbol. **Fix:** require a shared secret header (e.g.
  `x-cron-secret` checked against a Supabase secret) or Supabase's own scheduled-
  function auth, reject everything else with 401, and add per-invocation rate
  limiting independent of the AI function's limiter.

- [ ] **`RealtimeMarketContext.registerSymbols()` is dead code — live pricing is
  silently broken for the majority of possible holdings** —
  `frontend/src/context/RealtimeMarketContext.tsx:135-139` defines it and exposes it
  on the context, but `grep -rn "registerSymbols" frontend/src` shows it is never
  called anywhere. `fetchLiveQuotes` (line 143) only ever polls
  `CORE_SYMBOLS` (20 hardcoded US/crypto/index tickers, line 100-104) plus whatever
  was registered — which is nothing. `PortfolioPage.tsx:18` and `DashboardPage.tsx`
  merge in `prices[h.sym]`; when a holding's symbol isn't one of those 20 or one of
  the ~70 in `BUILTIN_ASSETS`, `prices[h.sym]` is `undefined` and the code falls back
  to `h.price`, which `PortfolioContext.tsx:47` and `:80` set equal to **cost basis**.
  Net effect: add any real-world stock that isn't Apple/Microsoft/Nvidia/etc., and
  its "current price" — and therefore P&L — is permanently pinned at 0% forever,
  with no error, no warning, no "stale" indicator. For an app whose stated purpose is
  Kenyan (NSE) + global portfolio tracking, this breaks the primary feature for most
  of its own target inventory (55 NSE tickers are in `BUILTIN_ASSETS` so those work,
  but anything outside the hardcoded universe does not). **Fix:** call
  `registerSymbols(holdings.map(h => h.sym))` from `PortfolioProvider`/`WatchlistProvider`
  whenever holdings/watchlist load or change, and add a visible "price unavailable"
  state in the UI instead of quietly reusing cost basis as if it were a live quote.

## Eliminate

- **`market-data.ts`'s `MARKET` object duplicates `RealtimeMarketContext.tsx`'s
  `BUILTIN_ASSETS`** for the same ~20 tickers with different, inconsistent fake
  numbers (e.g. KCB is priced at 42.10 in `RealtimeMarketContext.tsx` and 38.90 in
  `market-data.ts`; same story for several others). Two sources of truth for the same
  fictional data is worse than one — pick one, and make it schema-only (symbol/name/
  exchange), not fake prices that can silently disagree with each other on-screen.
- **Root `package-lock.json`** — 98 bytes, `"packages": {}`, no root `package.json`
  exists. It's a stray artifact from an `npm install` run at the wrong directory that
  resolved to nothing. Delete it; it actively invites someone to `npm install` from
  the repo root and think it did something.
- **`vite.config.ts:13-18`'s `/api` proxy to `http://localhost:3001`** — nothing in
  the frontend calls `/api/*` (confirmed via repo-wide grep). No such server exists
  anywhere in this repo. Leftover scaffold config; delete it.
- **`frontend/playwright.config.ts` + `playwright-fixture.ts`** — `testDir` is set to
  `"./frontend/e2e"`, which resolves relative to the config file's own directory
  (`frontend/`) to `frontend/frontend/e2e` — a path that doesn't exist. There are zero
  `*.spec.ts` files anywhere in the repo. `@playwright/test` is a real dependency
  (adds install time and a `critical`-adjacent transitive vuln surface) backing
  nothing. Either write real specs and fix the path, or drop Playwright.
- **The "Data Sources" tab's fake connection test** —
  `frontend/src/pages/SettingsPage.tsx:149-166`. `handleTestApiKey` never calls
  `provider.testUrl` (defined at lines 15-19 but never fetched anywhere in the file).
  It just checks `stored.key.length >= 8` and reports "Connection valid" for any
  8+ character string. Worse, even a real key would do nothing: none of the five
  market-data edge functions read `user_api_keys` — `market-quotes`, `market-chart`,
  `market-search`, `market-news`, and the `ai-insights` tool calls all hit
  `query1/query2.finance.yahoo.com` directly and unconditionally. The entire
  "bring your own API key" feature is UI theater over a real, RLS-protected,
  **unencrypted** (`key_value text`, migration `20260513...sql`) secrets table.
  Either wire it up for real or remove the tab — right now it teaches users to paste
  real third-party API keys into a database that nothing reads, in plaintext.
- **The Security tab's "Two-Factor Authentication" toggle** (`SettingsPage.tsx`
  `security.twoFA`, defaults to `true`) — `saveSettings()` just JSON-stringifies it
  into `user_settings.settings`. There is no `supabase.auth.mfa` call anywhere in the
  codebase. A financial app defaulting a fake 2FA toggle to "on" is actively
  misleading about the account's real security posture.
- **Fabricated changelog entries in `TRANSFORMATION_IMPLEMENTATION.md`** — Section
  4, Phase 6, item 4 ("Auth UI") cites `AuthPage.tsx:2,58,109` for an admin-credential
  "Fill admin credentials" card with `ShieldCheck` icon and specific toast copy. None
  of it exists: `grep -n "ShieldCheck\|ADMIN_CREDENTIALS" frontend/src/pages/AuthPage.tsx`
  returns nothing, and `ADMIN_CREDENTIALS` (exported from `AuthContext.tsx:187`) is
  never imported anywhere. Section 3.2's "Phase 2 ✅ Completed" claims React Router
  code-splitting replaced the old `useState('dashboard') + switch` pattern — the
  literal switch statement is still there, verbatim, in `Index.tsx:40+`. This
  document should not be trusted as a record of what shipped; either regenerate it
  from an actual diff review or delete it before it misleads the next engineer (or
  agent) who reads it as ground truth.

## Introduce

- **A real market-data fallback chain.** `ALPHA_VANTAGE_KEY`, `FINNHUB_KEY`,
  `COINGECKO_KEY` are documented in `.env.example` and the README as an active
  "Yahoo → Alpha Vantage → Finnhub → CoinGecko cascade," but none of the five
  market-data edge functions reference any of those env vars — confirmed by
  `grep -rn "ALPHA_VANTAGE\|FINNHUB\|COINGECKO" backend/` returning nothing outside
  `.env.example`. Every quote, search, chart, and news call is a single unauthenticated
  fetch to `query1/query2.finance.yahoo.com` with a spoofed browser `User-Agent`
  string — an undocumented endpoint Yahoo can rate-limit or block without notice, with
  zero contract and zero SLA. This is the single point of failure for the entire
  product's core feature. Implement at least one real fallback provider before
  calling this "production-ready."
- **Proper JWT validation on all six edge functions**, not just `ai-insights`.
  `market-quotes`/`chart`/`search`/`news` being open is lower-risk (public data), but
  `portfolio-snapshot` needs it immediately (see Critical Issues), and setting
  `verify_jwt = true` project-wide in `config.toml` for anything that isn't
  intentionally public should be the default, not an opt-in "hardening" listed under
  Future Possibilities.
- **Distributed rate limiting.** `ai-insights/index.ts:275-282`'s limiter is an
  in-memory `Map` scoped to a single Deno isolate — the code comment admits
  "per-instance only." On a platform that spins new isolates per cold start/region,
  this provides close to zero real protection at any scale. Move it to a durable
  store (Supabase table with a short TTL, or Upstash Redis as the doc's own roadmap
  suggests) before relying on it.
- **A CI pipeline that actually runs lint/test/build and fails on error.** None
  exists today (no `.github/workflows`). `npm run lint` currently exits with 30
  errors and 16 warnings (verified by running it) — set that up first, or the first
  CI run will be red on day one.
- **Real automated tests.** The entire test suite is
  `frontend/src/test/example.test.ts`: `expect(true).toBe(true)`. Zero coverage of
  `AuthContext`, `PortfolioContext`, `WatchlistContext`, or any page. At minimum, test
  the admin-bypass branch, the localStorage fallback paths in `PortfolioContext`/
  `WatchlistContext`, and the `add_holding`/`remove_holding` validation logic in
  `ai-insights/index.ts` (the `validSymbol`/`validatePositiveNum` guards are the only
  server-side input validation in the whole backend and currently have no tests).
- **A visible "data may be delayed / demo" indicator wherever a non-live price is
  shown.** `isLive` already exists as a flag on `UniversalAsset` — it's computed but
  never rendered as a disclosure to the user. For a platform that displays fabricated
  numbers (`BUILTIN_ASSETS`, `MARKET`) as if they were live market data, and can
  silently fall back to cost-basis-as-price (see Critical Issues), not labeling stale
  data is a real disclosure problem for anything marketed as investment tooling.
- **Encryption at rest for `user_api_keys.key_value`**, or don't collect it. It's
  currently a plain `text` column readable by anyone with the service_role key (used,
  unauthenticated, in `portfolio-snapshot`) or DB access.

## Modify (with specifics)

- **`frontend/src/context/AuthContext.tsx`** — remove the hardcoded default password
  (`|| 'MevestAdmin@2026'` on line 20 and `|| 'admin@mevest.africa'` on line 19); if
  the bypass stays for demo purposes, require both env vars to be explicitly set with
  no fallback and add a build-time check that fails the build if
  `NODE_ENV=production` and the bypass is enabled without `VITE_DISABLE_ADMIN_BYPASS`
  set. Also fix the four `@typescript-eslint/no-explicit-any` lint errors on lines
  9-12 (the `User`/`Session` mock casts) and the empty `catch {}` block at line 64
  (silently swallowing `localStorage` errors makes debugging session issues
  impossible — at minimum `console.warn`).

- **`frontend/src/context/RealtimeMarketContext.tsx`** — wire `registerSymbols` into
  `PortfolioProvider` and `WatchlistProvider` (see Critical Issues). While there,
  dedupe against `market-data.ts`: export one canonical `KNOWN_ASSETS` list from a
  single file and delete the other.

- **`backend/supabase/functions/portfolio-snapshot/index.ts`** — add a secret-header
  check as the very first line inside `Deno.serve`, before any DB call:
  ```ts
  const cronSecret = req.headers.get('x-cron-secret');
  if (cronSecret !== Deno.env.get('CRON_SECRET')) {
    return new Response('Unauthorized', { status: 401, headers: corsHeaders });
  }
  ```
  Set `CRON_SECRET` via `supabase secrets set`, and pass it from whatever triggers
  this (see Deployment Plan — a GitHub Actions cron is the natural caller here).

- **`backend/supabase/functions/market-quotes/index.ts`,
  `market-chart/index.ts`, `market-search/index.ts`, `market-news/index.ts`,
  `ai-insights/index.ts` (tool functions)** — add one real fallback provider (Finnhub
  has the most generous free tier for this use case — see Deployment Plan). Wrap the
  existing Yahoo call in a try/catch that falls through to the fallback instead of
  returning empty arrays, which is what currently happens on any Yahoo failure.

- **`frontend/src/pages/Index.tsx`** — replace the `useState('dashboard')` + manual
  `switch` (lines ~24-40+) with actual `react-router-dom` routes
  (`/dashboard`, `/portfolio`, `/markets`, etc.) and `React.lazy()` + `Suspense` per
  page. This is the single biggest lever on the 1.67MB/440kB-gzip single-chunk bundle
  (verified via `npm run build` — no chunk splitting occurs at all today, contrary to
  what `TRANSFORMATION_IMPLEMENTATION.md` claims). Also gets you real deep-linking
  and browser back/forward, which the current design doesn't support at all — a
  reload always lands on the dashboard, in-app navigation never changes the URL.

- **`frontend/src/pages/SettingsPage.tsx`** — `handleTestApiKey` (lines 149-166):
  either actually `fetch(provider.testUrl + key)` (careful: this calls third-party
  APIs directly from the browser with the user's key exposed in the request URL/
  network tab — better to proxy it through an edge function) or remove the "Test
  Connection" button and the "connected" status entirely so it stops lying. Fix the
  five `@typescript-eslint/no-explicit-any` errors (lines 65, 70, 77, 88, 119).

- **`frontend/src/context/PortfolioContext.tsx` / `WatchlistContext.tsx`** — four
  empty `catch {}` blocks each (localStorage read/write failures are silently
  swallowed at `PortfolioContext.tsx:67,76,96,110` and `WatchlistContext.tsx:38,46,63,74`).
  At minimum log; on `addHolding`/`removeHolding`, consider surfacing a toast when the
  Supabase `upsert`/`delete` fails so the user knows their change didn't actually
  persist server-side (right now it's a silent `console.warn`, and the optimistic
  local state already updated, so the UI looks successful even when the write to
  Supabase failed).

- **`frontend/src/pages/ResetPasswordPage.tsx`** — `minLength={6}` (line ~52) with no
  complexity requirement and no confirm-password field. For a platform handling
  investment data, raise this to a real policy (12+ chars or a zxcvbn-style strength
  check) and add password confirmation to catch typos before lockout.

- **Root of repo** — delete `package-lock.json` (see Eliminate). Add a `LICENSE` file
  if this is meant to be a real product (README currently says "See repo license if
  present" — none is present).

## Deployment Plan (free-tier target)

**Backend: already deployed — no action needed to choose a host.** This project's
backend is Supabase (Postgres + Auth + 6 Deno edge functions), and it's already
running on a live hosted Supabase project (`fulgofnlmlmetlgidhup`). Supabase's free
tier (verified current as of Sep 2026: 500MB database, 1GB file storage, 5GB egress,
50,000 MAUs, 500,000 edge function invocations/month) comfortably covers an early-
stage product at this scale. The one real gotcha: **free-tier Supabase projects pause
after 7 days with no API traffic**, and this project has no keepalive. Add a
scheduled GitHub Actions workflow that pings `/auth/v1/health` every 2-3 days — this
also solves the `portfolio-snapshot` cron problem in one shot (see below) and, unlike
a paid Pro plan, costs nothing.

**Frontend: static Vite SPA, needs a static host only — no server-side rendering, no
background worker, no websockets, no local disk writes.** That rules out anything
billed for compute; this is a pure "build once, serve files" problem.

- **Primary: Cloudflare Pages.** Free tier (verified Aug-Sep 2026): unlimited static
  bandwidth, 500 builds/month, up to 20,000 files/deployment, custom domains, no
  credit card, and — the deciding factor over the alternative below — **commercial
  use is explicitly permitted** on the free tier. This project doesn't need Cloudflare
  Pages Functions at all (all dynamic work is already on Supabase), so the
  Workers-request ceiling that trips up other Pages projects never comes into play
  here.
  - Incompatibilities in this repo: none functional. Two things need fixing to
    deploy cleanly:
    1. There's no root `package.json`, so Cloudflare Pages' build must be pointed at
       the `frontend/` subdirectory (set "Root directory" to `frontend` in the Pages
       project settings), not the repo root.
    2. `react-router-dom`'s `BrowserRouter` needs an SPA fallback so a hard refresh
       on `/reset-password` doesn't 404 — add `frontend/public/_redirects` containing
       `/* /index.html 200`.
  - Exact config:
    - Build command: `npm run build`
    - Build output directory: `dist`
    - Root directory: `frontend`
    - Environment variables (Pages project settings, not committed):
      `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_SUPABASE_PROJECT_ID`, and
      — if the admin bypass is kept at all — `VITE_ADMIN_PASSWORD` set to something
      that is **not** `MevestAdmin@2026` and is not in any doc.

- **Fallback: GitHub Pages.** Free forever for public repos (this repo already is
  public), no separate signup, commercial use permitted, builds via a simple GitHub
  Actions workflow (`actions/deploy-pages`). Same two fixes apply (build from
  `frontend/`, SPA fallback — GitHub Pages uses a `404.html`-copies-`index.html` trick
  instead of `_redirects` since it has no redirect rules engine). Weaker than
  Cloudflare Pages only in that there's no dashboard-based env var injection for
  preview builds; secrets go through GitHub Actions repo secrets instead, which is
  fine here since there's only one environment.

- **Edge function fallback provider (for the market-data reliability gap in
  "Introduce"):** Finnhub's free tier (60 calls/minute, no card required) is the best
  fit to add first — it's already a documented-but-unused env var
  (`FINNHUB_KEY`) in this repo, so wiring it in is additive, not a new integration.

## Priority Order

1. **(S)** Remove hardcoded admin password default from `AuthContext.tsx`; scrub both
   docs of the plaintext credential.
2. **(S)** Add the `x-cron-secret` (or equivalent) check to `portfolio-snapshot`.
3. **(M)** Wire `registerSymbols()` into `PortfolioProvider`/`WatchlistProvider`; add
   a visible "price unavailable" state instead of the cost-basis fallback.
4. **(S)** Set up the GitHub Actions Supabase keepalive ping (also triggers the now-
   secured `portfolio-snapshot` on a schedule instead of never).
5. **(M)** Deploy to Cloudflare Pages with the two config fixes above — get a real
   URL live before doing anything else, since none of this matters if there's nothing
   to test against.
6. **(M)** Set up CI: lint → test → build, failing on the 30 current lint errors
   (fix them as part of this step — mostly `no-explicit-any` and empty `catch{}`).
7. **(L)** Replace `Index.tsx`'s manual switch with real `react-router-dom` routes +
   `lazy()` code-splitting; delete the duplicate `market-data.ts`/`BUILTIN_ASSETS`
   dataset in the same pass since both touch the same pages.
8. **(M)** Add one real market-data fallback provider (Finnhub) behind the existing
   Yahoo calls in all 5 relevant edge functions.
9. **(S)** Fix or remove the fake "Test Connection" button and the unused 2FA toggle
   in `SettingsPage.tsx`; decide whether `user_api_keys` is a real feature or gets
   deleted.
10. **(M)** Write real tests: auth bypass branch, Portfolio/Watchlist localStorage
    fallback paths, `ai-insights` tool input validation. Delete or actually populate
    the Playwright setup — don't leave a pointing-at-nothing `testDir`.
11. **(S)** Delete root `package-lock.json`, the dead `/api` proxy in
    `vite.config.ts`, and rewrite `TRANSFORMATION_IMPLEMENTATION.md` from an actual
    diff instead of leaving fabricated entries in it.
12. **(L)** Encrypt `user_api_keys.key_value` at rest or remove the feature; set
    `verify_jwt = true` across all edge functions that don't need to be public.
