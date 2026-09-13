# F1 Predictor 2026 — Transformation Plan

Repository: `Jack-ki1/FORMULA_1_PREDICTOR_2026` (branch: `main`)

This picks up where `docs/MIGRATION.md` / the original decoupling plan left off.
The migration itself (Flask blueprints → `/api/v1` + React shell) landed cleanly.
What's below fixes the two runtime bugs you hit, makes the repo deployable on
free hosting, and lays out a creative roadmap on top of it.

**Everything under "Already applied" was implemented and verified in a clone
of your repo** (`npm run build` passes, Python files `py_compile` clean,
`config.settings` imports and prints the new CSP correctly). Copy each block
into the matching file in your repo — every one is a complete, ready-to-paste
file or an exact diff.

---

## TL;DR

| # | Problem | Root cause | Status |
|---|---|---|---|
| 1 | Port 5000 shows raw/unstyled HTML | `Content-Security-Policy: default-src 'self'` silently blocked Tailwind CDN, Chart.js CDN, Google Fonts, Font Awesome and inline `<script>` on **every** Jinja page | **Fixed** (Phase 1) |
| 2 | Port 5173 shows different content | It's the new React SPA's dev server — working as designed, but the `Home` and `Reports` pages were placeholders (17 and 1 lines) next to a 2,090-line legacy homepage | **Fixed for Home/Reports** (Phase 2); other pages already had real API wiring |
| 3 | Not ready for Vercel | Backend has `fastf1`, `xgboost`, `lightgbm`, `scikit-learn`, `weasyprint` — structurally incompatible with Vercel serverless functions | **Fixed via split topology**: Vercel (frontend) + Render (backend) — configs included (Phase 3) |
| 4 | "Make it better, be creative" | — | Shipped 5 new F1-themed pieces now; roadmap for more (Phase 4) |

---

## Phase 1 — Port 5000: CSS/JS not loading

### Root cause

`dashboard/app.py` registers `add_security_headers` as an `after_request` hook,
which writes `config/settings.py`'s `SECURITY_HEADERS` dict onto every
response. That dict contained:

```python
'Content-Security-Policy': "default-src 'self'"
```

`default-src 'self'` is the fallback for **every** unspecified fetch
directive — `script-src`, `style-src`, `font-src`, `img-src`, all of it. Your
templates load:

- `base.html` (used by `/dashboard/`, `/standings`, `/h2h`, `/constructors`,
  `/analytics`) → Tailwind from `cdn.tailwindcss.com`, Chart.js from
  `cdn.jsdelivr.net`, plus an inline `<script>` that sets the theme before
  paint.
- `homepage.html` (served at `/`, ~2,090 lines, its own hero/cursor/lightbox
  build) → the same Tailwind CDN + an inline `tailwind.config` script, Google
  Fonts via `fonts.googleapis.com`, Font Awesome via `cdnjs.cloudflare.com`,
  and a large inline `<script>` block driving the cursor/lightbox/ticker
  interactions.

None of those origins were allowlisted, so the browser silently dropped
every one of them (check your browser console — it will be full of CSP
violation entries for exactly these origins). Tailwind never loaded, so
every `flex`, `grid`, `px-4`, `gap-3`… utility class in your markup did
nothing — what you saw was correct HTML with almost no layout or styling
applied. `styles.css`'s own `@import url('https://fonts.googleapis.com/...')`
was blocked the same way.

This is the entire explanation for "content is right, but it just looks like
raw HTML."

### Fix applied — `config/settings.py`

```python
    # CORS — only matters if the frontend calls this API cross-origin (e.g.
    # Vercel frontend -> Render backend directly, without a rewrite proxy in
    # front of it). Comma-separated origins, e.g.
    # "https://f1-predictor.vercel.app,https://f1-predictor-2026.vercel.app".
    # Defaults to "*" so local dev / docker-compose keep working unchanged.
    CORS_ORIGINS: str = '*'

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = '100/hour'
    RATE_LIMIT_AUTHED: str = '500/hour'

    # Security headers
    #
    # NOTE: the previous value here was a bare "default-src 'self'". Every
    # Jinja page (base.html + homepage.html) loads Tailwind, Chart.js, Google
    # Fonts and Font Awesome from CDNs, plus a handful of inline
    # <script>/style="" attributes. A bare default-src silently blocked all
    # of that — CSS/JS never executed, so the browser fell back to unstyled
    # markup ("raw HTML"). This is the root cause of the port-5000 rendering
    # bug. The policy below explicitly allowlists exactly the external
    # origins this app actually uses; nothing else is relaxed. See "Phase 1
    # follow-up" below for self-hosting these assets so this can tighten
    # back to a bare 'self'.
    SECURITY_HEADERS: Dict[str, str] = {
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        ),
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
```

Replace the existing `SECURITY_HEADERS` dict (and add the `CORS_ORIGINS`
field above it — it's used in Phase 3) with the block above. This alone
fixes port 5000: reload `/`, `/dashboard/`, `/standings/`, etc. and Tailwind
utility classes, Chart.js, fonts and icons will all render.

### Phase 1 follow-up (recommended, not required) — stop depending on CDNs at all

The fix above is a safe allowlist, but every page still makes 4–5 external
requests on load (Tailwind CDN, Chart.js CDN, Google Fonts, Font Awesome),
which means: slower first paint, a hard dependency on those CDNs staying up,
and it won't work at all in network-restricted environments. Your own
migration notes already flagged this for the React side ("Tailwind should
move from CDN usage into a proper frontend build") — the same applies to the
legacy dashboard. Once done, `SECURITY_HEADERS` can tighten back to:

```python
'Content-Security-Policy': "default-src 'self'; frame-ancestors 'none'"
```

Steps:

1. **Compile Tailwind instead of loading it from the CDN.**
   ```bash
   cd dashboard
   npm init -y
   npm install -D tailwindcss@3 postcss autoprefixer
   npx tailwindcss init -p
   ```
   `dashboard/tailwind.config.js`:
   ```js
   module.exports = {
     content: ['./templates/**/*.html'],
     theme: { extend: { fontFamily: { sans: ['Inter','sans-serif'], display: ['Montserrat','sans-serif'] }, colors: { f1red: '#E10600' } } },
     plugins: [],
   }
   ```
   `dashboard/static/css/tailwind-input.css`:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```
   Build: `npx tailwindcss -i ./static/css/tailwind-input.css -o ./static/css/tailwind.css --minify`
   In `base.html` and `homepage.html`, replace
   `<script src="https://cdn.tailwindcss.com"></script>` (and, in
   `homepage.html`, the inline `tailwind.config = {...}` script right after
   it) with:
   ```html
   <link rel="stylesheet" href="{{ url_for('static', filename='css/tailwind.css') }}">
   ```

2. **Vendor Chart.js.**
   ```bash
   npm install chart.js@4.4.4
   cp node_modules/chart.js/dist/chart.umd.min.js dashboard/static/js/vendor/chart.umd.min.js
   ```
   Replace `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>`
   with `<script src="{{ url_for('static', filename='js/vendor/chart.umd.min.js') }}"></script>`.

3. **Self-host the fonts.** Download woff2 files for Titillium Web, IBM Plex
   Mono, Inter and Montserrat (e.g. via `google-webfonts-helper`) into
   `dashboard/static/fonts/`, add `@font-face` rules at the top of
   `styles.css`, and delete the `@import url('https://fonts.googleapis.com/...')`
   line from `styles.css` and the two `<link rel="preconnect"...>` /
   `<link href="https://fonts.googleapis.com/...">` lines from
   `homepage.html`.

4. **Drop Font Awesome for the 5 icons actually used** (`fa-play`,
   `fa-pause`, `fa-volume-high`, `fa-volume-xmark`, `fa-check` — all inside
   the video controls / copy-link button in `homepage.html`). Swap each
   `<i class="fa-solid fa-...">` for a small inline `<svg>` (same pattern
   already used for the moon/sun theme icons in `base.html`). Removes the
   `cdnjs.cloudflare.com` Font Awesome stylesheet entirely.

5. **Move the inline theme-init script to a file.** Both `base.html` and
   `homepage.html` have an inline `<script>` that reads `localStorage` and
   sets `data-theme` before paint. Save it as
   `dashboard/static/js/theme_init.js` and load it with a normal
   `<script src="...">` tag. This removes the last need for
   `'unsafe-inline'` in `script-src`.

Once all five are done, ship the tightened CSP from above.

---

## Phase 2 — Port 5173: what it is, and why it looked different

### What it is

`http://localhost:5173` is Vite's dev server for `frontend/` — the new React
SPA from the migration. `frontend/vite.config.ts` already proxies `/api`,
`/dashboard`, `/standings`, `/h2h`, `/constructors`, `/analytics`,
`/reports`, `/health` to `http://localhost:5000`, so in dev it's genuinely
talking to your real Flask backend and real prediction engine — this part
was never broken. You need it (or its production build) because it's the
strangler-fig replacement UI the whole migration plan was building toward;
5000 is the legacy Jinja app being phased out, 5173 is where it's headed.

### Why the content looked "totally different"

Not a bug — a completion gap. I compared every page:

| Page | Jinja (port 5000) | React (port 5173) before this pass | Status |
|---|---|---|---|
| `/` (home) | `homepage.html`, ~2,090 lines: hero video, custom cursor, lightbox, animated stat counters, image banners | `pages/Home/index.tsx`, **17 lines**: a title, a paragraph, 3 links | Fixed below |
| `/dashboard` | `dashboard.html` + `dashboard.js` | `pages/Dashboard/index.tsx` (48 lines) driving real components (`RaceSelector`, `SessionSelector`, `PredictionControls`, `GridEditor`, `PredictionCharts`, `AISidebar`…), each wired to `/api/v1/*` via TanStack Query hooks | **Already at parity** — just terser code, same functionality |
| `/standings`, `/h2h`, `/constructors`, `/analytics` | Jinja + page-specific JS | Thin page containers over real API-backed components | **Already at parity** |
| `/reports` | `reports.py` blueprint, CSV/JSON/PDF/share export | `pages/Reports/index.tsx`, **1 line**: a stub paragraph | Fixed below |

So: if what you loaded first was `/`, you hit the single biggest gap in the
whole migration. Everything past the homepage was closer than it looked.

### Fix applied

**`frontend/src/pages/Home/index.tsx`** — full rewrite. Hero with a kicker,
big title, subtitle, primary/ghost CTAs, an F1 start-lights animation, and a
**live countdown to the next race** pulled from real `/api/v1/races` data; a
checkered-flag divider; an animated stat ticker (races/drivers/constructors/
simulations-per-race); a 6-card feature grid linking to every section; a
"how a prediction gets made" panel. Zero new npm dependencies — built
entirely on your existing `.card` / `.btn-primary` / `.navy-panel` /
`--red` design tokens from `legacy.css`.

```tsx
import { Link } from 'react-router-dom'
import { useRaces } from '../../hooks/useRaces'
import { useCountUp } from '../../hooks/useCountUp'
import { StartLights } from '../../components/home/StartLights'
import { NextRaceCountdown } from '../../components/home/NextRaceCountdown'

function Stat({ value, suffix = '', label }: { value: number; suffix?: string; label: string }) {
  const { display, ref } = useCountUp(value)
  return (
    <div className="hp-stat" ref={ref as any}>
      <span className="hp-stat-value f1-display">{display.toLocaleString()}{suffix}</span>
      <span className="hp-stat-label fs-11">{label}</span>
    </div>
  )
}

const ICONS = {
  dashboard: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="M7 15l3-4 3 3 5-7" /></svg>
  ),
  standings: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 21V9M14 21V3M20 21v-6M4 21v-3" /></svg>
  ),
  h2h: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="7" cy="8" r="3" /><circle cx="17" cy="8" r="3" /><path d="M2 21c0-3 2.5-5 5-5s5 2 5 5M12 21c0-3 2.5-5 5-5s5 2 5 5" /></svg>
  ),
  constructors: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 17h18M5 17l1.5-6h11L19 17M9 11V7h6v4" /><circle cx="7.5" cy="19" r="1.5" /><circle cx="16.5" cy="19" r="1.5" /></svg>
  ),
  analytics: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z" /><path d="M21.2 8.4A10 10 0 0 0 15.6 2.8v5.6h5.6z" /></svg>
  ),
  reports: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M9 13h6M9 17h6" /></svg>
  ),
}

const FEATURES: Array<{ to: string; icon: keyof typeof ICONS; title: string; blurb: string }> = [
  { to: '/dashboard', icon: 'dashboard', title: 'Prediction Dashboard', blurb: 'Pick a Grand Prix and session, tune the grid, and run the Monte Carlo engine live.' },
  { to: '/standings', icon: 'standings', title: 'Standings', blurb: "Live driver and constructor standings for the 2026 season, with fallback to season data." },
  { to: '/h2h', icon: 'h2h', title: 'Head-to-Head', blurb: 'Compare any two drivers — Elo-derived win probability, reversed and ranked.' },
  { to: '/constructors', icon: 'constructors', title: 'Constructors', blurb: 'Team power rankings and full 2026 lineups, car by car.' },
  { to: '/analytics', icon: 'analytics', title: 'Analytics & Settings', blurb: 'Model accuracy tracking, feature-weight tuning, and target calibration.' },
  { to: '/reports', icon: 'reports', title: 'Reports', blurb: 'Export any prediction as CSV, JSON, a PDF race sheet, or a shareable card.' },
]

export function HomePage() {
  const { data: races } = useRaces()
  const raceCount = races?.filter((r) => r.status !== 'cancelled').length ?? 24

  return (
    <div>
      {/* ---------- HERO ---------- */}
      <section className="hp-hero">
        <div className="hp-hero-grid-bg" aria-hidden="true" />
        <div className="hp-hero-glow" aria-hidden="true" />
        <div className="px-4 sm:px-8 py-16 sm:py-24 relative">
          <span className="hp-kicker fs-11">2026 SEASON · AI RACE INTELLIGENCE</span>
          <h1 className="hp-title f1-display">
            F1 PREDICTOR <span style={{ color: 'var(--red)' }}>2026</span>
          </h1>
          <p className="hp-subtitle text-sub">
            Monte-Carlo race simulation, Elo-based head-to-heads and an optional AI layer —
            built on a real prediction engine, not a guess.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-6">
            <Link to="/dashboard" className="btn-primary">Open Dashboard</Link>
            <Link to="/standings" className="btn-ghost">View Standings</Link>
            <StartLights />
          </div>

          <div className="mt-8 max-w-md">
            <NextRaceCountdown />
          </div>
        </div>
      </section>

      {/* ---------- CHECKERED DIVIDER ---------- */}
      <div className="hp-checkered" aria-hidden="true" />

      {/* ---------- STAT TICKER ---------- */}
      <section className="px-4 sm:px-8 py-8">
        <div className="hp-stat-row">
          <Stat value={raceCount} label="RACES THIS SEASON" />
          <Stat value={20} label="DRIVERS MODELLED" />
          <Stat value={10} label="CONSTRUCTORS" />
          <Stat value={10000} suffix="+" label="SIMULATIONS PER RACE" />
        </div>
      </section>

      {/* ---------- FEATURE GRID ---------- */}
      <section className="px-4 sm:px-8 py-6">
        <h2 className="f1-display text-xl font-bold">Everything the engine can tell you</h2>
        <p className="text-sub fs-11 mt-1">Six views onto the same prediction engine — pick where you want to start.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
          {FEATURES.map((f) => (
            <Link key={f.to} to={f.to} className="card p-4 hp-feature-card">
              <span className="hp-feature-icon">{ICONS[f.icon]}</span>
              <div className="f1-display font-bold mt-3">{f.title}</div>
              <p className="text-sub fs-11 mt-1">{f.blurb}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* ---------- HOW IT WORKS ---------- */}
      <section className="px-4 sm:px-8 py-10">
        <div className="navy-panel p-6 sm:p-8 rounded-xl text-white">
          <h2 className="f1-display text-xl font-bold">How a prediction gets made</h2>
          <div className="grid sm:grid-cols-3 gap-6 mt-6">
            <div className="hp-step">
              <span className="hp-step-number f1-mono">01</span>
              <div className="f1-display font-bold mt-2">Build the grid</div>
              <p className="fs-11 mt-1" style={{ color: 'rgba(255,255,255,.75)' }}>
                Race, qualifying or practice — pull the real 2026 calendar, weather and starting grid, or set it manually.
              </p>
            </div>
            <div className="hp-step">
              <span className="hp-step-number f1-mono">02</span>
              <div className="f1-display font-bold mt-2">Run the simulation</div>
              <p className="fs-11 mt-1" style={{ color: 'rgba(255,255,255,.75)' }}>
                Thousands of Monte Carlo laps factor in safety-car odds, chaos level and driver/team strength — with an optional AI adjustment layered on top.
              </p>
            </div>
            <div className="hp-step">
              <span className="hp-step-number f1-mono">03</span>
              <div className="f1-display font-bold mt-2">Read the odds</div>
              <p className="fs-11 mt-1" style={{ color: 'rgba(255,255,255,.75)' }}>
                Calibrated win, podium and points probabilities, with confidence intervals and drift detection — export it or take it to the grid editor.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
```

**`frontend/src/hooks/useCountUp.ts`** (new file):

```ts
import { useEffect, useRef, useState } from 'react'

/**
 * Animates a number from 0 -> value once it scrolls into view (or immediately
 * if used without a ref). Pure CSS/JS, no dependency — mirrors the
 * `animateNumber()` IntersectionObserver pattern from the legacy
 * homepage.html ticker so the React version keeps the same feel.
 */
export function useCountUp(value: number, durationMs = 1200) {
  const [display, setDisplay] = useState(0)
  const ref = useRef<HTMLElement | null>(null)
  const started = useRef(false)

  useEffect(() => {
    const node = ref.current
    if (!node) {
      animate()
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !started.current) {
          started.current = true
          animate()
        }
      },
      { threshold: 0.4 }
    )
    observer.observe(node)
    return () => observer.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  function animate() {
    const start = performance.now()
    function frame(now: number) {
      const progress = Math.min(1, (now - start) / durationMs)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.floor(value * eased))
      if (progress < 1) requestAnimationFrame(frame)
      else setDisplay(value)
    }
    requestAnimationFrame(frame)
  }

  return { display, ref }
}
```

**`frontend/src/components/home/StartLights.tsx`** (new file):

```tsx
import { useEffect, useState } from 'react'

/**
 * The five red F1 start lights: illuminate one at a time, hold, then cut out
 * together ("lights out and away we go") before looping. Purely decorative,
 * zero dependencies — sits in the hero next to the CTA buttons.
 */
export function StartLights() {
  const [lit, setLit] = useState(0) // 0..5 lights lit; 6 = "lights out" frame

  useEffect(() => {
    let step = 0
    let timer: ReturnType<typeof setTimeout>
    const sequence = () => {
      if (step <= 5) {
        setLit(step)
        step++
        timer = setTimeout(sequence, step === 6 ? 900 : 420)
      } else {
        setLit(6) // lights out
        step = 0
        timer = setTimeout(sequence, 1600)
      }
    }
    timer = setTimeout(sequence, 500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="hp-start-lights" role="img" aria-label="Formula 1 start lights sequence">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={`hp-start-light ${lit >= n && lit < 6 ? 'is-lit' : ''}`} />
      ))}
    </div>
  )
}
```

**`frontend/src/components/home/NextRaceCountdown.tsx`** (new file):

```tsx
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRaces } from '../../hooks/useRaces'
import type { Race } from '../../types'

function timeParts(msRemaining: number) {
  const clamped = Math.max(0, msRemaining)
  const totalSeconds = Math.floor(clamped / 1000)
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
  }
}

/** Live countdown to the next non-cancelled race, driven by real /api/v1/races data. */
export function NextRaceCountdown() {
  const { data: races, isLoading } = useRaces()
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const nextRace: Race | undefined = useMemo(() => {
    if (!races) return undefined
    return races
      .filter((r) => r.status !== 'cancelled' && new Date(r.date).getTime() >= Date.now())
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())[0]
  }, [races])

  if (isLoading) {
    return <div className="hp-countdown card p-4"><span className="text-sub fs-11">Loading race calendar…</span></div>
  }
  if (!nextRace) {
    return null
  }

  const { days, hours, minutes, seconds } = timeParts(new Date(nextRace.date).getTime() - now)
  const cell = (value: number, label: string) => (
    <div className="hp-countdown-cell">
      <span className="hp-countdown-value f1-mono">{String(value).padStart(2, '0')}</span>
      <span className="hp-countdown-label">{label}</span>
    </div>
  )

  return (
    <Link to="/dashboard" className="hp-countdown card p-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <span className="fs-11 text-sub">Up next · Round {nextRace.round}</span>
          <div className="f1-display font-bold text-base mt-1">
            {nextRace.flag} {nextRace.name}
          </div>
          <span className="fs-11 text-muted">{nextRace.circuit}, {nextRace.location}</span>
        </div>
        <div className="hp-countdown-grid">
          {cell(days, 'DAYS')}
          {cell(hours, 'HRS')}
          {cell(minutes, 'MIN')}
          {cell(seconds, 'SEC')}
        </div>
      </div>
    </Link>
  )
}
```

**`frontend/src/pages/Reports/index.tsx`** — replaces the 1-line stub with a
real (if intentionally simple — exports are triggered from the Dashboard,
this page explains and links there) page:

```tsx
const FORMATS: Array<{ id: string; title: string; blurb: string }> = [
  { id: 'csv', title: 'CSV', blurb: 'Raw probabilities per driver — opens straight into Sheets/Excel for your own analysis.' },
  { id: 'json', title: 'JSON', blurb: 'The full prediction payload — targets, confidence intervals, drift score, metadata.' },
  { id: 'pdf', title: 'PDF race sheet', blurb: 'A formatted, printable summary of the prediction (WeasyPrint-rendered).' },
  { id: 'share', title: 'Share card', blurb: 'A shareable image card with the headline prediction, for socials.' },
]

export function ReportsPage() {
  return (
    <div className="px-4 sm:px-8 py-6">
      <h2 className="f1-display text-xl font-bold">Reports</h2>
      <p className="text-sub fs-11 mt-2 max-w-2xl">
        Exports are generated from a live prediction, so start on the{' '}
        <a href="/dashboard" className="text-red" style={{ color: 'var(--red)' }}>Dashboard</a>{' '}
        — run a prediction, then use the Export control at the bottom of the results.
        Every format below is served from the same endpoint:{' '}
        <code className="f1-mono fs-11">POST /api/v1/reports/export</code>.
      </p>
      <div className="grid sm:grid-cols-2 gap-4 mt-6">
        {FORMATS.map((f) => (
          <div key={f.id} className="card p-4">
            <div className="f1-display font-bold">{f.title}</div>
            <p className="text-sub fs-11 mt-1">{f.blurb}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**`frontend/src/styles/globals.css`** — append (nothing existing is
changed, this is purely additive so `legacy.css`/`variables.css` tokens keep
driving the palette everywhere else):

```css
/* ==========================================================================
   HOME PAGE — hero, countdown, stat ticker, feature grid, checkered divider
   ========================================================================== */

.hp-hero { position: relative; overflow: hidden; isolation: isolate; }
.hp-hero-grid-bg {
  position: absolute; inset: 0; z-index: -2;
  background-image:
    linear-gradient(var(--gridline) 1px, transparent 1px),
    linear-gradient(90deg, var(--gridline) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: linear-gradient(to bottom, #000, transparent 92%);
  opacity: .6;
}
.hp-hero-glow {
  position: absolute; z-index: -1; left: -10%; right: -10%; top: -30%; height: 60%;
  background: radial-gradient(circle, rgba(225,6,0,.16), transparent 62%);
  filter: blur(50px);
}
.hp-kicker { color: var(--red); font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }
.hp-title { font-size: clamp(2.2rem, 6vw, 4rem); font-weight: 900; line-height: 1.02; margin-top: .5rem; letter-spacing: -.02em; }
.hp-subtitle { max-width: 42rem; margin-top: .9rem; font-size: 1rem; line-height: 1.6; }

.hp-start-lights { display: inline-flex; gap: 6px; padding: 8px 10px; background: var(--navy); border-radius: 999px; }
.hp-start-light { width: 10px; height: 10px; border-radius: 999px; background: #4a1512; transition: background .15s ease, box-shadow .15s ease; }
.hp-start-light.is-lit { background: var(--red); box-shadow: 0 0 10px 2px rgba(225,6,0,.7); }

.hp-countdown { display: block; text-decoration: none; transition: transform .2s ease, border-color .2s ease; }
.hp-countdown:hover { transform: translateY(-2px); border-color: var(--red); }
.hp-countdown-grid { display: flex; gap: 10px; }
.hp-countdown-cell { display: flex; flex-direction: column; align-items: center; min-width: 42px; }
.hp-countdown-value { font-size: 1.15rem; font-weight: 700; color: var(--red); }
.hp-countdown-label { font-size: 9px; letter-spacing: .12em; color: var(--muted); margin-top: 2px; }

.hp-checkered {
  height: 14px;
  background-image: conic-gradient(var(--border) 90deg, transparent 90deg 180deg, var(--border) 180deg 270deg, transparent 270deg);
  background-size: 14px 14px;
  opacity: .7;
}

.hp-stat-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
@media (min-width: 640px) { .hp-stat-row { grid-template-columns: repeat(4, 1fr); } }
.hp-stat { text-align: center; padding: 1.1rem .5rem; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
.hp-stat-value { display: block; font-size: 1.9rem; font-weight: 900; color: var(--red); }
.hp-stat-label { display: block; margin-top: 4px; letter-spacing: .08em; color: var(--muted); text-transform: uppercase; }

.hp-feature-card { text-decoration: none; display: block; transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease; }
.hp-feature-card:hover { transform: translateY(-4px); border-color: var(--red); box-shadow: 0 14px 34px rgba(0,0,0,.12); }
.hp-feature-icon { display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; border-radius: 9px; background: var(--red-tint); color: var(--red); }

.hp-step-number { font-size: 1.6rem; font-weight: 700; color: rgba(255,255,255,.35); }

/* Global fetch indicator — see components/shared/RaceLoadingBar.tsx */
.race-loading-bar-track { height: 2px; width: 100%; background: transparent; overflow: hidden; }
.race-loading-bar-fill {
  height: 100%; width: 0%; background: var(--red);
  box-shadow: 0 0 8px 1px rgba(225,6,0,.6);
  transition: width .2s ease, opacity .2s ease;
  opacity: 0;
}
.race-loading-bar-fill.is-active {
  width: 100%; opacity: 1;
  animation: race-loading-sweep 1.1s ease-in-out infinite;
}
@keyframes race-loading-sweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Podium reveal confetti — see components/prediction/PodiumReveal.tsx */
.podium-reveal { position: fixed; inset: 0; pointer-events: none; z-index: 60; overflow: hidden; }
.podium-confetti {
  position: absolute; top: -10px; width: 8px; height: 14px; opacity: .9;
  border-radius: 2px; animation-name: podium-fall; animation-timing-function: ease-in; animation-fill-mode: forwards;
  transform: rotate(var(--r, 0deg));
}
@keyframes podium-fall { to { transform: translateY(105vh) rotate(calc(var(--r, 0deg) + 360deg)); opacity: 0; } }
.podium-reveal-label {
  position: fixed; top: 14px; left: 50%; transform: translateX(-50%);
  background: var(--navy); color: #fff; padding: 8px 16px; border-radius: 999px;
  font-weight: 700; box-shadow: 0 10px 30px rgba(0,0,0,.25); animation: podium-label-in .3s ease;
}
@keyframes podium-label-in { from { opacity: 0; transform: translate(-50%,-10px); } to { opacity: 1; transform: translate(-50%,0); } }
```

Two more pieces (also part of the Phase 4 creative pass, listed here since
they touch shared shell files):

**`frontend/src/components/shared/RaceLoadingBar.tsx`** (new file) — a slim
red "DRS telemetry" bar under the nav that lights up on any in-flight
TanStack Query request:

```tsx
import { useIsFetching } from '@tanstack/react-query'

export function RaceLoadingBar() {
  const isFetching = useIsFetching()
  return (
    <div className="race-loading-bar-track" aria-hidden="true">
      <div className={`race-loading-bar-fill ${isFetching ? 'is-active' : ''}`} />
    </div>
  )
}
```

**`frontend/src/components/layout/AppShell.tsx`** — one-line integration:

```tsx
import { Outlet } from 'react-router-dom'
import { TopNavigation } from '../navigation/TopNavigation'
import { ThemeProvider } from '../../features/theme/ThemeProvider'
import { RaceLoadingBar } from '../shared/RaceLoadingBar'
export function AppShell(){
  return (
    <ThemeProvider>
      <div style={{minHeight:'100vh', display:'flex', flexDirection:'column'}}>
        <TopNavigation />
        <RaceLoadingBar />
        <main style={{flex:1}}><Outlet /></main>
        <footer className="f1-footer px-4 sm:px-8 py-6 mt-8">
          <div className="flex flex-wrap items-center justify-between gap-2 fs-11">
            <span>&copy; 2026 F1 Predictor. Predictions are modelled estimates, not betting advice.</span>
            <span className="f1-mono">Season 2026 · Model v1.0</span>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  )
}
```

**`frontend/src/components/prediction/PodiumReveal.tsx`** (new file) — a
brief confetti + toast when a race prediction's top pick appears, re-firing
only when the winner actually changes:

```tsx
import { useEffect, useMemo, useState } from 'react'

const CONFETTI_COLORS = ['var(--red)', 'var(--amber)', 'var(--green)', 'var(--purple)', '#ffffff']

export function PodiumReveal({ trigger, label }: { trigger?: string; label?: string }) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (!trigger) return
    setShow(true)
    const t = setTimeout(() => setShow(false), 2200)
    return () => clearTimeout(t)
  }, [trigger])

  const pieces = useMemo(
    () =>
      Array.from({ length: 28 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.4,
        duration: 1.4 + Math.random() * 0.8,
        color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
        rotate: Math.round(Math.random() * 360),
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [trigger]
  )

  if (!show) return null

  return (
    <div className="podium-reveal" aria-live="polite">
      {pieces.map((p) => (
        <span
          key={p.id}
          className="podium-confetti"
          style={
            {
              left: `${p.left}%`,
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`,
              background: p.color,
              '--r': `${p.rotate}deg`,
            } as React.CSSProperties
          }
        />
      ))}
      {label && <div className="podium-reveal-label f1-display">🏆 {label} — predicted P1</div>}
    </div>
  )
}
```

**`frontend/src/components/prediction/PredictionResults.tsx`** — wire it in:

```tsx
import { PodiumReveal } from './PodiumReveal'
export function PredictionResults({result}:{result:any}){
  if(!result) return <div className="empty-state p-8 text-center text-muted">No prediction yet — select a race and run the engine.</div>
  const targets = Object.keys(result.predictions||{})
  const topDriver = targets[0] ? result.predictions[targets[0]]?.predictions?.[0]?.driver_code : undefined
  return (
    <div className="space-y-4">
      {topDriver && (
        <PodiumReveal trigger={`${result.race_id}-${result.session_type}-${topDriver}`} label={topDriver} />
      )}
      {targets.map(tid=>{
        const summary=result.predictions[tid]
        return (
          <div key={tid} className="card p-4">
            <div className="f1-display font-bold">{summary.target_label} <span className="fs-11 text-sub">· confidence {(summary.confidence*100).toFixed(1)}%</span></div>
            <div className="f1-table mt-3">
              <div className="overflow-x-auto">
                <table className="f1-table w-full">
                  <thead><tr><th>#</th><th>Driver</th><th>Prob</th><th>%</th></tr></thead>
                  <tbody>
                    {summary.predictions.slice(0,12).map((p:any,i:number)=>
                      <tr key={p.driver_code}><td className="f1-mono">{i+1}</td><td className="font-semibold">{p.driver_code}</td><td className="f1-mono">{p.probability.toFixed(4)}</td><td>{p.percentage.toFixed(2)}%</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
```

**Verified:** `cd frontend && npm install && npm run build` — 123 modules,
no TypeScript errors, `dist/assets/index-*.js` ≈ 448 KB (≈147 KB gzip).

### Optional next step — port the homepage's visual assets

The rebuilt Home page above deliberately uses **zero image/video assets**
(pure CSS gradients + the checkerboard trick), so it works immediately with
no extra steps. If you want the same photographic/video richness as the
original `homepage.html` (hero video, driver photos, circuit shots):

```bash
mkdir -p frontend/public/media
cp dashboard/static/img/*.png dashboard/static/img/*.jpg frontend/public/media/
cp dashboard/static/videos/*.mp4 frontend/public/media/
```

Anything under `frontend/public/` is served at the site root by Vite — so
`frontend/public/media/f1_cartoon.png` becomes `/media/f1_cartoon.png`, no
backend dependency. Deliberately **don't** point the React app at
`dashboard/static/...` for these assets — the frontend and backend are meant
to deploy independently (Phase 3), and `frontend/nginx.conf` / the Vercel
rewrites below don't proxy `/static/*`.

---

## Phase 3 — Deployment readiness (Vercel + free hosting)

### Reality check

`requirements.txt` pulls in `fastf1`, `pandas`, `scipy`, `scikit-learn`,
`xgboost`, `lightgbm`, `weasyprint` (native Cairo/Pango bindings),
`prometheus_client`, and runs a background live-updater thread
(`data/live_updater.py`, started in `main.py`). None of that fits Vercel's
Python serverless functions: they're stateless per-invocation (no background
threads survive between requests), have hard package-size limits that
`scikit-learn`+`xgboost`+`lightgbm`+`fastf1` alone can blow through, and
short execution-time limits that a several-thousand-run Monte Carlo can
exceed. This isn't a configuration problem — it's a structural mismatch. Any
plan that says "just deploy the whole thing to Vercel" would be setting you
up to fail after the fact, so the honest recommendation is a split
topology, which is also exactly what `docker-compose.yml` already assumes
(separate `backend` and `frontend` services).

### Recommended topology

```
                    ┌──────────────────────┐
   Browser  ───────▶│   Vercel (frontend)  │   React static build
                    │   f1-predictor.vercel.app
                    └──────────┬───────────┘
                               │ rewrites /api,/dashboard,/standings,… (same-origin, no CORS)
                               ▼
                    ┌──────────────────────┐
                    │  Render (backend)    │   Flask + engine, from your existing Dockerfile
                    │  f1-predictor-backend.onrender.com
                    └──────────┬───────────┘
                               │ optional
                     ┌─────────┴─────────┐
                     ▼                   ▼
             Upstash Redis        Neon / Supabase Postgres
             (free tier)          (free tier, for persistence)
```

Why Render for the backend: it deploys your existing `Dockerfile` as-is
(unlike Vercel/Netlify functions), free-tier web services run as a normal
long-lived process (background threads work), and it has no per-function
package-size ceiling. The trade-off: the free plan spins the service down
after ~15 minutes idle, so the first request after a quiet spell has a
~30–50s cold start — acceptable for a portfolio/demo project, worth knowing
about. Railway and Fly.io are equally viable alternatives with the same
Docker-first model if you'd rather use one of those.

### Data & cache on a free tier

- **Redis is optional.** `cache/redis.py` already does a TCP probe before
  connecting and falls back to an in-memory `DictCache` if Redis is
  unreachable — so you can deploy the backend with zero Redis configuration
  and it'll just work (cache resets on each cold start/restart, which is a
  fine trade-off for a free deployment). If you do want a persistent cache,
  Upstash's free Redis tier works, but `RedisCache._connect()` only supports
  plain `host`/`port`/`password` — Upstash requires TLS. Small patch if you
  want this:
  ```python
  # cache/redis.py, inside RedisCache._connect(), replacing the redis.Redis(...) call:
  self.client = redis.Redis(
      host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB,
      password=settings.REDIS_PASSWORD, decode_responses=True,
      socket_connect_timeout=3, socket_timeout=3,
      ssl=settings.REDIS_TLS,  # add REDIS_TLS: bool = False to Settings
  )
  ```
- **SQLite won't persist on Render's free tier** — there's no disk between
  deploys/restarts on the free plan. If predictions/accuracy history need to
  survive restarts, point `DATABASE_URL` at a free hosted Postgres (Neon or
  Supabase both have generous free tiers) — `database/client.py` already
  takes `DATABASE_URL` from settings, so this is a pure env-var change, no
  code change needed.

### Config files (new)

**`frontend/vercel.json`** — static build + same-origin API proxy (no CORS
needed) + SPA fallback. Replace `YOUR-BACKEND-HOST.example.com` with your
actual Render URL once deployed:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://YOUR-BACKEND-HOST.example.com/api/$1" },
    { "source": "/dashboard/(.*)", "destination": "https://YOUR-BACKEND-HOST.example.com/dashboard/$1" },
    { "source": "/standings/(.*)", "destination": "https://YOUR-BACKEND-HOST.example.com/standings/$1" },
    { "source": "/h2h/(.*)", "destination": "https://YOUR-BACKEND-HOST.example.com/h2h/$1" },
    { "source": "/constructors/(.*)", "destination": "https://YOUR-BACKEND-HOST.example.com/constructors/$1" },
    { "source": "/analytics/(.*)", "destination": "https://YOUR-BACKEND-HOST.example.com/analytics/$1" },
    { "source": "/reports/(.*)", "destination": "https://YOUR-BACKEND-HOST.example.com/reports/$1" },
    { "source": "/health", "destination": "https://YOUR-BACKEND-HOST.example.com/health" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Rewrites are evaluated top-to-bottom — the SPA fallback (`/(.*)` →
`/index.html`) has to stay last, or it'll swallow the API rewrites above it.

*Alternative (Option B), if you'd rather not maintain rewrites:* leave
`vercel.json` out, set `VITE_API_BASE=https://YOUR-BACKEND-HOST.onrender.com`
as a Vercel environment variable (`frontend/src/api/client.ts` already reads
`import.meta.env.VITE_API_BASE`), and rely on the `CORS_ORIGINS` setting
below instead. Simpler, but now it's a genuine cross-origin call and you're
trusting CORS instead of same-origin same-origin proxying.

**`render.yaml`** — Render Blueprint for the backend, reusing your existing
root `Dockerfile`:

```yaml
services:
  - type: web
    name: f1-predictor-backend
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    plan: free
    healthCheckPath: /health
    envVars:
      - key: FLASK_ENV
        value: production
      - key: DEBUG
        value: "false"
      - key: SECRET_KEY
        generateValue: true
      # Free-tier Render web services have no persistent disk, so SQLite
      # (the default DATABASE_URL) resets on every deploy/restart. Point
      # this at a free hosted Postgres (Neon, Supabase, or Render's own
      # Postgres) if predictions/accuracy history need to survive restarts.
      - key: DATABASE_URL
        sync: false
      # Optional — Redis is not required (see "Data & cache" above).
      - key: REDIS_HOST
        sync: false
      - key: REDIS_PORT
        sync: false
      - key: REDIS_PASSWORD
        sync: false
      # Restrict CORS to the deployed frontend once you know its domain
      # (Option B path above).
      - key: CORS_ORIGINS
        sync: false
```

### Two deploy-blockers fixed while in here

**`Dockerfile`** — WeasyPrint (`reports/pdf_generator.py`) needs Pango/Cairo
system libraries *at runtime*; they weren't installed, so PDF export would
500 on first use in any container build, including your existing
docker-compose setup:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies.
# gcc/g++: build a couple of ML wheels that don't ship manylinux binaries.
# curl: container HEALTHCHECK.
# libpango/libcairo/libgdk-pixbuf/shared-mime-info/fonts-liberation: WeasyPrint
#   (reports/pdf_generator.py) needs these at *runtime*, not just build time —
#   without them, PDF export 500s the first time anyone requests one.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directories
RUN mkdir -p cache/api_responses cache/fastf1_cache cache/model_cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
```

**`main.py`** — Render/Railway/Fly assign a port via `$PORT` at runtime and
expect the process to bind to it; there was no way to honor that short of
overriding `FLASK_PORT`, which those platforms don't let you set to match
their dynamic value:

```python
    # Run Flask app
    # Most free hosts (Render, Railway, Fly.io) assign a port at runtime via
    # $PORT and expect the process to bind to it — they don't let you set
    # FLASK_PORT to match. Prefer $PORT when present; fall back to
    # FLASK_PORT/5000 for local dev and the existing docker-compose setup.
    run_port = int(os.environ.get("PORT", settings.FLASK_PORT))
    print(f"\nStarting Flask server on {settings.FLASK_HOST}:{run_port}...")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Season: {settings.SEASON_YEAR}")
    print("=" * 60)

    try:
        app.run(
            host=settings.FLASK_HOST,
            port=run_port,
            debug=settings.DEBUG,
            use_reloader=False,  # Don't use reloader in production
        )
```
(Only the `port=` line and the `run_port` computation change — everything
else in `main()` stays as-is.)

**`dashboard/app.py`** — CORS now reads `CORS_ORIGINS` (added in Phase 1's
`config/settings.py` block above) instead of being wide open:

```python
    # Enable CORS. CORS_ORIGINS defaults to "*" (fine for local dev and the
    # docker-compose stack, where nginx/Vite proxy same-origin anyway). Set
    # it to a comma-separated allowlist in production if the frontend calls
    # this API cross-origin (Option B above).
    _cors_origins = settings.CORS_ORIGINS
    CORS(
        app,
        supports_credentials=True,
        origins=_cors_origins.split(',') if _cors_origins != '*' else '*',
    )
```

### Step-by-step

1. Push all the changes above to `main`.
2. **Backend → Render:** New → Blueprint → point at your repo → Render
   detects `render.yaml` → set `DATABASE_URL` (optional, Postgres) if you
   want persistence → Deploy. Note the resulting URL
   (`https://f1-predictor-backend.onrender.com`).
3. **Frontend → Vercel:** New Project → import the repo → set **Root
   Directory** to `frontend` → Vercel detects `vercel.json` (Vite framework
   preset) → before deploying, edit `frontend/vercel.json` and replace every
   `YOUR-BACKEND-HOST.example.com` with the Render URL from step 2 → Deploy.
4. Visit the Vercel URL. `/`, `/dashboard`, `/standings`, etc. all now load
   through the rewrite proxy — no CORS, single origin, same behavior as the
   local `nginx.conf` / Vite dev proxy setups you already had.
5. `curl https://<vercel-domain>/api/v1/races | jq 'length'` should return
   the race count, proxied through to Render.

---

## Phase 4 — Creative pass: F1-themed improvements

### Shipped now (all in Phase 2/3 blocks above — recap)

- **Hero + live next-race countdown** — genuinely useful (not just
  decorative): tells you at a glance when the next Grand Prix is, pulled
  from real race data.
- **Start lights animation** — the actual 5-red-lights F1 start sequence,
  looping in the hero.
- **Animated stat ticker** — count-up races/drivers/constructors/
  simulations, IntersectionObserver-triggered like the original homepage's
  ticker.
- **Race loading bar** — a DRS-style telemetry strip under the nav that
  lights up during any live API fetch, anywhere in the app.
- **Podium reveal confetti** — fires once per new race prediction, not on
  every re-render.
- **Feature grid + "how it works" panel** — turns the homepage into an
  actual map of the product instead of 3 bare links.
- **Reports page rewritten** with real format explanations instead of a stub.

### Roadmap — prioritized, with a starting sketch for each

**1. Team-color accents (highest value, lowest effort).** `Driver.team_color`
and `Team.color`/`color_hex` are already in your types and already coming
back from the API — they're just not used anywhere in the UI yet. A `team-bar`
CSS class already exists in `styles.css`/`legacy.css` (a 4×22px rounded bar)
but isn't wired to real data. Add a small helper and use it in the Standings
table, H2H driver cards and the prediction results table:

```tsx
// frontend/src/components/shared/TeamStripe.tsx
export function TeamStripe({ color }: { color?: string }) {
  return <span className="team-bar" style={{ background: color || 'var(--muted)' }} />
}
```
Drop `<TeamStripe color={driver.team_color} />` next to each driver code —
instantly ties every table back to real team branding with no new deps.

**2. Head-to-head "duel" radar chart.** `react-chartjs-2` is already a
dependency (`package.json`) but only used for line/bar charts so far. A
radar comparing `strength` / `wet_skill` / `consistency` / `reliability` for
the two selected drivers in `H2HPage` would visualize exactly the inputs the
Elo probability is built from — genuinely explains the number instead of
just stating it.

**3. Tire-strategy visualizer.** `engine/tire_model.py` and
`engine/pit_strategy.py` already model this server-side but nothing surfaces
it in the UI. A horizontal stacked-bar "stint plan" (compound colors: white/
yellow/red per regulation) per driver on the Dashboard would be a strong,
genuinely F1-specific visual nothing else in the roadmap covers.

**4. Share cards, made shareable.** `reports/share_card_generator.py`
already generates a share-card image server-side — the Reports page
(rewritten above) explains the format but doesn't preview it. Add an
`<img>` preview + a "Copy image" / native `navigator.share()` button once a
prediction exists, so the feature is actually discoverable instead of
existing only in the API docs.

**5. PWA / installable app.** Vite has an official `vite-plugin-pwa`. Given
the countdown/hero already lean on "next race" as a hook, a home-screen icon
+ offline-cached shell (predictions still need network, but standings/
calendar could cache) is a natural fit and free to host — the manifest and
service worker are just static files Vercel serves like anything else.

**6. Race-weekend live ticker (bigger lift).** `data/live_updater.py`
already polls in the background on the Flask side. Wiring a WebSocket
(Flask-SocketIO, or Server-Sent Events for something lighter) so the React
dashboard gets pushed updates during a live weekend instead of polling would
be the single biggest "wow" feature — but it's real backend work and a
genuinely different deployment shape (Render's free web service supports
long-lived connections, Vercel serverless would not), so treat it as a
separate project once the rest of this is stable.

**7. Grid-walk parallax on the homepage.** If you do the "port the visual
assets" step from Phase 2, a slow parallax scroll through 4–5 of the
existing driver/circuit images (same images the legacy `homepage.html`
already has) between the feature grid and "how it works" sections would
close the remaining visual gap with the original cinematic homepage without
needing the custom-cursor/lightbox machinery that made it 2,000+ lines.

---

## File-by-file change log

| File | Status | What changed |
|---|---|---|
| `config/settings.py` | Modified | Fixed `SECURITY_HEADERS['Content-Security-Policy']` (Phase 1); added `CORS_ORIGINS` field (Phase 3) |
| `dashboard/app.py` | Modified | `CORS(...)` now reads `settings.CORS_ORIGINS` instead of always `*` |
| `Dockerfile` | Modified | Added WeasyPrint runtime system libraries |
| `main.py` | Modified | Binds to `$PORT` when set, falls back to `FLASK_PORT` |
| `frontend/src/pages/Home/index.tsx` | Rewritten | 17 lines → full hero/countdown/ticker/feature-grid homepage |
| `frontend/src/pages/Reports/index.tsx` | Rewritten | 1-line stub → real format explanations + link to Dashboard |
| `frontend/src/hooks/useCountUp.ts` | New | Count-up animation hook for the stat ticker |
| `frontend/src/components/home/StartLights.tsx` | New | F1 start-lights hero animation |
| `frontend/src/components/home/NextRaceCountdown.tsx` | New | Live countdown to next race, real API data |
| `frontend/src/components/shared/RaceLoadingBar.tsx` | New | Global DRS-style fetch indicator |
| `frontend/src/components/prediction/PodiumReveal.tsx` | New | Confetti celebration on new race prediction |
| `frontend/src/components/layout/AppShell.tsx` | Modified | Mounts `<RaceLoadingBar />` |
| `frontend/src/components/prediction/PredictionResults.tsx` | Modified | Mounts `<PodiumReveal />` on new results |
| `frontend/src/styles/globals.css` | Modified (append-only) | CSS for all of the above — nothing existing touched |
| `frontend/vercel.json` | New | Vercel build config + API rewrite proxy |
| `render.yaml` | New | Render Blueprint for the backend |
| `frontend/src/components/shared/TeamStripe.tsx` | Roadmap (not yet created) | See Phase 4, item 1 |

---

## Verification performed

- `python3 -m py_compile config/settings.py dashboard/app.py main.py` — clean.
- `python3 -c "from config.settings import settings; print(settings.SECURITY_HEADERS[...])"` — new CSP loads and renders correctly.
- `cd frontend && npm install && npm run build` — passes after every change
  above (Home rewrite, new components, AppShell/PredictionResults wiring,
  Reports rewrite): 123 modules transformed, 0 TypeScript errors,
  `dist/assets/index-*.js` ≈ 448 KB / 147 KB gzip.
- Not run in this environment (needs the full ML/Flask dependency stack and
  a live Redis/DB, outside what this sandbox can install quickly): an actual
  `python main.py` boot, Docker build, or Render/Vercel deploy. Treat those
  as your final check before considering this done — the fixes above are
  verified at the source/build level, not end-to-end in a browser.

---

## Next steps checklist

- [ ] Paste the `config/settings.py`, `dashboard/app.py`, `Dockerfile`,
      `main.py` changes into your repo, redeploy locally, confirm port 5000
      renders styled.
- [ ] Paste the Phase 2 frontend files in, `npm run build`, confirm port
      5173 (or `npm run preview`) shows the new homepage.
- [ ] Decide: quick CSP allowlist (already applied) vs. the Phase 1
      follow-up (self-hosted assets, tighter CSP) — the follow-up is
      recommended before a public launch but not blocking.
- [ ] Add `frontend/vercel.json` and `render.yaml`, deploy backend to
      Render first, then frontend to Vercel with the real backend URL filled
      in.
- [ ] Decide on `DATABASE_URL` (ephemeral SQLite vs. free Postgres) based on
      whether you need prediction history to survive restarts.
- [ ] Pick 1–2 items from the Phase 4 roadmap — team-color accents (#1) is
      the best effort-to-payoff ratio to start with.