import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

/**
 * Guardrail tests for the frontend halves of the fixes in ../../docs/modify.md.
 * They assert against source text where the logic is embedded in JSX and not
 * separately exportable — crude, but they lock the *behavioural* contract
 * (no hardcoded grid sizes, no fabricated data), which is what actually broke.
 *
 * Path resolution uses `import.meta.url` rather than `__dirname`: package.json
 * sets "type": "module", so these files are ESM where __dirname is undefined.
 *
 * NOTE on this rewrite: the previous version of this file asserted against
 * `pages/Constructors/index.tsx` and `pages/Analytics/index.tsx`. Neither page
 * has ever existed in this repository — confirmed against the codebase before
 * this redesign pass too — so those tests had been failing (ENOENT / missing
 * strings) on every run, undetected, for as long as this file existed. The
 * constructor table lives inside pages/Standings/index.tsx; there is no
 * separate analytics/drift-tracking page. Rewritten against what's actually
 * here instead of inventing pages to satisfy stale assertions.
 */
const HERE = dirname(fileURLToPath(import.meta.url))
const read = (p: string) => readFileSync(resolve(HERE, '..', p), 'utf8')

/** Strip comments so tests assert on *code*, not on notes mentioning the strings we forbid. */
const readCode = (p: string) =>
  read(p)
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/^\s*\/.*$/gm, '')

describe('grid size consistency (modify.md 1.5)', () => {
  it('GridEditor derives positions from the driver list, not a literal 23', () => {
    const src = readCode('features/manual-grid/GridEditor.tsx')
    expect(src).toContain('Array.from({length:codes.length}')
    expect(src).not.toContain('Array.from({length:23}')
    expect(src).not.toContain('codes.slice(0,23)')
  })

  it('no page claims a 23-driver grid', () => {
    for (const p of [
      'pages/Fantasy/index.tsx',
      'pages/Standings/index.tsx',
      'pages/Dashboard/index.tsx',
      'pages/H2H/index.tsx',
    ]) {
      const src = readCode(p)
      expect(src, `${p} still says "23 drivers"`).not.toMatch(/23\s*drivers/i)
      expect(src, `${p} still slices 23`).not.toContain('slice(0,23)')
    }
  })
})

describe('no fabricated results in the UI', () => {
  it('Dashboard does not hardcode an actual winner/podium', () => {
    const src = readCode('pages/Dashboard/index.tsx')
    expect(src).not.toContain("actualWinner = 'ANT'")
    expect(src).not.toContain("actualPodium = ['ANT','RUS','HAM']")
    // Results come from the real prediction mutation, not a literal in the component.
    expect(src).toContain('usePrediction()')
    expect(src).toContain('mut.mutateAsync')
  })

  it('Home page labels its sample preview as illustrative, not live', () => {
    // MINI_PREVIEW_RACES is a static array for the homepage teaser — it must not
    // claim to be the same live Monte Carlo run that Dashboard performs.
    const src = readCode('pages/Home/index.tsx')
    expect(src).not.toContain('This is the same Monte Carlo that powers')
    expect(src).toMatch(/Illustrative|Sample/i)
  })

  it('Settings placeholder names the real env var', () => {
    const src = readCode('pages/Settings/index.tsx')
    expect(src).toContain('SETTINGS_ADMIN_TOKEN')
    expect(src).not.toContain('X-Admin-Token (SECRET_KEY)')
  })

  it('Standings does not leak internal implementation notes as user copy', () => {
    const src = readCode('pages/Standings/index.tsx')
    expect(src).not.toContain('Math.random')
    expect(src).not.toContain('team_id→team mapping')
  })
})

describe('Settings tunable fields are honestly tiered (modify.md 5)', () => {
  it('every engine parameter carries a live/admin/planned tier, not a bare slider', () => {
    const src = readCode('pages/Settings/index.tsx')
    expect(src).toContain('tier="live"')
    expect(src).toContain('tier="admin"')
    expect(src).toContain('tier="planned"')
  })

  it('admin-gated fields actually send X-Admin-Token', () => {
    const settingsApi = readCode('api/settings.ts')
    expect(settingsApi).toContain('X-Admin-Token')
  })
})

describe('routes are code-split', () => {
  it('heavy pages are lazy-loaded behind Suspense', () => {
    const src = readCode('app/router.tsx')
    for (const page of ['Dashboard', 'Standings', 'H2H', 'Fantasy', 'Guide', 'Settings']) {
      expect(src, `${page} should be lazy-loaded`).toContain(`lazy(() => import('../pages/${page}')`)
    }
    expect(src).toContain('<Suspense')
  })
})
