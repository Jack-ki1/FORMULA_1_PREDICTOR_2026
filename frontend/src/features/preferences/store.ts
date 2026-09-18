import { create } from '../../stores/create'
import { DEFAULT_PREFERENCES, DARK_ACCENT_PRESET, LIGHT_ACCENT_PRESET } from './types'
import type { Preferences, ThemeMode } from './types'

const STORAGE_KEY = 'f1-preferences-v3'
const ADMIN_TOKEN_KEY = 'f1-admin-token' // sessionStorage only — never written to the persisted profile

function deepMerge<T>(base: T, patch: any): T {
  if (!patch || typeof patch !== 'object') return base
  const out: any = Array.isArray(base) ? [...(base as any)] : { ...(base as any) }
  for (const k of Object.keys(patch)) {
    const bv = (base as any)?.[k]
    const pv = patch[k]
    if (pv && typeof pv === 'object' && !Array.isArray(pv) && bv && typeof bv === 'object') {
      out[k] = deepMerge(bv, pv)
    } else if (pv !== undefined) {
      out[k] = pv
    }
  }
  return out
}

function migrateLegacyKeys(): Partial<Preferences> {
  // Best-effort import of the pre-v3 scattered keys so nobody loses their setup
  // the first time they load the redesigned app.
  const patch: any = {}
  try {
    const theme = localStorage.getItem('f1-theme')
    if (theme === 'dark' || theme === 'light') patch.appearance = { themeMode: theme }
  } catch { /* noop */ }
  try {
    const colors = JSON.parse(localStorage.getItem('f1-settings-colors') || '{}')
    if (Object.keys(colors).length) {
      patch.appearance = {
        ...(patch.appearance || {}),
        accent: colors.PRIMARY_COLOR ?? undefined,
        background: colors.BACKGROUND ?? undefined,
        surface: colors.SURFACE ?? undefined,
        surfaceAlt: colors.SURFACE_ALT ?? undefined,
        border: colors.BORDER ?? undefined,
        text: colors.TEXT ?? undefined,
        sub: colors.SUB ?? undefined,
      }
    }
  } catch { /* noop */ }
  try {
    const cached = JSON.parse(localStorage.getItem('f1-settings-cache') || '{}')
    if (cached && typeof cached === 'object') {
      const e: any = {}
      if (cached.MONTE_CARLO_SIMULATIONS != null) e.simulationCount = cached.MONTE_CARLO_SIMULATIONS
      if (cached.CHAOS_LEVEL_DEFAULT != null) e.chaosLevel = cached.CHAOS_LEVEL_DEFAULT
      if (cached.GRID_WEIGHT_DEFAULT != null) e.gridWeight = cached.GRID_WEIGHT_DEFAULT
      if (cached.WET_INFLUENCE_DEFAULT != null) e.wetInfluence = cached.WET_INFLUENCE_DEFAULT
      if (cached.RELIABILITY_INFLUENCE_DEFAULT != null) e.reliabilityInfluence = cached.RELIABILITY_INFLUENCE_DEFAULT
      if (cached.STRATEGY_AGGRESSIVENESS_DEFAULT != null) e.strategyAggressiveness = cached.STRATEGY_AGGRESSIVENESS_DEFAULT
      if (Object.keys(e).length) patch.engine = e
      const b: any = {}
      if (cached.CACHE_TTL_SECONDS != null) b.cacheTtlSeconds = cached.CACHE_TTL_SECONDS
      if (cached.DATA_SOURCE_PRIORITY != null) b.dataSourcePriority = cached.DATA_SOURCE_PRIORITY
      if (cached.LIVE_UPDATE_INTERVAL != null) b.liveUpdateInterval = cached.LIVE_UPDATE_INTERVAL
      if (cached.MODEL_TYPE != null) b.modelType = cached.MODEL_TYPE
      if (Object.keys(b).length) patch.backendAdvanced = b
    }
  } catch { /* noop */ }
  try {
    const mods = JSON.parse(localStorage.getItem('f1-dashboard-mods') || '{}')
    if (mods && typeof mods === 'object') {
      const e: any = {}
      if (mods.chaos != null) e.chaosLevel = mods.chaos
      if (mods.gridWeight != null) e.gridWeight = mods.gridWeight
      if (mods.wetInfluence != null) e.wetInfluence = mods.wetInfluence
      if (mods.reliability != null) e.reliabilityInfluence = mods.reliability
      if (mods.strategy != null) e.strategyAggressiveness = mods.strategy
      if (mods.safetyCar != null) e.safetyCarWeight = mods.safetyCar
      if (Object.keys(e).length) patch.engine = { ...(patch.engine || {}), ...e }
    }
  } catch { /* noop */ }
  return patch
}

function load(): Preferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return deepMerge(DEFAULT_PREFERENCES, JSON.parse(raw))
  } catch { /* noop */ }
  // First run under the new schema — pull forward anything from the old keys.
  const legacy = migrateLegacyKeys()
  return deepMerge(DEFAULT_PREFERENCES, legacy)
}

function persist(prefs: Preferences) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs)) } catch { /* noop */ }
}

export function resolveThemeMode(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') {
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return mode
}

/** Applies appearance + accessibility preferences to the document. Single place that
 *  touches document.documentElement, replacing the old dual ThemeProvider/Settings
 *  inline-style conflict. */
export function applyPreferencesToDocument(prefs: Preferences) {
  const root = document.documentElement
  const resolved = resolveThemeMode(prefs.appearance.themeMode)
  root.setAttribute('data-theme', resolved)
  root.style.setProperty('--red', prefs.appearance.accent)
  root.style.setProperty('--bg', prefs.appearance.background)
  root.style.setProperty('--surface', prefs.appearance.surface)
  root.style.setProperty('--surface-alt', prefs.appearance.surfaceAlt)
  root.style.setProperty('--border', prefs.appearance.border)
  root.style.setProperty('--text', prefs.appearance.text)
  root.style.setProperty('--sub', prefs.appearance.sub)
  const c = prefs.appearance.accent
  if (c?.startsWith('#') && c.length === 7) {
    const r = parseInt(c.slice(1, 3), 16), g = parseInt(c.slice(3, 5), 16), b = parseInt(c.slice(5, 7), 16)
    root.style.setProperty('--red-dark', `rgb(${Math.max(0, r - 40)},${Math.max(0, g - 10)},${Math.max(0, b - 10)})`)
  }
  root.style.setProperty('--font-scale', String(prefs.appearance.fontScale))
  root.style.setProperty('--radius-base', `${prefs.appearance.radius}px`)
  root.setAttribute('data-density', prefs.appearance.density)
  root.setAttribute('data-reduced-motion', String(prefs.accessibility.reducedMotion))
  root.setAttribute('data-high-contrast', String(prefs.accessibility.highContrast))
  root.setAttribute('data-dyslexia-font', String(prefs.accessibility.dyslexiaFont))
  root.setAttribute('data-underline-links', String(prefs.accessibility.underlineLinks))
  root.setAttribute('data-reduce-data', String(prefs.advanced.reduceDataUsage))
}

type Store = {
  prefs: Preferences
  hydrated: boolean
  set: (patch: any) => void
  setAppearance: (patch: Partial<Preferences['appearance']>) => void
  applyAccentPreset: (which: 'light' | 'dark') => void
  reset: (section?: keyof Preferences) => void
  exportJson: () => string
  importJson: (json: string) => { ok: boolean; error?: string }
}

const initial = load()
if (typeof document !== 'undefined') applyPreferencesToDocument(initial)

export const usePreferences = (create as any)((set: any, get: () => Store) => {
  // Keep "system" theme in sync with OS-level changes while the tab is open.
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => {
      const s = get()
      if (s.prefs.appearance.themeMode === 'system') applyPreferencesToDocument(s.prefs)
    }
    mq.addEventListener?.('change', onChange)
  }

  return {
    prefs: initial,
    hydrated: true,
    set: (patch: any) => {
      const next = deepMerge(get().prefs, patch)
      persist(next)
      applyPreferencesToDocument(next)
      set({ prefs: next })
    },
    setAppearance: (patch: any) => get().set({ appearance: patch }),
    applyAccentPreset: (which: 'light' | 'dark') => {
      const preset = which === 'dark' ? DARK_ACCENT_PRESET : LIGHT_ACCENT_PRESET
      get().set({ appearance: { ...preset, themeMode: which } })
    },
    reset: (section?: keyof Preferences) => {
      if (!section) {
        persist(DEFAULT_PREFERENCES)
        applyPreferencesToDocument(DEFAULT_PREFERENCES)
        set({ prefs: DEFAULT_PREFERENCES })
        return
      }
      const next = { ...get().prefs, [section]: (DEFAULT_PREFERENCES as any)[section] }
      persist(next)
      applyPreferencesToDocument(next)
      set({ prefs: next })
    },
    exportJson: () => JSON.stringify(get().prefs, null, 2),
    importJson: (json: string) => {
      try {
        const parsed = JSON.parse(json)
        const next = deepMerge(DEFAULT_PREFERENCES, parsed)
        persist(next)
        applyPreferencesToDocument(next)
        set({ prefs: next })
        return { ok: true }
      } catch (e: any) {
        return { ok: false, error: e?.message || 'Invalid JSON' }
      }
    },
  }
})

// Admin token deliberately lives in sessionStorage (not the persisted preferences
// object): it's a bearer credential for the backend's admin-only settings fields,
// not a UI preference, and shouldn't survive being synced/exported/shared via
// "export settings as JSON".
export const adminToken = {
  get: (): string => { try { return sessionStorage.getItem(ADMIN_TOKEN_KEY) || '' } catch { return '' } },
  set: (token: string) => { try { token ? sessionStorage.setItem(ADMIN_TOKEN_KEY, token) : sessionStorage.removeItem(ADMIN_TOKEN_KEY) } catch { /* noop */ } },
}
