// Single typed shape for every user-controllable, locally-persisted preference in the app.
// This replaces the previously scattered localStorage keys (f1-theme, f1-settings-colors,
// f1-settings-cache, f1-dashboard-mods, f1-ai-mode, f1-ai-model, f1-ai-weight,
// f1-ai-temperature) with one coherent, versioned object so Settings, the Dashboard,
// the nav, and every page read/write the same source of truth.

export type ThemeMode = 'light' | 'dark' | 'system'
export type Density = 'comfortable' | 'compact'
export type DataUsageMode = 'full' | 'reduced'

export interface AppearancePrefs {
  themeMode: ThemeMode
  accent: string
  background: string
  surface: string
  surfaceAlt: string
  border: string
  text: string
  sub: string
  fontScale: number // 0.9 - 1.25
  radius: number // 0 - 20 (px)
  density: Density
}

export interface AccessibilityPrefs {
  reducedMotion: boolean
  highContrast: boolean
  dyslexiaFont: boolean
  underlineLinks: boolean
}

export interface EngineDefaults {
  simulationCount: number
  chaosLevel: number
  gridWeight: number
  wetInfluence: number
  reliabilityInfluence: number
  strategyAggressiveness: number
  safetyCarWeight: number
}

// These exist in the backend's Settings model and ARE admin-gated but ARE real
// server-side config (cache TTL, data source priority, etc.) — kept distinct from
// EngineDefaults (which are real, per-request, unauthenticated, and always honoured
// by the live prediction engine) so the UI can be honest about which tier each is in.
export interface BackendAdvanced {
  cacheTtlSeconds: number
  dataSourcePriority: 'jolpica' | 'openf1' | 'fastf1' | 'fallback'
  liveUpdateInterval: number
  modelType: 'ml' | 'dl' | 'ensemble'
}

export interface DashboardLayoutPrefs {
  visiblePanels: Record<string, boolean>
  defaultRoute: string
  compactTables: boolean
}

export interface NotificationPrefs {
  raceReminders: boolean
  reminderMinutesBefore: number
}

export interface AdvancedPrefs {
  apiBaseOverride: string
  requestTimeoutMs: number
  debugLogging: boolean
  keyboardShortcuts: boolean
  reduceDataUsage: boolean
  adminToken: string // session-only, never persisted to localStorage — see store.ts
}

export interface ProfilePrefs {
  displayName: string
  favoriteDriverCode: string
  favoriteTeam: string
}

export interface Preferences {
  version: 3
  appearance: AppearancePrefs
  accessibility: AccessibilityPrefs
  engine: EngineDefaults
  backendAdvanced: BackendAdvanced
  dashboardLayout: DashboardLayoutPrefs
  notifications: NotificationPrefs
  advanced: Omit<AdvancedPrefs, 'adminToken'>
  profile: ProfilePrefs
}

export const DEFAULT_PREFERENCES: Preferences = {
  version: 3,
  appearance: {
    themeMode: 'system',
    accent: '#E10600',
    background: '#F4F5F7',
    surface: '#FFFFFF',
    surfaceAlt: '#EEF0F3',
    border: '#E3E5EA',
    text: '#15151E',
    sub: '#6B7280',
    fontScale: 1,
    radius: 12,
    density: 'comfortable',
  },
  accessibility: {
    reducedMotion: false,
    highContrast: false,
    dyslexiaFont: false,
    underlineLinks: false,
  },
  engine: {
    simulationCount: 10000,
    chaosLevel: 50,
    gridWeight: 55,
    wetInfluence: 60,
    reliabilityInfluence: 40,
    strategyAggressiveness: 50,
    safetyCarWeight: 30,
  },
  backendAdvanced: {
    cacheTtlSeconds: 300,
    dataSourcePriority: 'jolpica',
    liveUpdateInterval: 300,
    modelType: 'ensemble',
  },
  dashboardLayout: {
    visiblePanels: {},
    defaultRoute: '/',
    compactTables: false,
  },
  notifications: {
    raceReminders: false,
    reminderMinutesBefore: 60,
  },
  advanced: {
    apiBaseOverride: '',
    requestTimeoutMs: 20000,
    debugLogging: false,
    keyboardShortcuts: true,
    reduceDataUsage: false,
  },
  profile: {
    displayName: '',
    favoriteDriverCode: '',
    favoriteTeam: '',
  },
}

export const DARK_ACCENT_PRESET = {
  accent: '#FF3B30', background: '#0A0C10', surface: '#15181F',
  surfaceAlt: '#1C2028', border: '#2B3039', text: '#F1F2F5', sub: '#9BA2AF',
}
export const LIGHT_ACCENT_PRESET = {
  accent: '#E10600', background: '#F4F5F7', surface: '#FFFFFF',
  surfaceAlt: '#EEF0F3', border: '#E3E5EA', text: '#15151E', sub: '#6B7280',
}
