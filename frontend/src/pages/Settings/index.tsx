import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

type Group = { id:string; label:string; icon:string; fields:string[]; desc?:string }

const COLOR_FIELDS = new Set(['PRIMARY_COLOR','BACKGROUND','SURFACE','SURFACE_ALT','BORDER','TEXT','SUB','NAVY','NAVY_LIGHT','RED','RED_DARK'])
const COLOR_DEFAULTS: Record<string,string> = {
  PRIMARY_COLOR: '#E10600', BACKGROUND: '#F4F5F7', SURFACE: '#FFFFFF', SURFACE_ALT: '#EEF0F3',
  BORDER: '#E3E5EA', TEXT: '#15151E', SUB: '#6B7280', NAVY: '#16233F', NAVY_LIGHT: '#22345A',
}

const FIELD_HELP: Record<string,string> = {
  PRIMARY_COLOR: 'Primary action color — buttons, links, active nav. Live preview below.',
  BACKGROUND: 'Page background. Light #F4F5F7 vs dark #0A0C10.',
  SURFACE: 'Card surface. Must contrast with background.',
  TEXT: 'Primary text color.',
  CHAOS_LEVEL_DEFAULT: 'Monte Carlo chaos 0 (deterministic) → 100 (uniform). Linear blend.',
  MONTE_CARLO_SIMULATIONS: 'Default sims per prediction — 100 to 50,000. Higher = smoother but slower.',
  GRID_WEIGHT_DEFAULT: 'Grid vs pace weight. 55 default; lower = 2026 closer racing.',
  ENABLE_ENSEMBLE: 'OOF ensemble (when trained) 45% ML + 55% MC.',
  MODEL_VERSION: 'Champion model id — bump invalidates prediction cache.',
  CACHE_TTL_SECONDS: 'API cache TTL — 300s default.',
  REDIS_REQUIRED: 'Fail loudly if Redis unavailable (prod true).',
  CORS_ORIGINS: 'Comma-separated allowed origins. * = allow all (dev).',
  RATE_LIMIT_PREDICTIONS: 'Per-route limit — 60/hour for predictions.',
  AI_PROVIDER: 'huggingface | openai | ollama',
  AI_MODEL_TEMPERATURE: '0.0 deterministic → 1.0 creative',
  SEASON_YEAR: 'Active season — 2026.',
  LIVE_UPDATE_INTERVAL: 'Background updater seconds — 300s.',
}

function applyColors(colors: Record<string,string>) {
  const map: Record<string,string> = {
    PRIMARY_COLOR: '--red', BACKGROUND: '--bg', SURFACE: '--surface', SURFACE_ALT: '--surface-alt',
    BORDER: '--border', TEXT: '--text', SUB: '--sub', NAVY: '--navy', NAVY_LIGHT: '--navy-light',
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
  if (isBool) {
    return <button onClick={()=> onChange(!value)} className={`f1-switch ${value?'is-on':''}`} aria-label={name}><span className="knob" /></button>
  }
  if (isColor) {
    return (
      <div className="flex items-center gap-2">
        <input type="color" value={typeof value==='string' && value.startsWith('#') ? value : '#E10600'} onChange={e=> onChange(e.target.value)} className="w-10 h-8 rounded border p-0" style={{ borderColor:'var(--border)'}} />
        <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input flex-1 font-mono text-xs" placeholder="#RRGGBB" />
      </div>
    )
  }
  if (isNumber) {
    return <input type="number" value={value} onChange={e=> onChange(e.target.value===''? '' : Number(e.target.value))} className="f1-input" />
  }
  if (String(name).includes('DATABASE_URL') || String(name).includes('CORS') || String(name).includes('URL')) {
    return <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input font-mono text-xs" />
  }
  if (String(value).length > 60) {
    return <textarea value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input min-h-[60px] text-xs font-mono" />
  }
  return <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input" />
}

export function SettingsPage(){
  // Fast load: initialize from local cache synchronously so first paint is instant, then merge API
  const [settings, setSettings] = useState<Record<string,any>>(()=>{
    try{
      const local = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
      const ui = JSON.parse(localStorage.getItem('f1-ui-prefs')||'{}')
      const cached = (()=>{ try{ return JSON.parse(localStorage.getItem('f1-settings-cache')||'{}')}catch{return {}}})()
      return { ...COLOR_DEFAULTS, CHAOS_LEVEL_DEFAULT:50, MONTE_CARLO_SIMULATIONS:10000, GRID_WEIGHT_DEFAULT:55, CACHE_ENABLED:true, ...cached, ...local, ...ui }
    }catch{ return { ...COLOR_DEFAULTS, CHAOS_LEVEL_DEFAULT:50, MONTE_CARLO_SIMULATIONS:10000 } }
  })
  const [schema, setSchema] = useState<{ groups:Group[] } | null>(null)
  const [draft, setDraft] = useState<Record<string,any>>(()=>{
    try{
      const local = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
      const cached = (()=>{ try{ return JSON.parse(localStorage.getItem('f1-settings-cache')||'{}')}catch{return {}}})()
      return { ...COLOR_DEFAULTS, CHAOS_LEVEL_DEFAULT:50, ...cached, ...local }
    }catch{ return { ...COLOR_DEFAULTS } }
  })
  const [active, setActive] = useState<string>('appearance')
  const [filter, setFilter] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<string|null>(null)
  const [globalResults, setGlobalResults] = useState<any[]|null>(null)
  const [apiReady, setApiReady] = useState(false)
  const [surface, setSurface] = useState<'preferences'|'admin'>('preferences')
  const [adminToken, setAdminToken] = useState<string>(()=> {
    try{ return localStorage.getItem('f1-admin-token')||'' }catch{ return '' }
  })
  const [favoriteDriver, setFavoriteDriver] = useState<string>(()=>{
    try{ return localStorage.getItem('f1-favorite-driver')||'' }catch{ return '' }
  })

  // Apply cached colors immediately for instant paint
  useEffect(()=>{
    try{
      const local = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
      if (Object.keys(local).length) applyColors(local)
      else applyColors(COLOR_DEFAULTS)
    }catch{ applyColors(COLOR_DEFAULTS) }
  },[])

  // Load backend + local colors — non-blocking, merges when ready
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
      setApiReady(true)
    }).catch(()=> { if(!cancelled) { setMsg('Backend settings unavailable — using local cache'); setApiReady(true)} })
    api.get<any>('/api/v1/settings/schema').then(setSchema).catch(()=>{})
    // also load frontend-only prefs
    try{
      const ui = JSON.parse(localStorage.getItem('f1-ui-prefs')||'{}')
      if (ui.fontScale) document.documentElement.style.webKitTextSizeAdjust = ui.fontScale
    }catch{}
    return ()=> { cancelled=true }
  },[])

  const baseGroups: Group[] = schema?.groups || [
    { id:'appearance', label:'Appearance', icon:'🎨', desc:'Colors, theme, live preview', fields:['PRIMARY_COLOR','BACKGROUND','SURFACE','TEXT','BORDER']},
    { id:'engine', label:'Engine', icon:'⚙️', desc:'Monte Carlo & weights', fields:['MONTE_CARLO_SIMULATIONS','CHAOS_LEVEL_DEFAULT']},
  ]

  // Augment with frontend-only massive tunings
  const groups: Group[] = useMemo(()=>{
    const extra: Group[] = [
      { id:'appearance', label:'Appearance', icon:'🎨', desc:'Colors, theme, typography — live preview', fields:['PRIMARY_COLOR','BACKGROUND','SURFACE','SURFACE_ALT','BORDER','TEXT','SUB','NAVY','NAVY_LIGHT']},
      { id:'quick', label:'Quick', icon:'⚡', desc:'Most used — one-click', fields:['THEME_MODE','PRIMARY_COLOR','MONTE_CARLO_SIMULATIONS','CHAOS_LEVEL_DEFAULT','GRID_WEIGHT_DEFAULT','CACHE_ENABLED']},
      { id:'accessibility', label:'Accessibility', icon:'♿', desc:'Font scale, motion, contrast', fields:['UI_FONT_SCALE','UI_REDUCED_MOTION','UI_HIGH_CONTRAST','UI_DYSLEXIA_FONT']},
    ]
    // Merge base groups but prioritize appearance/quick overrides
    const map = new Map<string,Group>()
    extra.forEach(g=> map.set(g.id, g))
    baseGroups.forEach(g=>{
      if (map.has(g.id)) {
        const cur = map.get(g.id)!
        map.set(g.id, { ...g, fields: Array.from(new Set([...cur.fields, ...g.fields])), desc: cur.desc || g.desc })
      } else map.set(g.id, g)
    })
    // Add accessibility if not in base
    if (!map.has('accessibility')) map.set('accessibility', extra[2])
    return Array.from(map.values())
  }, [baseGroups])

  const filteredGroups = useMemo(()=>{
    if (surface==='preferences') return groups.filter(g=> ['appearance','quick','accessibility'].includes(g.id))
    return groups
  }, [groups, surface])
  // Ensure active is valid for current surface
  useEffect(()=>{
    if (!filteredGroups.find(g=> g.id===active) && filteredGroups.length) setActive(filteredGroups[0].id)
  }, [filteredGroups, active])
  const currentGroup = useMemo(()=> filteredGroups.find(g=> g.id===active) || filteredGroups[0] || groups[0], [filteredGroups, groups, active])

  const filteredFields = useMemo(()=>{
    if (!currentGroup) return []
    const q = filter.toLowerCase().trim()
    if (!q) return currentGroup.fields
    // global search across all groups if filter active
    if (q.length>1) {
      const allFields = groups.flatMap(g=> g.fields)
      const matches = allFields.filter(f=> f.toLowerCase().includes(q) || String(draft[f]??'').toLowerCase().includes(q) || (FIELD_HELP[f]||'').toLowerCase().includes(q))
      if (currentGroup.id==='quick' || filter.length>2) return matches.slice(0,40)
    }
    return currentGroup.fields.filter(f=> !q || f.toLowerCase().includes(q) || String(draft[f]??'').toLowerCase().includes(q) || (FIELD_HELP[f]||'').toLowerCase().includes(q))
  }, [currentGroup, filter, draft, groups])

  // Global search results popup
  useEffect(()=>{
    if (filter.length>=2) {
      const q = filter.toLowerCase()
      const all = groups.flatMap(g=> g.fields.map(f=> ({ field:f, group:g.label, value: draft[f], help: FIELD_HELP[f]||'' })))
      const res = all.filter(r=> r.field.toLowerCase().includes(q) || String(r.value||'').toLowerCase().includes(q) || r.help.toLowerCase().includes(q)).slice(0,8)
      setGlobalResults(res.length? res : null)
    } else setGlobalResults(null)
  }, [filter, draft, groups])

  const setField = (k:string, v:any)=>{
    setDraft(d=> ({...d, [k]: v}))
    if (COLOR_FIELDS.has(k)) {
      applyColors({ [k]: v })
      try{
        const prev = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
        localStorage.setItem('f1-settings-colors', JSON.stringify({...prev, [k]: v}))
      }catch{}
    }
    if (k==='UI_FONT_SCALE') {
      document.documentElement.style.fontSize = v==='large'?'17px': v==='small'?'13px':'14px'
      try{ const ui=JSON.parse(localStorage.getItem('f1-ui-prefs')||'{}'); localStorage.setItem('f1-ui-prefs', JSON.stringify({...ui, fontScale: v}))}catch{}
    }
    if (k==='UI_REDUCED_MOTION') {
      document.documentElement.style.setProperty('--motion', v? '0ms':'')
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
      // Send admin token if in admin surface or if diff contains non-safe fields
      const headers: Record<string,string> = {}
      if (adminToken) headers['X-Admin-Token'] = adminToken
      const res = await fetch('/api/v1/settings', { method:'POST', headers: { 'Content-Type':'application/json', ...headers }, body: JSON.stringify(diff) }).then(async r=>{
        if (!r.ok) {
          const j = await r.json().catch(()=> ({}))
          throw new Error(j?.error?.message || `Save failed ${r.status}`)
        }
        return r.json()
      })
      setSettings(res.settings)
      setDraft(res.settings)
      try{ localStorage.setItem('f1-settings-cache', JSON.stringify(res.settings)) }catch{}
      setMsg(`Saved ${Object.keys(diff).length} fields — ${surface==='admin'?'admin':'preferences'} — overrides live until restart.`)
      const colors: Record<string,string> = {}
      Object.keys(COLOR_DEFAULTS).forEach(k=> { if (draft[k]) colors[k]=String(draft[k]) })
      if (Object.keys(colors).length) localStorage.setItem('f1-settings-colors', JSON.stringify(colors))
    }catch(e:any){ setMsg(e.message || 'Save failed — admin token required for non-safe fields?')}
    finally{ setSaving(false)}
  }

  const reset = async()=>{
    if (!confirm('Reset all runtime overrides? This clears backend + local colors.')) return
    setSaving(true)
    try{
      const headers: Record<string,string> = {}
      if (adminToken) headers['X-Admin-Token'] = adminToken
      const r = await fetch('/api/v1/settings/reset', { method:'POST', headers: { 'Content-Type':'application/json', ...headers }, body: JSON.stringify({}) }).then(async r=>{
        if (!r.ok) {
          const j = await r.json().catch(()=> ({}))
          throw new Error(j?.error?.message || `Reset failed ${r.status}`)
        }
        return r.json()
      })
      setSettings(r.settings); setDraft(r.settings)
      try{ localStorage.removeItem('f1-settings-cache')}catch{}
      localStorage.removeItem('f1-settings-colors')
      localStorage.removeItem('f1-ui-prefs')
      applyColors(COLOR_DEFAULTS)
      document.documentElement.style.fontSize=''
      setMsg('Reset — overrides and local colors cleared.')
    }catch(e:any){ setMsg(e.message)}
    finally{ setSaving(false)}
  }

  const applyPreset = (name:string)=>{
    const presets: Record<string, Record<string,any>> = {
      conservative: { CHAOS_LEVEL_DEFAULT: 20, GRID_WEIGHT_DEFAULT: 65, WET_INFLUENCE_DEFAULT: 30, RELIABILITY_INFLUENCE_DEFAULT: 70, STRATEGY_AGGRESSIVENESS_DEFAULT: 30, MONTE_CARLO_SIMULATIONS: 8000 },
      aggressive: { CHAOS_LEVEL_DEFAULT: 75, GRID_WEIGHT_DEFAULT: 40, WET_INFLUENCE_DEFAULT: 70, RELIABILITY_INFLUENCE_DEFAULT: 30, STRATEGY_AGGRESSIVENESS_DEFAULT: 80, MONTE_CARLO_SIMULATIONS: 15000 },
      qualifying: { CHAOS_LEVEL_DEFAULT: 25, GRID_WEIGHT_DEFAULT: 75, MONTE_CARLO_SIMULATIONS: 5000, ENABLE_ENSEMBLE: true },
      race: { CHAOS_LEVEL_DEFAULT: 50, GRID_WEIGHT_DEFAULT: 55, MONTE_CARLO_SIMULATIONS: 12000, ENABLE_ENSEMBLE: true },
      dark: { PRIMARY_COLOR: '#FF3B30', BACKGROUND: '#0A0C10', SURFACE: '#15181F', SURFACE_ALT: '#1C2028', BORDER: '#2B3039', TEXT: '#F1F2F5', SUB:'#9BA2AF' },
      light: { PRIMARY_COLOR: '#E10600', BACKGROUND: '#F4F5F7', SURFACE: '#FFFFFF', SURFACE_ALT: '#EEF0F3', BORDER: '#E3E5EA', TEXT: '#15151E', SUB:'#6B7280' },
      performance: { CACHE_ENABLED: true, CACHE_TTL_SECONDS: 600, CACHE_MAX_SIZE: 2000, API_RESPONSE_COMPRESSION_ENABLED: true, MODEL_INFERENCE_OPTIMIZATION_ENABLED: true },
      broadcast: { PRIMARY_COLOR: '#E10600', UI_FONT_SCALE:'large', UI_REDUCED_MOTION:false },
    }
    const p = presets[name]
    if (!p) return
    const next = {...draft, ...p}
    setDraft(next)
    if (p.PRIMARY_COLOR) applyColors(p)
    setMsg(`Preset "${name}" staged — hit Save to persist.`)
  }

  const exportJson = ()=>{
    const blob = new Blob([JSON.stringify(draft, null, 2)], { type:'application/json'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href=url; a.download='f1-settings.json'; a.click(); URL.revokeObjectURL(url)
  }
  const importJson = (e:any)=>{
    const file = e.target.files?.[0]; if (!file) return
    const reader = new FileReader()
    reader.onload = ()=>{
      try{
        const obj = JSON.parse(String(reader.result))
        setDraft(d=> ({...d, ...obj}))
        setMsg(`Imported ${Object.keys(obj).length} fields — hit Save.`)
      }catch{ setMsg('Invalid JSON')}
    }
    reader.readAsText(file)
  }

  // Fast load: show UI immediately with cached defaults, merge API when ready
  const isInitialLoading = !settings || !Object.keys(settings).length
  // Keep rendering even while loading — use draft defaults

  const sims = Number(draft.MONTE_CARLO_SIMULATIONS||1000)
  const perfImpact = sims>20000? 'High — ~1.2s per prediction, juicy smooth': sims>8000? 'Balanced — ~0.4s' : 'Snappy — ~0.15s'

  return (
    <div className="px-4 sm:px-8 py-6 max-w-6xl mx-auto space-y-6">
      {/* Hero */}
      <div className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ background:'var(--red)'}} />
              <span className="fs-11 font-bold tracking-widest" style={{ color:'var(--red)'}}>CONTROL CENTER — EVERYTHING IS TUNABLE</span>
            </div>
            <h1 className="f1-display text-2xl font-black mt-1">Settings</h1>
            <p className="text-sub fs-11 mt-1 max-w-2xl">Change app colors live, swap models, tune Monte Carlo, cache, data sources, security, monitoring — <strong>massive tunings</strong> for the entire project. Overrides are in-memory (Redis mirrored) and survive until restart; <code className="f1-mono fs-11">.env</code> is source of truth on reboot. Search globally, use presets, export/import.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={save} disabled={saving} className="btn-primary" style={{ background:'#16a34a'}}>{saving?'Saving…':'Save changes'}</button>
            <button onClick={reset} className="btn-ghost">Reset</button>
            <button onClick={exportJson} className="btn-ghost">Export JSON</button>
            <label className="btn-ghost cursor-pointer">Import JSON<input type="file" accept=".json" onChange={importJson} className="hidden"/></label>
          </div>
        </div>
        {msg && <div className="mt-3 p-2 rounded-lg surface-alt fs-11">{msg}</div>}
      </div>

      {/* Surface split — Preferences (per-user, safe) vs Admin (global, requires token) */}
      <div className="card p-3 flex flex-wrap items-center gap-3">
        <div className="flex gap-2">
          <button onClick={()=> setSurface('preferences')} className={`px-4 py-2 rounded-full fs-11 font-bold ${surface==='preferences'?'bg-black text-white':'bg-white border'}`}>Preferences — Personal</button>
          <button onClick={()=> setSurface('admin')} className={`px-4 py-2 rounded-full fs-11 font-bold ${surface==='admin'?'bg-black text-white':'bg-white border'}`}>Admin Console — Global</button>
        </div>
        <span className="fs-11 text-sub">{surface==='preferences'?'Safe, per-device — theme, favorite driver, no auth needed':'Global, affects every visitor — requires X-Admin-Token'}</span>
        {surface==='admin' && (
          <div className="ml-auto flex items-center gap-2">
            <input value={adminToken} onChange={e=> { setAdminToken(e.target.value); try{ localStorage.setItem('f1-admin-token', e.target.value)}catch{} }} placeholder="X-Admin-Token (SECRET_KEY)" className="f1-input w-48 font-mono text-xs" />
            <span className="fs-11 px-2 py-1 rounded-full" style={{ background: adminToken?'#dcfce7':'#fee2e2', color: adminToken?'#16a34a':'#ef4444'}}>{adminToken?'Token set':'No token — writes to non-safe fields will 403'}</span>
          </div>
        )}
      </div>

      {/* Favorite driver — cross-cutting preference */}
      {surface==='preferences' && (
        <div className="card p-4">
          <div className="f1-display font-bold">Favorite Driver — personalizes every page</div>
          <p className="fs-11 text-sub">Settings stores a favorite driver/constructor — every other section (Predictions, Standings, H2H, Fantasy) can highlight/pin that driver. Turns Settings from isolated config into personalization.</p>
          <div className="flex gap-2 mt-3">
            <input value={favoriteDriver} onChange={e=> { setFavoriteDriver(e.target.value.toUpperCase()); try{ localStorage.setItem('f1-favorite-driver', e.target.value.toUpperCase())}catch{} }} placeholder="e.g. VER, HAM, LEC" className="f1-input w-32 font-mono" />
            <button onClick={()=> { try{ localStorage.setItem('f1-favorite-driver', favoriteDriver); setMsg(`Favorite driver set to ${favoriteDriver} — other pages will highlight it`)}catch{} }} className="btn-primary" style={{ background:'#16a34a'}}>Save favorite</button>
            <span className="fs-11 text-sub self-center">Current: {favoriteDriver||'—'}</span>
          </div>
        </div>
      )}

      {/* Quick bar + Live preview */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card p-4">
          <div className="f1-display font-bold">Quick — Most used</div>
          <div className="grid sm:grid-cols-3 gap-3 mt-3">
            <label className="fs-11 font-bold flex flex-col gap-1">Primary <input type="color" value={String(draft.PRIMARY_COLOR||'#E10600')} onChange={e=> setField('PRIMARY_COLOR', e.target.value)} className="w-full h-8 rounded border" /></label>
            <label className="fs-11 font-bold flex flex-col gap-1">Sims {sims}<input type="range" min={100} max={50000} value={sims} onChange={e=> setField('MONTE_CARLO_SIMULATIONS', parseInt(e.target.value))} className="f1-range"/></label>
            <label className="fs-11 font-bold flex flex-col gap-1">Chaos {draft.CHAOS_LEVEL_DEFAULT}<input type="range" min={0} max={100} value={Number(draft.CHAOS_LEVEL_DEFAULT||50)} onChange={e=> setField('CHAOS_LEVEL_DEFAULT', parseInt(e.target.value))} className="f1-range"/></label>
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            <button onClick={()=> applyPreset('conservative')} className="badge">Conservative</button>
            <button onClick={()=> applyPreset('aggressive')} className="badge">Aggressive</button>
            <button onClick={()=> applyPreset('qualifying')} className="badge">Qualifying</button>
            <button onClick={()=> applyPreset('race')} className="badge">Race</button>
            <button onClick={()=> applyPreset('dark')} className="badge">Dark</button>
            <button onClick={()=> applyPreset('light')} className="badge">Light</button>
            <button onClick={()=> applyPreset('performance')} className="badge">Performance</button>
            <span className="fs-11 text-sub ml-auto">{perfImpact}</span>
          </div>
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">Live preview</div>
          <div className="mt-3 p-3 rounded-xl border" style={{ background:'var(--surface)', borderColor:'var(--border)'}}>
            <div className="flex items-center gap-2"><span className="w-6 h-6 rounded flex items-center justify-center text-white font-black" style={{ background:'var(--red)'}}>F1</span><span className="f1-display font-bold" style={{ color:'var(--text)'}}>Button</span><span className="ml-auto px-2 py-0.5 rounded-full text-white fs-11" style={{ background:'var(--red)'}}>LIVE</span></div>
            <button className="btn-primary mt-3 w-full" style={{ background:'var(--red)'}}>Preview Primary</button>
            <div className="mt-2 h-2 rounded-full overflow-hidden" style={{ background:'var(--surface-alt)'}}><span className="h-full block w-2/3" style={{ background:'var(--red)'}} /></div>
            <div className="fs-11 text-sub mt-1" style={{ color:'var(--sub)'}}>Text secondary · <span style={{ color:'var(--text)'}}>primary text</span></div>
          </div>
          <div className="fs-11 text-sub mt-2">Colors apply live as you pick them — no save needed for preview. Save persists to backend.</div>
        </div>
      </div>

      {/* Search */}
      <div className="card p-4">
        <div className="flex gap-3">
          <input value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Global search — e.g. CHAOS, REDIS, CORS, AI, font" className="f1-input flex-1" />
          <span className="fs-11 text-sub self-center">{Object.keys(draft).length} keys</span>
        </div>
        {globalResults && (
          <div className="mt-3 grid sm:grid-cols-2 gap-2">
            {globalResults.map((r:any)=> (
              <button key={r.field} onClick={()=> { setActive(groups.find(g=> g.fields.includes(r.field))?.id || active); setFilter(''); document.getElementById(`field-${r.field}`)?.scrollIntoView({behavior:'smooth', block:'center'})}} className="text-left p-2 rounded-lg surface-alt hover:bg-black/10">
                <div className="f1-mono text-xs font-bold">{r.field}</div>
                <div className="fs-11 text-sub truncate">{r.help || String(r.value).slice(0,60)}</div>
                <div className="fs-11 opacity-60">{r.group}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-[220px_1fr] gap-4">
        {/* Left nav — filtered by surface */}
        <div className="card p-2 h-fit">
          {filteredGroups.map(g=> (
            <button key={g.id} onClick={()=> setActive(g.id)} className={`w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 ${active===g.id?'bg-black text-white':'hover:bg-black/5'}`}>
              <span>{g.icon}</span><span className="fs-11 font-bold">{g.label}</span><span className="ml-auto fs-11 opacity-60">{g.fields.length}</span>
            </button>
          ))}
          <div className="mt-3 p-3 surface-alt rounded-lg fs-11 text-sub">
            Tip: search above is global — finds in any group + help text. Colors preview live; engine fields affect next <code className="f1-mono">POST /predictions</code>.
          </div>
          <div className="mt-3 p-3 rounded-lg border fs-11" style={{ borderColor:'var(--border)'}}>
            <div className="font-bold">Power tools</div>
            <div className="flex flex-wrap gap-1 mt-2">
              <button onClick={()=> setField('CACHE_ENABLED', !draft.CACHE_ENABLED)} className="badge">Toggle cache</button>
              <button onClick={()=> setField('MONITORING_ENABLED', !draft.MONITORING_ENABLED)} className="badge">Monitoring</button>
              <button onClick={()=> setField('ENABLE_ENSEMBLE', !draft.ENABLE_ENSEMBLE)} className="badge">Ensemble</button>
            </div>
          </div>
        </div>

        {/* Fields */}
        <div className="card p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="f1-display font-bold">{currentGroup.label}</h2>
              <div className="fs-11 text-sub">{currentGroup.desc}</div>
            </div>
            <span className="fs-11 text-sub">{filteredFields.length} / {currentGroup.fields.length} fields</span>
          </div>
          <p className="fs-11 text-sub mt-1">Group <code className="f1-mono fs-11">{currentGroup.id}</code> — patchable via <code className="f1-mono fs-11">POST /api/v1/settings</code>. Help per field below.</p>

          <div className="mt-4 space-y-3">
            {filteredFields.map(name=>{
              const v = draft[name]
              const dirty = settings && JSON.stringify(settings[name]) !== JSON.stringify(v)
              return (
                <div key={name} id={`field-${name}`} className={`p-3 rounded-lg ${dirty?'border' : 'border border-transparent'}`} style={{ borderColor: dirty ? 'var(--amber)' : undefined, background: dirty? 'var(--surface-alt)' : undefined }}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="f1-mono text-xs font-bold break-all">{name}</span>
                        {dirty && <span className="fs-11 px-1.5 py-0.5 rounded bg-amber-500 text-white">dirty</span>}
                        {typeof v === 'boolean' && <span className="fs-11 text-sub">{v?'ON':'OFF'}</span>}
                      </div>
                      <div className="fs-11 text-sub mt-0.5">{FIELD_HELP[name] || `Runtime override for ${name}`}</div>
                      <div className="fs-11 text-sub break-all opacity-60">Current: <span className="font-mono">{JSON.stringify(settings[name])}</span></div>
                    </div>
                    <div className="w-[200px] sm:w-[260px] shrink-0">
                      <FieldInput name={name} value={v} onChange={(nv)=> setField(name, nv)} />
                    </div>
                  </div>
                </div>
              )
            })}
            {filteredFields.length===0 && <div className="p-8 text-center opacity-60 fs-11">No fields match “{filter}” — try global search above.</div>}
          </div>

          {/* Accessibility quick */}
          {currentGroup.id==='accessibility' && (
            <div className="mt-6 grid sm:grid-cols-2 gap-3">
              <label className="fs-11 font-bold flex flex-col gap-1">Font scale<select value={String(draft.UI_FONT_SCALE||'medium')} onChange={e=> setField('UI_FONT_SCALE', e.target.value)} className="f1-select"><option value="small">Small</option><option value="medium">Medium</option><option value="large">Large</option></select></label>
              <label className="fs-11 font-bold flex items-center gap-2">Reduced motion <input type="checkbox" checked={!!draft.UI_REDUCED_MOTION} onChange={e=> setField('UI_REDUCED_MOTION', e.target.checked)} /></label>
              <label className="fs-11 font-bold flex items-center gap-2">High contrast <input type="checkbox" checked={!!draft.UI_HIGH_CONTRAST} onChange={e=> setField('UI_HIGH_CONTRAST', e.target.checked)} /></label>
              <label className="fs-11 font-bold flex items-center gap-2">Dyslexia font <input type="checkbox" checked={!!draft.UI_DYSLEXIA_FONT} onChange={e=> setField('UI_DYSLEXIA_FONT', e.target.checked)} /></label>
            </div>
          )}

          <details className="mt-6">
            <summary className="fs-11 font-bold cursor-pointer">Raw JSON — all settings (power users)</summary>
            <textarea value={JSON.stringify(draft, null, 2)} onChange={e=>{
              try{ const obj = JSON.parse(e.target.value); setDraft(obj)}catch{}
            }} className="f1-input mt-2 min-h-[260px] font-mono text-[11px] leading-relaxed" />
          </details>
        </div>
      </div>

      <div className="card p-4 flex flex-wrap items-center gap-3 fs-11 text-sub">
        <span>Source: <code className="f1-mono">backend/app/config/settings.py</code> + overrides</span>
        <span className="ml-auto">Docs: <code className="f1-mono">GET /api/v1/settings/schema</code> &amp; <code>GET /docs</code></span>
      </div>
    </div>
  )
}
