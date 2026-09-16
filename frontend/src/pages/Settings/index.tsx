import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

type Group = { id:string; label:string; icon:string; fields:string[]; desc?:string }

const COLOR_FIELDS = new Set(['PRIMARY_COLOR','BACKGROUND','SURFACE','SURFACE_ALT','BORDER','TEXT','SUB'])
const COLOR_DEFAULTS: Record<string,string> = {
  PRIMARY_COLOR: '#E10600', BACKGROUND: '#F4F5F7', SURFACE: '#FFFFFF', SURFACE_ALT: '#EEF0F3',
  BORDER: '#E3E5EA', TEXT: '#15151E', SUB: '#6B7280',
}

const FIELD_HELP: Record<string,string> = {
  // Appearance
  PRIMARY_COLOR: 'Primary action color — buttons, links, active nav. Live preview below.',
  BACKGROUND: 'Page background. Light #F4F5F7 vs dark #0A0C10.',
  SURFACE: 'Card surface. Must contrast with background.',
  TEXT: 'Primary text color.',
  
  // Monte Carlo Engine
  MONTE_CARLO_SIMULATIONS: 'Number of race simulations (100-50,000). More = smoother predictions but slower (~80ms per 10k sims)',
  CHAOS_LEVEL_DEFAULT: 'Race unpredictability 0-100. Higher = more upsets, surprises, and variance in results',
  GRID_WEIGHT_DEFAULT: 'Starting position importance 0-100. Lower = closer 2026 racing with active aero',
  WET_INFLUENCE_DEFAULT: 'Rain impact on results 0-100. Affects reliability and overtaking probability',
  RELIABILITY_INFLUENCE_DEFAULT: 'DNF risk factor 0-100. Higher = more mechanical failures and crashes',
  STRATEGY_AGGRESSIVENESS_DEFAULT: 'Pit stop strategy aggressiveness 0-100. Affects tire compound choices',
  
  // Feature Engineering Weights
  DRIVER_STRENGTH_WEIGHT: 'Driver skill importance in predictions (Elo-based rating)',
  TEAM_PACE_WEIGHT: 'Team car performance weight (constructor strength)',
  TRACK_CHARACTERISTICS_WEIGHT: 'Circuit layout influence (power vs technical tracks)',
  WEATHER_IMPACT_WEIGHT: 'Weather conditions effect on race outcomes',
  TYRE_DEGRADATION_WEIGHT: 'Tire wear and compound strategy importance',
  
  // Elo Rating System
  ELO_K_FACTOR: 'Elo rating adjustment speed (higher = faster changes after races)',
  ELO_INITIAL_RATING: 'Starting Elo for new drivers (default 1500)',
  ELO_HOME_ADVANTAGE: 'Bonus points for home races (e.g., Hamilton at Silverstone)',
  
  // Probability Model
  ENSEMBLE_WEIGHT_ML: 'Machine Learning model weight in ensemble (0-100%)',
  ENSEMBLE_WEIGHT_MC: 'Monte Carlo simulation weight in ensemble (0-100%)',
  CALIBRATION_METHOD: 'Probability calibration method: isotonic, Platt scaling, or none',
  CONFIDENCE_INTERVAL: 'Confidence level for prediction intervals (e.g., 95%)',
  
  // Data Sources & Caching
  CACHE_TTL_SECONDS: 'API response cache lifetime in seconds (300 = 5 minutes)',
  DATA_SOURCE_PRIORITY: 'Primary data source: Jolpica, OpenF1, FastF1, or fallback',
  LIVE_UPDATE_INTERVAL: 'Background data refresh interval in seconds',
  
  // Model Selection
  MODEL_TYPE: 'Prediction approach: ML (fast), DL (accurate), or Ensemble (combined)',
  MODEL_VERSION: 'Active model version identifier (e.g., v12.4)',
}

function applyColors(colors: Record<string,string>) {
  const map: Record<string,string> = {
    PRIMARY_COLOR: '--red', BACKGROUND: '--bg', SURFACE: '--surface', SURFACE_ALT: '--surface-alt',
    BORDER: '--border', TEXT: '--text', SUB: '--sub',
  }
  Object.entries(colors).forEach(([k,v]) => {
    const cssVar = map[k]
    if (cssVar && v) document.documentElement.style.setProperty(cssVar, v)
  })
  if (colors.PRIMARY_COLOR) {
    document.documentElement.style.setProperty('--red', colors.PRIMARY_COLOR)
    const c = colors.PRIMARY_COLOR
    if (c.startsWith('#') && c.length===7) {
      const r = parseInt(c.slice(1,3),16), g=parseInt(c.slice(3,5),16), b=parseInt(c.slice(5,7),16)
      const dark = `rgb(${Math.max(0,r-40)},${Math.max(0,g-10)},${Math.max(0,b-10)})`
      document.documentElement.style.setProperty('--red-dark', dark)
    }
  }
}

function FieldInput({ name, value, onChange }: { name:string; value:any; onChange:(v:any)=>void }) {
  const isColor = COLOR_FIELDS.has(name) || name.toLowerCase().includes('color')
  const isBool = typeof value === 'boolean'
  const isNumber = typeof value === 'number'
  
  if (isColor) {
    return (
      <div className="flex items-center gap-2">
        <input type="color" value={typeof value==='string' && value.startsWith('#') ? value : '#E10600'} onChange={e=> onChange(e.target.value)} className="w-10 h-8 rounded border p-0" style={{ borderColor:'var(--border)'}} />
        <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input flex-1 font-mono text-xs" placeholder="#RRGGBB" />
      </div>
    )
  }
  
  // Model selection dropdown
  if (name === 'MODEL_TYPE') {
    return (
      <select value={value || 'ensemble'} onChange={e=> onChange(e.target.value)} className="f1-select">
        <option value="ml">⚙️ Machine Learning (Fast ~50ms)</option>
        <option value="dl">🧠 Deep Learning (Accurate ~200ms)</option>
        <option value="ensemble">🎯 Ensemble (Balanced ~120ms)</option>
      </select>
    )
  }
  
  // Calibration method dropdown
  if (name === 'CALIBRATION_METHOD') {
    return (
      <select value={value || 'isotonic'} onChange={e=> onChange(e.target.value)} className="f1-select">
        <option value="isotonic">Isotonic Regression</option>
        <option value="platt">Platt Scaling</option>
        <option value="none">No Calibration</option>
      </select>
    )
  }
  
  // Data source priority
  if (name === 'DATA_SOURCE_PRIORITY') {
    return (
      <select value={value || 'jolpica'} onChange={e=> onChange(e.target.value)} className="f1-select">
        <option value="jolpica">Jolpica (Official F1 Timing)</option>
        <option value="openf1">OpenF1 (Live Telemetry)</option>
        <option value="fastf1">FastF1 (Historical Data)</option>
        <option value="fallback">Local Cache (Offline)</option>
      </select>
    )
  }
  
  if (isBool) {
    return <button onClick={()=> onChange(!value)} className={`f1-switch ${value?'is-on':''}`} aria-label={name}><span className="knob" /></button>
  }
  
  if (isNumber) {
    // Sliders for important tuning params
    const isSlider = [
      'CHAOS_LEVEL_DEFAULT', 'GRID_WEIGHT_DEFAULT', 'WET_INFLUENCE_DEFAULT',
      'RELIABILITY_INFLUENCE_DEFAULT', 'STRATEGY_AGGRESSIVENESS_DEFAULT',
      'DRIVER_STRENGTH_WEIGHT', 'TEAM_PACE_WEIGHT', 'TRACK_CHARACTERISTICS_WEIGHT',
      'WEATHER_IMPACT_WEIGHT', 'TYRE_DEGRADATION_WEIGHT',
      'ENSEMBLE_WEIGHT_ML', 'ENSEMBLE_WEIGHT_MC'
    ].includes(name)
    
    if (isSlider) {
      return (
        <div className="flex items-center gap-3">
          <input 
            type="range" 
            min={name.includes('WEIGHT') || name.includes('INFLUENCE') ? 0 : 100} 
            max={name.includes('WEIGHT') || name.includes('INFLUENCE') ? 100 : 50000} 
            value={value} 
            onChange={e=> onChange(parseInt(e.target.value))} 
            className="f1-range flex-1 accent-red" 
          />
          <span className="f1-mono w-16 text-sm font-bold text-right" style={{ color:'var(--red)'}}>{value}</span>
        </div>
      )
    }
    
    return <input type="number" value={value} onChange={e=> onChange(e.target.value===''? '' : Number(e.target.value))} className="f1-input" />
  }
  
  return <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input" />
}

export function SettingsPage(){
  // Fast load: initialize from local cache synchronously so first paint is instant, then merge API
  const [settings, setSettings] = useState<Record<string,any>>(()=>{
    try{
      const local = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
      const cached = (()=>{ try{ return JSON.parse(localStorage.getItem('f1-settings-cache')||'{}')}catch{return {}}})()
      return { 
        ...COLOR_DEFAULTS,
        // Monte Carlo defaults
        MONTE_CARLO_SIMULATIONS: 10000,
        CHAOS_LEVEL_DEFAULT: 50,
        GRID_WEIGHT_DEFAULT: 55,
        WET_INFLUENCE_DEFAULT: 60,
        RELIABILITY_INFLUENCE_DEFAULT: 40,
        STRATEGY_AGGRESSIVENESS_DEFAULT: 50,
        // Feature weights
        DRIVER_STRENGTH_WEIGHT: 70,
        TEAM_PACE_WEIGHT: 65,
        TRACK_CHARACTERISTICS_WEIGHT: 55,
        WEATHER_IMPACT_WEIGHT: 60,
        TYRE_DEGRADATION_WEIGHT: 50,
        // Elo
        ELO_K_FACTOR: 32,
        ELO_INITIAL_RATING: 1500,
        ELO_HOME_ADVANTAGE: 25,
        // Ensemble
        ENSEMBLE_WEIGHT_ML: 45,
        ENSEMBLE_WEIGHT_MC: 55,
        CALIBRATION_METHOD: 'isotonic',
        CONFIDENCE_INTERVAL: 95,
        // Data
        CACHE_TTL_SECONDS: 300,
        DATA_SOURCE_PRIORITY: 'jolpica',
        LIVE_UPDATE_INTERVAL: 300,
        // Model
        MODEL_TYPE: 'ensemble',
        MODEL_VERSION: 'v12.4',
        ...cached, 
        ...local 
      }
    }catch{ 
      return { 
        ...COLOR_DEFAULTS,
        MONTE_CARLO_SIMULATIONS: 10000,
        CHAOS_LEVEL_DEFAULT: 50,
        MODEL_TYPE: 'ensemble',
        MODEL_VERSION: 'v12.4'
      } 
    }
  })
  const [draft, setDraft] = useState<Record<string,any>>(()=>{
    try{
      const local = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
      const cached = (()=>{ try{ return JSON.parse(localStorage.getItem('f1-settings-cache')||'{}')}catch{return {}}})()
      return { 
        ...COLOR_DEFAULTS,
        MONTE_CARLO_SIMULATIONS: 10000,
        CHAOS_LEVEL_DEFAULT: 50,
        MODEL_TYPE: 'ensemble',
        MODEL_VERSION: 'v12.4',
        ...cached, 
        ...local 
      }
    }catch{ 
      return { 
        ...COLOR_DEFAULTS,
        MONTE_CARLO_SIMULATIONS: 10000,
        CHAOS_LEVEL_DEFAULT: 50,
        MODEL_TYPE: 'ensemble',
        MODEL_VERSION: 'v12.4'
      } 
    }
  })
  const [active, setActive] = useState<string>('appearance')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<string|null>(null)

  // Apply cached colors immediately for instant paint
  useEffect(()=>{
    try{
      const local = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
      if (Object.keys(local).length) applyColors(local)
      else applyColors(COLOR_DEFAULTS)
    }catch{ applyColors(COLOR_DEFAULTS) }
  },[])

  // Load backend + local settings — non-blocking, merges when ready
  useEffect(()=>{
    let cancelled=false
    api.get<any>('/api/v1/settings').then(r=>{
      if (cancelled) return
      setSettings(r.settings)
      setDraft(r.settings)
      try{ localStorage.setItem('f1-settings-cache', JSON.stringify(r.settings)) }catch{}
      const local = (()=>{ try{ return JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')}catch{return {}}})()
      const colors: Record<string,string> = {}
      Object.keys(COLOR_DEFAULTS).forEach(k=> {
        const v = r.settings[k] || local[k] || COLOR_DEFAULTS[k]
        if (v) colors[k]=String(v)
      })
      applyColors(colors)
    }).catch(()=> { if(!cancelled) setMsg('Backend settings unavailable — using local cache') })
    return ()=> { cancelled=true }
  },[])

  const groups: Group[] = useMemo(()=> [
    { id:'appearance', label:'Appearance', icon:'🎨', desc:'Colors, theme, live preview', fields:['PRIMARY_COLOR','BACKGROUND','SURFACE','SURFACE_ALT','BORDER','TEXT','SUB']},
    { id:'monte-carlo', label:'Monte Carlo Engine', icon:'🎲', desc:'Simulation count, chaos, grid weight, weather impact', fields:['MONTE_CARLO_SIMULATIONS','CHAOS_LEVEL_DEFAULT','GRID_WEIGHT_DEFAULT','WET_INFLUENCE_DEFAULT','RELIABILITY_INFLUENCE_DEFAULT','STRATEGY_AGGRESSIVENESS_DEFAULT']},
    { id:'features', label:'Feature Engineering', icon:'⚙️', desc:'Driver strength, team pace, track, weather, tyre weights', fields:['DRIVER_STRENGTH_WEIGHT','TEAM_PACE_WEIGHT','TRACK_CHARACTERISTICS_WEIGHT','WEATHER_IMPACT_WEIGHT','TYRE_DEGRADATION_WEIGHT']},
    { id:'elo', label:'Elo Ratings', icon:'📊', desc:'Driver rating system configuration', fields:['ELO_K_FACTOR','ELO_INITIAL_RATING','ELO_HOME_ADVANTAGE']},
    { id:'probability', label:'Probability Model', icon:'🎯', desc:'Ensemble weights, calibration, confidence intervals', fields:['ENSEMBLE_WEIGHT_ML','ENSEMBLE_WEIGHT_MC','CALIBRATION_METHOD','CONFIDENCE_INTERVAL']},
    { id:'data', label:'Data & Cache', icon:'💾', desc:'API sources, cache TTL, update intervals', fields:['CACHE_TTL_SECONDS','DATA_SOURCE_PRIORITY','LIVE_UPDATE_INTERVAL']},
    { id:'models', label:'Model Selection', icon:'🤖', desc:'ML vs DL vs Ensemble prediction approach', fields:['MODEL_TYPE','MODEL_VERSION']},
  ], [])

  const currentGroup = useMemo(()=> groups.find(g=> g.id===active) || groups[0], [groups, active])

  const setField = (k:string, v:any)=>{
    setDraft(d=> ({...d, [k]: v}))
    if (COLOR_FIELDS.has(k)) {
      applyColors({ [k]: v })
      try{
        const prev = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
        localStorage.setItem('f1-settings-colors', JSON.stringify({...prev, [k]: v}))
      }catch{}
    }
  }

  const save = async()=>{
    setSaving(true); setMsg(null)
    try{
      const diff: Record<string,any> = {}
      const base = settings || {}
      Object.entries(draft).forEach(([k,v])=>{
        if (JSON.stringify(base[k]) !== JSON.stringify(v)) diff[k]=v
      })
      if (!Object.keys(diff).length) { setMsg('No changes to save'); setSaving(false); return }
      const res = await fetch('/api/v1/settings', { method:'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify(diff) }).then(async r=>{
        if (!r.ok) throw new Error(`Save failed ${r.status}`)
        return r.json()
      })
      setSettings(res.settings)
      setDraft(res.settings)
      try{ localStorage.setItem('f1-settings-cache', JSON.stringify(res.settings)) }catch{}
      setMsg(`Saved ${Object.keys(diff).length} engine parameters successfully.`)
      const colors: Record<string,string> = {}
      Object.keys(COLOR_DEFAULTS).forEach(k=> { if (draft[k]) colors[k]=String(draft[k]) })
      if (Object.keys(colors).length) localStorage.setItem('f1-settings-colors', JSON.stringify(colors))
    }catch(e:any){ setMsg(e.message || 'Save failed')}
    finally{ setSaving(false)}
  }

  const reset = async()=>{
    if (!confirm('Reset all engine settings to defaults?')) return
    setSaving(true)
    try{
      const r = await fetch('/api/v1/settings/reset', { method:'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({}) }).then(async r=>{
        if (!r.ok) throw new Error(`Reset failed ${r.status}`)
        return r.json()
      })
      setSettings(r.settings); setDraft(r.settings)
      try{ localStorage.removeItem('f1-settings-cache')}catch{}
      localStorage.removeItem('f1-settings-colors')
      applyColors(COLOR_DEFAULTS)
      setMsg('All engine settings reset to defaults.')
    }catch(e:any){ setMsg(e.message)}
    finally{ setSaving(false)}
  }

  const applyPreset = (name:string)=>{
    const presets: Record<string, Record<string,any>> = {
      // Racing styles
      conservative: { CHAOS_LEVEL_DEFAULT: 20, GRID_WEIGHT_DEFAULT: 65, WET_INFLUENCE_DEFAULT: 30, RELIABILITY_INFLUENCE_DEFAULT: 70, STRATEGY_AGGRESSIVENESS_DEFAULT: 30, MONTE_CARLO_SIMULATIONS: 8000 },
      aggressive: { CHAOS_LEVEL_DEFAULT: 75, GRID_WEIGHT_DEFAULT: 40, WET_INFLUENCE_DEFAULT: 70, RELIABILITY_INFLUENCE_DEFAULT: 30, STRATEGY_AGGRESSIVENESS_DEFAULT: 80, MONTE_CARLO_SIMULATIONS: 15000 },
      qualifying: { CHAOS_LEVEL_DEFAULT: 25, GRID_WEIGHT_DEFAULT: 75, MONTE_CARLO_SIMULATIONS: 5000, ENSEMBLE_WEIGHT_ML: 60, ENSEMBLE_WEIGHT_MC: 40 },
      race: { CHAOS_LEVEL_DEFAULT: 50, GRID_WEIGHT_DEFAULT: 55, MONTE_CARLO_SIMULATIONS: 12000, ENSEMBLE_WEIGHT_ML: 45, ENSEMBLE_WEIGHT_MC: 55 },
      // Themes
      dark: { PRIMARY_COLOR: '#FF3B30', BACKGROUND: '#0A0C10', SURFACE: '#15181F', SURFACE_ALT: '#1C2028', BORDER: '#2B3039', TEXT: '#F1F2F5', SUB:'#9BA2AF' },
      light: { PRIMARY_COLOR: '#E10600', BACKGROUND: '#F4F5F7', SURFACE: '#FFFFFF', SURFACE_ALT: '#EEF0F3', BORDER: '#E3E5EA', TEXT: '#15151E', SUB:'#6B7280' },
      performance: { PRIMARY_COLOR: '#16a34a', BACKGROUND: '#0A0C10', SURFACE: '#15181F', CACHE_TTL_SECONDS: 600, MONTE_CARLO_SIMULATIONS: 5000 },
      // Accuracy focused
      high_accuracy: { MONTE_CARLO_SIMULATIONS: 50000, ENSEMBLE_WEIGHT_ML: 50, ENSEMBLE_WEIGHT_MC: 50, CALIBRATION_METHOD: 'isotonic', CONFIDENCE_INTERVAL: 99 },
      fast_predictions: { MONTE_CARLO_SIMULATIONS: 1000, ENSEMBLE_WEIGHT_ML: 70, ENSEMBLE_WEIGHT_MC: 30, CACHE_TTL_SECONDS: 60 },
    }
    const p = presets[name]
    if (!p) return
    const next = {...draft, ...p}
    setDraft(next)
    if (p.PRIMARY_COLOR) applyColors(p)
    setMsg(`Preset "${name}" applied — hit Save to persist engine config.`)
  }

  const sims = Number(draft.MONTE_CARLO_SIMULATIONS||10000)
  const perfImpact = sims>20000? 'High accuracy — ~1.2s per prediction': sims>8000? 'Balanced — ~0.4s' : 'Fast — ~0.15s'

  return (
    <div className="px-4 sm:px-8 py-6 max-w-6xl mx-auto space-y-6">
      {/* Hero */}
      <div className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ background:'var(--red)'}} />
              <span className="fs-11 font-bold tracking-widest" style={{ color:'var(--red)'}}>ENGINE CONTROL CENTER</span>
            </div>
            <h1 className="f1-display text-2xl font-black mt-1">Prediction Engine Settings</h1>
            <p className="text-sub fs-11 mt-1 max-w-3xl">
              Tune every aspect of the prediction engine: Monte Carlo simulations, feature weights, Elo ratings, 
              probability models, and data sources. All changes take effect on next prediction run.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={save} disabled={saving} className="btn-primary" style={{ background:'#16a34a'}}>{saving?'Saving…':'Save Engine Config'}</button>
            <button onClick={reset} className="btn-ghost">Reset Defaults</button>
          </div>
        </div>
        {msg && <div className="mt-3 p-2 rounded-lg surface-alt fs-11">{msg}</div>}
      </div>

      {/* Quick Presets Bar */}
      <div className="card p-4">
        <div className="fs-11 font-bold mb-3">Quick Presets — One-click engine profiles</div>
        <div className="flex flex-wrap gap-2">
          <button onClick={()=> applyPreset('conservative')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            🛡️ Conservative
          </button>
          <button onClick={()=> applyPreset('aggressive')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            ⚡ Aggressive
          </button>
          <button onClick={()=> applyPreset('qualifying')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            🏁 Qualifying Mode
          </button>
          <button onClick={()=> applyPreset('race')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            🏎️ Race Mode
          </button>
          <button onClick={()=> applyPreset('high_accuracy')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            🎯 High Accuracy
          </button>
          <button onClick={()=> applyPreset('fast_predictions')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            ⚙️ Fast Predictions
          </button>
          <button onClick={()=> applyPreset('dark')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            🌙 Dark Theme
          </button>
          <button onClick={()=> applyPreset('light')} className="px-4 py-2 rounded-lg border fs-11 font-bold hover:bg-black/5" style={{ borderColor: 'var(--border)' }}>
            ☀️ Light Theme
          </button>
          <span className="ml-auto fs-11 text-sub self-center">{perfImpact}</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="card p-3 flex flex-wrap gap-2">
        {groups.map(g=> (
          <button 
            key={g.id} 
            onClick={()=> setActive(g.id)} 
            className={`px-4 py-2 rounded-full fs-11 font-bold transition-colors ${
              active===g.id ? 'bg-black text-white' : 'bg-white border hover:bg-black/5'
            }`}
          >
            <span className="mr-1">{g.icon}</span>
            {g.label}
          </button>
        ))}
      </div>

      {/* Active Section */}
      <div className="card p-6">
        <div className="flex items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="f1-display font-bold flex items-center gap-2">
              <span>{currentGroup.icon}</span>
              {currentGroup.label}
            </h2>
            <div className="fs-11 text-sub">{currentGroup.desc}</div>
          </div>
        </div>

        <div className="space-y-4">
          {currentGroup.fields.map(name=>{
            const v = draft[name]
            const dirty = settings && JSON.stringify(settings[name]) !== JSON.stringify(v)
            return (
              <div key={name} className={`p-4 rounded-lg ${dirty?'border-2' : 'border'}`} style={{ borderColor: dirty ? '#f59e0b' : 'var(--border)' }}>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="f1-mono text-sm font-bold">{name.replace(/_/g, ' ')}</span>
                      {dirty && <span className="fs-11 px-1.5 py-0.5 rounded bg-amber-500 text-white">changed</span>}
                    </div>
                    <div className="fs-11 text-sub mt-1">{FIELD_HELP[name] || `Setting for ${name}`}</div>
                  </div>
                  <div className="w-[280px] shrink-0">
                    <FieldInput name={name} value={v} onChange={(nv)=> setField(name, nv)} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Contextual Info Panels */}
        {currentGroup.id === 'monte-carlo' && (
          <div className="mt-6 p-4 rounded-lg bg-black text-white">
            <div className="fs-11 font-bold mb-2">🎲 Monte Carlo Engine Details</div>
            <div className="fs-11 space-y-2">
              <div><strong>Simulations:</strong> Vectorized NumPy operations run {sims.toLocaleString()} race scenarios in ~{(sims * 0.008).toFixed(1)}ms</div>
              <div><strong>Chaos Level:</strong> Blends deterministic (0) to uniform random (100) distributions for grid positions</div>
              <div><strong>Grid Weight:</strong> 2026 active aero reduces starting position advantage — lower values = closer racing</div>
              <div><strong>Weather Impact:</strong> Rain increases DNF probability and creates overtaking opportunities</div>
              <div><strong>Reliability:</strong> Models mechanical failures based on historical DNF rates per driver/team</div>
            </div>
          </div>
        )}

        {currentGroup.id === 'features' && (
          <div className="mt-6 p-4 rounded-lg surface-alt">
            <div className="fs-11 font-bold mb-2">⚙️ Feature Engineering Overview</div>
            <div className="fs-11 text-sub space-y-2">
              <div>These weights control how much each factor influences final predictions. Total doesn't need to equal 100 — they're normalized internally.</div>
              <div className="grid md:grid-cols-2 gap-3 mt-3">
                <div><strong>Driver Strength:</strong> Elo-based rating from historical performance</div>
                <div><strong>Team Pace:</strong> Constructor competitiveness and car development</div>
                <div><strong>Track Characteristics:</strong> Circuit layout (street vs permanent, power vs technical)</div>
                <div><strong>Weather Impact:</strong> Rain, temperature, wind effects on performance</div>
                <div><strong>Tyre Degradation:</strong> Compound wear and pit strategy optimization</div>
              </div>
            </div>
          </div>
        )}

        {currentGroup.id === 'elo' && (
          <div className="mt-6 p-4 rounded-lg surface-alt">
            <div className="fs-11 font-bold mb-2">📊 Elo Rating System</div>
            <div className="fs-11 text-sub space-y-2">
              <div>Elo ratings track driver skill over time, updating after each race based on results vs expectations.</div>
              <div className="grid md:grid-cols-3 gap-3 mt-3">
                <div><strong>K-Factor ({draft.ELO_K_FACTOR}):</strong> How quickly ratings change. Higher = more volatile, reacts faster to form changes</div>
                <div><strong>Initial Rating ({draft.ELO_INITIAL_RATING}):</strong> Starting point for rookies and new drivers</div>
                <div><strong>Home Advantage (+{draft.ELO_HOME_ADVANTAGE}):</strong> Bonus for racing at home circuits (e.g., Hamilton at Silverstone)</div>
              </div>
            </div>
          </div>
        )}

        {currentGroup.id === 'probability' && (
          <div className="mt-6 p-4 rounded-lg surface-alt">
            <div className="fs-11 font-bold mb-2">🎯 Ensemble Probability Model</div>
            <div className="fs-11 text-sub space-y-2">
              <div>Combines ML predictions with Monte Carlo simulations for balanced accuracy and interpretability.</div>
              <div className="grid md:grid-cols-2 gap-3 mt-3">
                <div><strong>ML Weight ({draft.ENSEMBLE_WEIGHT_ML}%):</strong> Historical pattern recognition via gradient boosting</div>
                <div><strong>MC Weight ({draft.ENSEMBLE_WEIGHT_MC}%):</strong> Physics-based race simulation with randomness</div>
                <div><strong>Calibration:</strong> {draft.CALIBRATION_METHOD === 'isotonic' ? 'Isotonic regression adjusts probabilities to match observed frequencies' : draft.CALIBRATION_METHOD === 'platt' ? 'Platt scaling uses logistic regression for probability calibration' : 'Raw uncalibrated probabilities'}</div>
                <div><strong>Confidence Interval:</strong> {draft.CONFIDENCE_INTERVAL}% prediction intervals show uncertainty range</div>
              </div>
            </div>
          </div>
        )}

        {currentGroup.id === 'data' && (
          <div className="mt-6 p-4 rounded-lg surface-alt">
            <div className="fs-11 font-bold mb-2">💾 Data Sources & Caching Strategy</div>
            <div className="fs-11 text-sub space-y-2">
              <div>Multi-source data federation with automatic failover and intelligent caching.</div>
              <div className="grid md:grid-cols-2 gap-3 mt-3">
                <div><strong>Primary Source:</strong> {draft.DATA_SOURCE_PRIORITY === 'jolpica' ? 'Jolpica provides official F1 timing data and results' : draft.DATA_SOURCE_PRIORITY === 'openf1' ? 'OpenF1 offers real-time telemetry and session data' : draft.DATA_SOURCE_PRIORITY === 'fastf1' ? 'FastF1 delivers comprehensive historical race data' : 'Local cached data for offline operation'}</div>
                <div><strong>Cache TTL:</strong> {draft.CACHE_TTL_SECONDS}s — responses cached to reduce API calls and improve speed</div>
                <div><strong>Update Interval:</strong> Every {draft.LIVE_UPDATE_INTERVAL}s during active sessions</div>
                <div><strong>Fallback Chain:</strong> Primary → Secondary → Tertiary → Local cache (automatic)</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Live Preview for Appearance */}
      {currentGroup.id === 'appearance' && (
        <div className="card p-6">
          <div className="f1-display font-bold mb-3">Live Preview</div>
          <div className="p-4 rounded-xl border" style={{ background:'var(--surface)', borderColor:'var(--border)'}}>
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded flex items-center justify-center text-white font-black" style={{ background:'var(--red)'}}>F1</span>
              <span className="f1-display font-bold" style={{ color:'var(--text)'}}>Sample Text</span>
              <span className="ml-auto px-2 py-1 rounded-full text-white fs-11" style={{ background:'var(--red)'}}>LIVE</span>
            </div>
            <button className="btn-primary mt-3 w-full sm:w-auto" style={{ background:'var(--red)'}}>Preview Button</button>
            <div className="mt-3 h-2 rounded-full overflow-hidden" style={{ background:'var(--surface-alt)'}}>
              <span className="h-full block w-2/3" style={{ background:'var(--red)'}} />
            </div>
            <div className="fs-11 text-sub mt-2" style={{ color:'var(--sub)'}}>Secondary text · <span style={{ color:'var(--text)'}}>primary text</span></div>
          </div>
          <div className="fs-11 text-sub mt-2">Colors apply instantly as you change them. Click Save to persist to backend.</div>
        </div>
      )}

      <div className="card p-4 flex flex-wrap items-center gap-3 fs-11 text-sub">
        <span>Engine settings stored locally and synced to backend on save</span>
        <span className="ml-auto">Changes take effect on next prediction run</span>
      </div>
    </div>
  )
}
