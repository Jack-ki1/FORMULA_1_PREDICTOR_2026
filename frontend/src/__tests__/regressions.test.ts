import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

/**
 * Guardrail tests for the frontend halves of the fixes in modify.md.
 * They assert against source text where the logic is embedded in JSX and not
 * separately exportable — crude, but they lock the *behavioural* contract
 * (no hardcoded grid sizes, no fabricated data), which is what actually broke.
 *
 * Path resolution uses `import.meta.url` rather than `__dirname`: package.json
 * sets "type": "module", so these files are ESM where __dirname is undefined.
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
      'pages/Constructors/index.tsx',
      'pages/Fantasy/index.tsx',
      'pages/Standings/index.tsx',
      'pages/Analytics/index.tsx',
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
    expect(src).toContain('/api/v1/predictions/history/last')
  })

  it('Analytics has no hardcoded drift numbers', () => {
    const src = readCode('pages/Analytics/index.tsx')
    expect(src).not.toContain('driftMock')
    expect(src).not.toContain('observed:0.55')
    expect(src).toContain('model_accuracy')
  })

  it('Settings placeholder names the real env var', () => {
    const src = readCode('pages/Settings/index.tsx')
    expect(src).toContain('SETTINGS_ADMIN_TOKEN')
    expect(src).not.toContain('X-Admin-Token (SECRET_KEY)')
  })
})

describe('typecheck-level fixes (modify.md 1.1)', () => {
  it('Settings uses the lowercase webkitTextSizeAdjust', () => {
    const src = readCode('pages/Settings/index.tsx')
    expect(src).not.toContain('webKitTextSizeAdjust')
    expect(src).toContain('webkitTextSizeAdjust')
  })

  it('Constructors has no dead nullish fallback', () => {
    const src = readCode('pages/Constructors/index.tsx')
    expect(src).not.toContain("det.wins*3 ?? '—'")
  })
})

describe('routes are code-split', () => {
  it('heavy pages are lazy-loaded behind Suspense', () => {
    const src = readCode('app/router.tsx')
    expect(src).toContain("lazy(() => import('../pages/Dashboard')")
    expect(src).toContain("lazy(() => import('../pages/Analytics')")
    expect(src).toContain('<Suspense')
  })
})
