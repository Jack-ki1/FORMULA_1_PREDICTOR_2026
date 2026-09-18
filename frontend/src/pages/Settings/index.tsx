import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { usePreferences, adminToken as adminTokenStore } from '../../features/preferences/store'
import { settingsApi } from '../../api/settings'
import { requestNotificationPermission } from '../../features/notifications/useRaceReminders'
import { Icon } from '../../components/icons/Icon'
import type { IconName } from '../../components/icons/Icon'
import { SectionHeader, SettingRow, Switch, RangeControl, ColorControl } from './controls'

const NAV: { id: string; label: string; icon: IconName }[] = [
  { id: 'appearance', label: 'Appearance', icon: 'palette' },
  { id: 'accessibility', label: 'Accessibility', icon: 'accessibility' },
  { id: 'engine', label: 'Prediction Engine', icon: 'engine' },
  { id: 'backend', label: 'Backend Config', icon: 'database' },
  { id: 'reference', label: 'Reference Params', icon: 'sliders' },
  { id: 'layout', label: 'Dashboard Layout', icon: 'layout' },
  { id: 'notifications', label: 'Notifications', icon: 'bell' },
  { id: 'profile', label: 'Profile', icon: 'user' },
  { id: 'advanced', label: 'Advanced', icon: 'shield' },
  { id: 'shortcuts', label: 'Keyboard Shortcuts', icon: 'keyboard' },
  { id: 'data', label: 'Data & Privacy', icon: 'trash' },
]

function useSectionScroll() {
  const [active, setActive] = useState('appearance')
  const goTo = (id: string) => {
    setActive(id)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  useEffect(() => {
    if (location.hash) {
      const id = location.hash.replace('#', '')
      setTimeout(() => { document.getElementById(id)?.scrollIntoView({ block: 'start' }); setActive(id) }, 50)
    }
  }, [])
  return { active, goTo }
}

export function SettingsPage() {
  const prefs = usePreferences((s: any) => s.prefs)
  const set = usePreferences((s: any) => s.set)
  const setAppearance = usePreferences((s: any) => s.setAppearance)
  const applyAccentPreset = usePreferences((s: any) => s.applyAccentPreset)
  const reset = usePreferences((s: any) => s.reset)
  const exportJson = usePreferences((s: any) => s.exportJson)
  const importJson = usePreferences((s: any) => s.importJson)
  const { active, goTo } = useSectionScroll()

  const [tokenInput, setTokenInput] = useState(() => adminTokenStore.get())
  const [tokenStatus, setTokenStatus] = useState<'idle' | 'checking' | 'ok' | 'bad'>('idle')
  const [importError, setImportError] = useState('')
  const [savedFlash, setSavedFlash] = useState('')

  const serverSettings = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.get(),
    staleTime: 30_000,
    retry: 0,
  })

  const server = (k: string) => serverSettings.data?.settings?.[k]

  const flash = (msg: string) => { setSavedFlash(msg); setTimeout(() => setSavedFlash(''), 2200) }

  const saveSafePrefs = async (body: Record<string, any>) => {
    try {
      await settingsApi.patch(body)
      flash('Saved to this browser and synced to the backend.')
    } catch {
      flash('Saved to this browser. (Backend sync failed — it may be offline; your setting still applies here.)')
    }
  }

  const testAdminToken = async () => {
    setTokenStatus('checking')
    adminTokenStore.set(tokenInput)
    try {
      const current = server('CACHE_TTL_SECONDS') ?? prefs.backendAdvanced.cacheTtlSeconds
      await settingsApi.patch({ CACHE_TTL_SECONDS: current }, tokenInput)
      setTokenStatus('ok')
      serverSettings.refetch()
    } catch {
      setTokenStatus('bad')
    }
  }

  const saveBackendField = async (key: string, value: any) => {
    try {
      await settingsApi.patch({ [key]: value }, adminTokenStore.get())
      flash(`${key} saved to the backend.`)
      serverSettings.refetch()
    } catch (e: any) {
      flash(e?.code === 'ADMIN_DISABLED'
        ? 'Backend has no SETTINGS_ADMIN_TOKEN configured — this field cannot be changed remotely until it does.'
        : 'Admin token missing or incorrect — open Advanced > Admin Access.')
    }
  }

  const handleExport = () => {
    const blob = new Blob([exportJson()], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'f1-predictor-settings.json'; a.click()
    setTimeout(() => URL.revokeObjectURL(url), 3000)
  }

  const handleImportFile = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      const res = importJson(String(reader.result || ''))
      if (!res.ok) setImportError(res.error || 'Invalid file')
      else { setImportError(''); flash('Settings imported.') }
    }
    reader.readAsText(file)
  }

  const clearLocalCache = () => {
    if (!confirm('Clear cached predictions and dashboard state stored in this browser? Your Settings preferences are kept.')) return
    ;['f1-last-prediction', 'f1-dashboard-mods', 'f1-reminder-fired'].forEach(k => { try { localStorage.removeItem(k) } catch { /* noop */ } })
    flash('Local cache cleared.')
  }

  return (
    <div className="px-4 sm:px-8 py-6">
      <div className="mb-6">
        <h1 className="f1-display text-2xl font-black">Settings</h1>
        <p className="fs-11 text-sub mt-1 max-w-2xl">
          Every control here is either <span className="badge badge-live" style={{ display: 'inline-flex' }}>Live</span> — genuinely changes what you see or what the prediction engine does right now — or clearly marked when it isn't yet. Nothing here is decorative without saying so.
        </p>
      </div>

      {savedFlash && (
        <div className="card p-3 mb-4 flex items-center gap-2 fs-11" style={{ borderColor: 'var(--success)', background: 'var(--success-tint)', color: 'var(--success)' }}>
          <Icon name="check" className="icon-sm" />{savedFlash}
        </div>
      )}

      <div className="settings-shell">
        <nav className="settings-sidebar card p-2" aria-label="Settings sections">
          {NAV.map(n => (
            <button key={n.id} onClick={() => goTo(n.id)} className={`settings-nav-item ${active === n.id ? 'is-active' : ''}`}>
              <Icon name={n.icon} className="icon-sm" />{n.label}
            </button>
          ))}
        </nav>

        <div className="space-y-8">
          {/* ================= APPEARANCE ================= */}
          <section id="appearance" className="card p-5">
            <SectionHeader icon="palette" title="Appearance" description="Theme, accent color, and layout density. Applies instantly across every page." />
            <div className="space-y-3">
              <SettingRow label="Theme" tier="live" help="System follows your OS/browser preference automatically.">
                <div className="flex gap-2">
                  {(['light', 'dark', 'system'] as const).map(m => (
                    <button key={m} onClick={() => setAppearance({ themeMode: m })}
                      className={`btn-ghost !py-1.5 !px-3 fs-11 flex-1 ${prefs.appearance.themeMode === m ? 'is-active' : ''}`}
                      style={prefs.appearance.themeMode === m ? { background: 'var(--red-tint)', borderColor: 'var(--red)', color: 'var(--red)' } : {}}>
                      {m[0].toUpperCase() + m.slice(1)}
                    </button>
                  ))}
                </div>
              </SettingRow>
              <SettingRow label="Quick presets" tier="live" help="Reset colors to a curated light or dark palette.">
                <div className="flex gap-2">
                  <button onClick={() => applyAccentPreset('light')} className="btn-ghost !py-1.5 !px-3 fs-11 flex-1">Light preset</button>
                  <button onClick={() => applyAccentPreset('dark')} className="btn-ghost !py-1.5 !px-3 fs-11 flex-1">Dark preset</button>
                </div>
              </SettingRow>
              <SettingRow label="Accent color" tier="live" help="Used for buttons, links, active states, and highlights everywhere.">
                <ColorControl value={prefs.appearance.accent} onChange={v => setAppearance({ accent: v })} />
              </SettingRow>
              <SettingRow label="Font size" tier="live" help="Scales all text app-wide, independent of your browser zoom.">
                <RangeControl value={prefs.appearance.fontScale} min={0.9} max={1.25} step={0.05} onChange={v => setAppearance({ fontScale: v })} />
              </SettingRow>
              <SettingRow label="Corner roundness" tier="live" help="Applies to cards, buttons, inputs, and panels.">
                <RangeControl value={prefs.appearance.radius} min={0} max={20} unit="px" onChange={v => setAppearance({ radius: v })} />
              </SettingRow>
              <SettingRow label="Density" tier="live" help="Compact tightens spacing across every page for more on-screen at once.">
                <div className="flex gap-2">
                  {(['comfortable', 'compact'] as const).map(d => (
                    <button key={d} onClick={() => setAppearance({ density: d })}
                      className={`btn-ghost !py-1.5 !px-3 fs-11 flex-1 ${prefs.appearance.density === d ? 'is-active' : ''}`}
                      style={prefs.appearance.density === d ? { background: 'var(--red-tint)', borderColor: 'var(--red)', color: 'var(--red)' } : {}}>
                      {d[0].toUpperCase() + d.slice(1)}
                    </button>
                  ))}
                </div>
              </SettingRow>
              <details className="mt-2">
                <summary className="fs-11 font-bold cursor-pointer text-sub">Advanced colors (background, surface, border, text)</summary>
                <div className="space-y-3 mt-3">
                  <SettingRow label="Background" tier="live"><ColorControl value={prefs.appearance.background} onChange={v => setAppearance({ background: v })} /></SettingRow>
                  <SettingRow label="Surface (cards)" tier="live"><ColorControl value={prefs.appearance.surface} onChange={v => setAppearance({ surface: v })} /></SettingRow>
                  <SettingRow label="Surface alt" tier="live"><ColorControl value={prefs.appearance.surfaceAlt} onChange={v => setAppearance({ surfaceAlt: v })} /></SettingRow>
                  <SettingRow label="Border" tier="live"><ColorControl value={prefs.appearance.border} onChange={v => setAppearance({ border: v })} /></SettingRow>
                  <SettingRow label="Text" tier="live"><ColorControl value={prefs.appearance.text} onChange={v => setAppearance({ text: v })} /></SettingRow>
                  <SettingRow label="Secondary text" tier="live"><ColorControl value={prefs.appearance.sub} onChange={v => setAppearance({ sub: v })} /></SettingRow>
                </div>
              </details>
              <div className="pt-3 border-t flex justify-between items-center" style={{ borderColor: 'var(--border)' }}>
                <span className="fs-10 text-sub">Colors and theme also sync to the backend as your saved preference (no login needed).</span>
                <button onClick={() => saveSafePrefs({ THEME: prefs.appearance.themeMode, PRIMARY_COLOR: prefs.appearance.accent, BACKGROUND: prefs.appearance.background, SURFACE: prefs.appearance.surface })} className="btn-ghost !py-1.5 !px-3 fs-11 shrink-0">Sync now</button>
              </div>
            </div>
          </section>

          {/* ================= ACCESSIBILITY ================= */}
          <section id="accessibility" className="card p-5">
            <SectionHeader icon="accessibility" title="Accessibility" description="Every toggle here is wired to real CSS applied across the whole app, not just this page." />
            <div className="space-y-3">
              <SettingRow label="Reduce motion" tier="live" help="Disables animations and transitions app-wide.">
                <Switch checked={prefs.accessibility.reducedMotion} onChange={v => { set({ accessibility: { reducedMotion: v } }); saveSafePrefs({ UI_REDUCED_MOTION: v }) }} />
              </SettingRow>
              <SettingRow label="High contrast" tier="live" help="Thicker borders and stronger contrast for low-vision readability.">
                <Switch checked={prefs.accessibility.highContrast} onChange={v => { set({ accessibility: { highContrast: v } }); saveSafePrefs({ UI_HIGH_CONTRAST: v }) }} />
              </SettingRow>
              <SettingRow label="Dyslexia-friendly font" tier="live" help="Switches body text to Atkinson Hyperlegible.">
                <Switch checked={prefs.accessibility.dyslexiaFont} onChange={v => { set({ accessibility: { dyslexiaFont: v } }); saveSafePrefs({ UI_DYSLEXIA_FONT: v }) }} />
              </SettingRow>
              <SettingRow label="Always underline links" tier="live" help="Makes links identifiable without relying on color alone.">
                <Switch checked={prefs.accessibility.underlineLinks} onChange={v => set({ accessibility: { underlineLinks: v } })} />
              </SettingRow>
            </div>
          </section>

          {/* ================= PREDICTION ENGINE (live, client-side defaults) ================= */}
          <section id="engine" className="card p-5">
            <SectionHeader icon="engine" title="Prediction Engine Defaults" description="These seed the Dashboard's race-condition sliders every time you open it. Change them per-race on the Dashboard, or set your usual baseline here." />
            <div className="card p-3 mb-4 fs-11" style={{ background: 'var(--info-tint)', color: 'var(--info)', border: '1px solid color-mix(in srgb, var(--info) 30%, transparent)' }}>
              These seven parameters are confirmed read by the live prediction engine (verified against the engine source) — they are not admin-gated and need no backend connection to work; they're applied entirely in your browser when you press "Run Prediction."
            </div>
            <div className="space-y-3">
              <SettingRow label="Simulation count" tier="live" help="Default Monte Carlo simulations per prediction (100–50,000).">
                <RangeControl value={prefs.engine.simulationCount} min={100} max={50000} step={100} onChange={v => set({ engine: { simulationCount: v } })} />
              </SettingRow>
              <SettingRow label="Chaos level" tier="live"><RangeControl value={prefs.engine.chaosLevel} min={0} max={100} onChange={v => set({ engine: { chaosLevel: v } })} /></SettingRow>
              <SettingRow label="Grid weight" tier="live"><RangeControl value={prefs.engine.gridWeight} min={0} max={100} unit="%" onChange={v => set({ engine: { gridWeight: v } })} /></SettingRow>
              <SettingRow label="Wet influence" tier="live"><RangeControl value={prefs.engine.wetInfluence} min={0} max={100} unit="%" onChange={v => set({ engine: { wetInfluence: v } })} /></SettingRow>
              <SettingRow label="Reliability influence" tier="live"><RangeControl value={prefs.engine.reliabilityInfluence} min={0} max={100} unit="%" onChange={v => set({ engine: { reliabilityInfluence: v } })} /></SettingRow>
              <SettingRow label="Strategy aggressiveness" tier="live"><RangeControl value={prefs.engine.strategyAggressiveness} min={0} max={100} unit="%" onChange={v => set({ engine: { strategyAggressiveness: v } })} /></SettingRow>
              <SettingRow label="Safety car weight" tier="live"><RangeControl value={prefs.engine.safetyCarWeight} min={0} max={100} unit="%" onChange={v => set({ engine: { safetyCarWeight: v } })} /></SettingRow>
            </div>
            <div className="pt-3 mt-3 border-t flex justify-between items-center" style={{ borderColor: 'var(--border)' }}>
              <span className="fs-10 text-sub">Open the Dashboard to see these applied to a real prediction.</span>
              <button onClick={() => reset('engine')} className="btn-ghost !py-1.5 !px-3 fs-11">Reset to defaults</button>
            </div>
          </section>

          {/* ================= BACKEND CONFIG (real fields, admin-gated) ================= */}
          <section id="backend" className="card p-5">
            <SectionHeader icon="database" title="Backend Configuration" description="Real server-side settings. Saving requires your backend's admin token (set below in Advanced) because these affect every visitor, not just you." />
            {serverSettings.isError && <div className="fs-11 mb-3" style={{ color: 'var(--warning)' }}>Could not reach the backend — showing your last local values. Values below may be stale.</div>}
            <div className="space-y-3">
              <SettingRow label="Cache TTL" tier="admin" help="How long API responses are cached, in seconds.">
                <div className="flex items-center gap-2">
                  <input type="number" className="f1-input" value={prefs.backendAdvanced.cacheTtlSeconds}
                    onChange={e => set({ backendAdvanced: { cacheTtlSeconds: parseInt(e.target.value) || 0 } })} />
                  <button onClick={() => saveBackendField('CACHE_TTL_SECONDS', prefs.backendAdvanced.cacheTtlSeconds)} className="btn-ghost !py-2 !px-3 fs-11 shrink-0">Save</button>
                </div>
              </SettingRow>
              <SettingRow label="Data source priority" tier="admin" help="Which upstream data provider to try first.">
                <div className="flex items-center gap-2">
                  <select className="f1-select" value={prefs.backendAdvanced.dataSourcePriority}
                    onChange={e => set({ backendAdvanced: { dataSourcePriority: e.target.value } })}>
                    <option value="jolpica">Jolpica (Ergast successor)</option>
                    <option value="openf1">OpenF1</option>
                    <option value="fastf1">FastF1</option>
                    <option value="fallback">Local cache (offline)</option>
                  </select>
                  <button onClick={() => saveBackendField('DATA_SOURCE_PRIORITY', prefs.backendAdvanced.dataSourcePriority)} className="btn-ghost !py-2 !px-3 fs-11 shrink-0">Save</button>
                </div>
              </SettingRow>
              <SettingRow label="Live update interval" tier="admin" help="Seconds between live session polling refreshes.">
                <div className="flex items-center gap-2">
                  <input type="number" className="f1-input" value={prefs.backendAdvanced.liveUpdateInterval}
                    onChange={e => set({ backendAdvanced: { liveUpdateInterval: parseInt(e.target.value) || 0 } })} />
                  <button onClick={() => saveBackendField('LIVE_UPDATE_INTERVAL', prefs.backendAdvanced.liveUpdateInterval)} className="btn-ghost !py-2 !px-3 fs-11 shrink-0">Save</button>
                </div>
              </SettingRow>
              <SettingRow label="Model type" tier="admin" help="Which prediction model family the backend serves.">
                <div className="flex items-center gap-2">
                  <select className="f1-select" value={prefs.backendAdvanced.modelType}
                    onChange={e => set({ backendAdvanced: { modelType: e.target.value } })}>
                    <option value="ml">ML (gradient boosted)</option>
                    <option value="dl">Deep learning</option>
                    <option value="ensemble">Ensemble</option>
                  </select>
                  <button onClick={() => saveBackendField('MODEL_TYPE', prefs.backendAdvanced.modelType)} className="btn-ghost !py-2 !px-3 fs-11 shrink-0">Save</button>
                </div>
              </SettingRow>
            </div>
            {serverSettings.data && (
              <div className="fs-10 text-sub mt-3 pt-3 border-t" style={{ borderColor: 'var(--border)' }}>
                Server currently reports: cache_ttl={String(server('CACHE_TTL_SECONDS'))}, model_type={String(server('MODEL_TYPE'))}, live_update_interval={String(server('LIVE_UPDATE_INTERVAL'))}
              </div>
            )}
          </section>

          {/* ================= REFERENCE PARAMS (confirmed not wired to engine) ================= */}
          <section id="reference" className="card p-5">
            <SectionHeader icon="sliders" title="Reference Parameters" description="Traced against the prediction engine's source — these are accepted by the API but not yet read by any model component. Kept visible and editable so nothing you'd expect to tune is hidden; not lost when the engine catches up to them." />
            <div className="card p-3 mb-4 fs-11" style={{ background: 'var(--warning-tint)', color: 'var(--warning)', border: '1px solid color-mix(in srgb, var(--warning) 30%, transparent)' }}>
              Changing these has no effect on predictions yet. They're saved locally as your intended values for when the engine adds support.
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {([
                ['Driver strength weight', 'driverStrengthWeight'], ['Team pace weight', 'teamPaceWeight'],
                ['Track characteristics weight', 'trackCharacteristicsWeight'], ['Weather impact weight', 'weatherImpactWeight'],
                ['Tyre degradation weight', 'tyreDegradationWeight'],
              ] as const).map(([label]) => (
                <SettingRow key={label} label={label} tier="planned"><span className="fs-11 text-sub">Elsewhere in Dashboard &gt; Race Conditions (planned)</span></SettingRow>
              ))}
              <SettingRow label="Elo K-factor" tier="planned"><span className="fs-11 text-sub">32 (fixed)</span></SettingRow>
              <SettingRow label="Ensemble ML / MC weight" tier="planned"><span className="fs-11 text-sub">60 / 40 (fixed)</span></SettingRow>
              <SettingRow label="Calibration method" tier="planned"><span className="fs-11 text-sub">Isotonic (fixed)</span></SettingRow>
              <SettingRow label="Confidence interval" tier="planned"><span className="fs-11 text-sub">95% (fixed)</span></SettingRow>
            </div>
          </section>

          {/* ================= DASHBOARD LAYOUT ================= */}
          <section id="layout" className="card p-5">
            <SectionHeader icon="layout" title="Dashboard Layout" description="Hide panels you don't use, and pick which page opens first." />
            <div className="space-y-3">
              <SettingRow label="Show manual grid editor" tier="live" help="Turn off if you always let qualifying set the grid.">
                <Switch checked={prefs.dashboardLayout.visiblePanels['dashboard.gridEditor'] ?? true}
                  onChange={v => set({ dashboardLayout: { visiblePanels: { ...prefs.dashboardLayout.visiblePanels, 'dashboard.gridEditor': v } } })} />
              </SettingRow>
              <SettingRow label="Show export panel" tier="live" help="The CSV/JSON/PDF export card at the bottom of the Dashboard.">
                <Switch checked={prefs.dashboardLayout.visiblePanels['dashboard.reports'] ?? true}
                  onChange={v => set({ dashboardLayout: { visiblePanels: { ...prefs.dashboardLayout.visiblePanels, 'dashboard.reports': v } } })} />
              </SettingRow>
              <SettingRow label="Compact tables" tier="live" help="Tighter row spacing in Standings and H2H tables.">
                <Switch checked={prefs.dashboardLayout.compactTables} onChange={v => set({ dashboardLayout: { compactTables: v } })} />
              </SettingRow>
              <SettingRow label="Default landing page" tier="live" help="Where the F1 logo / '/' takes you.">
                <select className="f1-select" value={prefs.dashboardLayout.defaultRoute} onChange={e => set({ dashboardLayout: { defaultRoute: e.target.value } })}>
                  <option value="/">Home</option>
                  <option value="/dashboard">Predictions</option>
                  <option value="/standings">Standings</option>
                </select>
              </SettingRow>
            </div>
          </section>

          {/* ================= NOTIFICATIONS ================= */}
          <section id="notifications" className="card p-5">
            <SectionHeader icon="bell" title="Notifications" description="Real browser notifications, scheduled entirely in your browser — no backend or account needed. There is no other notification system in this app, so nothing else appears here." />
            <div className="space-y-3">
              <SettingRow label="Race start reminders" tier="live" help="Requires notification permission for this site.">
                <Switch checked={prefs.notifications.raceReminders} onChange={async v => {
                  if (v) {
                    const perm = await requestNotificationPermission()
                    if (perm !== 'granted') { flash(perm === 'unsupported' ? 'Notifications are not supported in this browser.' : 'Notification permission was not granted.'); return }
                  }
                  set({ notifications: { raceReminders: v } })
                }} />
              </SettingRow>
              <SettingRow label="Remind me before" tier="live" help="How far ahead of the next session to notify you.">
                <select className="f1-select" value={prefs.notifications.reminderMinutesBefore} onChange={e => set({ notifications: { reminderMinutesBefore: parseInt(e.target.value) } })}>
                  <option value={15}>15 minutes</option><option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option><option value={180}>3 hours</option><option value={1440}>1 day</option>
                </select>
              </SettingRow>
            </div>
          </section>

          {/* ================= PROFILE ================= */}
          <section id="profile" className="card p-5">
            <SectionHeader icon="user" title="Profile" description="There's no account system in this app (sign-in is disabled), so this is local personalization only — your favorite driver is marked with an icon on the Standings table, and nothing else." />
            <div className="space-y-3">
              <SettingRow label="Display name" tier="live"><input className="f1-input" value={prefs.profile.displayName} onChange={e => set({ profile: { displayName: e.target.value } })} placeholder="Your name" /></SettingRow>
              <SettingRow label="Favorite driver code" tier="live" help="E.g. VER, NOR, LEC — highlighted where relevant."><input className="f1-input f1-mono" maxLength={3} value={prefs.profile.favoriteDriverCode} onChange={e => set({ profile: { favoriteDriverCode: e.target.value.toUpperCase() } })} /></SettingRow>
              <SettingRow label="Favorite team" tier="live"><input className="f1-input" value={prefs.profile.favoriteTeam} onChange={e => set({ profile: { favoriteTeam: e.target.value } })} /></SettingRow>
            </div>
          </section>

          {/* ================= ADVANCED ================= */}
          <section id="advanced" className="card p-5">
            <SectionHeader icon="shield" title="Advanced" description="API connection, admin access, and developer options." />
            <div className="space-y-3">
              <SettingRow label="API base URL override" tier="live" help="Point this frontend at a different backend host without rebuilding. Leave blank to use the default.">
                <input className="f1-input f1-mono" placeholder="https://api.example.com" value={prefs.advanced.apiBaseOverride} onChange={e => set({ advanced: { apiBaseOverride: e.target.value } })} />
              </SettingRow>
              <SettingRow label="Request timeout" tier="live" help="Aborts a stalled request after this long.">
                <RangeControl value={prefs.advanced.requestTimeoutMs} min={2000} max={60000} step={1000} unit="ms" onChange={v => set({ advanced: { requestTimeoutMs: v } })} />
              </SettingRow>
              <SettingRow label="Debug logging" tier="live" help="Logs every API request's timing and status to the browser console.">
                <Switch checked={prefs.advanced.debugLogging} onChange={v => set({ advanced: { debugLogging: v } })} />
              </SettingRow>
              <SettingRow label="Keyboard shortcuts" tier="live" help="Enable the g-then-letter navigation shortcuts (see below).">
                <Switch checked={prefs.advanced.keyboardShortcuts} onChange={v => set({ advanced: { keyboardShortcuts: v } })} />
              </SettingRow>
              <SettingRow label="Reduce data usage" tier="live" help="Hides hero videos and heavy imagery on the Home page.">
                <Switch checked={prefs.advanced.reduceDataUsage} onChange={v => set({ advanced: { reduceDataUsage: v } })} />
              </SettingRow>
            </div>

            <div className="mt-5 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2 mb-1"><Icon name="lock" className="icon-sm" /><span className="font-bold text-sm">Admin access</span></div>
              <p className="fs-11 text-sub mb-2 max-w-lg">Needed only for the Backend Configuration fields above. Kept in this browser tab's session only — never saved to disk, never exported. If your backend has no <code className="f1-mono">SETTINGS_ADMIN_TOKEN</code> configured, no token will work.</p>
              <div className="flex items-center gap-2">
                <input type="password" className="f1-input f1-mono flex-1" placeholder="Admin token" value={tokenInput} onChange={e => setTokenInput(e.target.value)} />
                <button onClick={testAdminToken} className="btn-ghost !py-2 !px-3 fs-11 shrink-0">{tokenStatus === 'checking' ? 'Checking…' : 'Save & test'}</button>
              </div>
              {tokenStatus === 'ok' && <div className="fs-11 mt-2" style={{ color: 'var(--success)' }}>Token accepted — backend fields above are now writable.</div>}
              {tokenStatus === 'bad' && <div className="fs-11 mt-2" style={{ color: 'var(--danger)' }}>Rejected. Either the token is wrong, or the backend has no SETTINGS_ADMIN_TOKEN set.</div>}
            </div>
          </section>

          {/* ================= SHORTCUTS ================= */}
          <section id="shortcuts" className="card p-5">
            <SectionHeader icon="keyboard" title="Keyboard Shortcuts" description="Active whenever the toggle in Advanced is on and you're not typing in a field." />
            <div className="grid sm:grid-cols-2 gap-2 fs-11">
              {[['g then h', 'Home'], ['g then d', 'Predictions'], ['g then s', 'Standings'], ['g then v', 'Head to Head'], ['g then f', 'Fantasy'], ['g then g', 'Guide'], ['g then t', 'Settings'], ['?', 'Open this shortcuts list']].map(([keys, action]) => (
                <div key={action} className="flex items-center justify-between p-2.5 rounded-lg" style={{ background: 'var(--surface-alt)' }}>
                  <span>{action}</span>
                  <span className="flex items-center gap-1">{keys.split(' then ').map((k, i, arr) => <span key={k} className="flex items-center gap-1"><span className="kbd">{k}</span>{i < arr.length - 1 && <span className="text-sub">then</span>}</span>)}</span>
                </div>
              ))}
            </div>
          </section>

          {/* ================= DATA & PRIVACY ================= */}
          <section id="data" className="card p-5">
            <SectionHeader icon="trash" title="Data & Privacy" description="Everything on this page lives in your browser's local storage. Nothing here is sent anywhere except the specific backend syncs described above." />
            <div className="flex flex-wrap gap-3">
              <button onClick={handleExport} className="btn-ghost fs-11 flex items-center gap-1.5"><Icon name="download" className="icon-sm" />Export settings as JSON</button>
              <label className="btn-ghost fs-11 flex items-center gap-1.5 cursor-pointer">
                <Icon name="upload" className="icon-sm" />Import settings
                <input type="file" accept="application/json" className="hidden" onChange={e => e.target.files?.[0] && handleImportFile(e.target.files[0])} />
              </label>
              <button onClick={clearLocalCache} className="btn-ghost fs-11 flex items-center gap-1.5"><Icon name="refresh" className="icon-sm" />Clear local cache</button>
            </div>
            {importError && <div className="fs-11 mt-2" style={{ color: 'var(--danger)' }}>{importError}</div>}
            <div className="mt-5 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
              <div className="font-bold text-sm mb-1" style={{ color: 'var(--danger)' }}>Danger zone</div>
              <button onClick={() => { if (confirm('Reset every setting on this page to defaults? This cannot be undone.')) reset() }} className="btn-danger fs-11">Reset all settings to defaults</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
