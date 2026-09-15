import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

type Group = { id:string; label:string; icon:string; fields:string[] }

const COLOR_FIELDS = new Set(['PRIMARY_COLOR','BACKGROUND','SURFACE','SURFACE_ALT','BORDER','TEXT','SUB','NAVY','NAVY_LIGHT','RED','RED_DARK'])
const COLOR_DEFAULTS: Record<string,string> = {
  PRIMARY_COLOR: '#E10600', BACKGROUND: '#F4F5F7', SURFACE: '#FFFFFF', SURFACE_ALT: '#EEF0F3',
  BORDER: '#E3E5EA', TEXT: '#15151E', SUB: '#6B7280', NAVY: '#16233F', NAVY_LIGHT: '#22345A',
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
  // also update legacy primary vars
  if (colors.PRIMARY_COLOR) {
    document.documentElement.style.setProperty('--red', colors.PRIMARY_COLOR)
    // derive dark
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
    return (
      <button onClick={()=> onChange(!value)} className={`f1-switch ${value?'is-on':''}`} aria-label={name}>
        <span className="knob" />
      </button>
    )
  }
  if (isColor) {
    return (
      <div className="flex items-center gap-2">
        <input type="color" value={typeof value==='string' && value.startsWith('#') ? value : '#E10600'} onChange={e=> onChange(e.target.value)} className="w-10 h-8 rounded border p-0" style={{ borderColor:'var(--border)'}} />
        <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input flex-1" placeholder="#RRGGBB" />
      </div>
    )
  }
  if (isNumber) {
    return <input type="number" value={value} onChange={e=> onChange(e.target.value===''? '' : Number(e.target.value))} className="f1-input" />
  }
  // string / other
  if (String(name).includes('DATABASE_URL') || String(name).includes('CORS') || String(name).includes('URL')) {
    return <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input font-mono text-xs" />
  }
  if (String(value).length > 60) {
    return <textarea value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input min-h-[60px] text-xs font-mono" />
  }
  return <input value={String(value??'')} onChange={e=> onChange(e.target.value)} className="f1-input" />
}

export function SettingsPage(){
  const [settings, setSettings] = useState<Record<string,any> | null>(null)
  const [schema, setSchema] = useState<{ groups:Group[] } | null>(null)
  const [draft, setDraft] = useState<Record<string,any>>({})
  const [active, setActive] = useState<string>('appearance')
  const [filter, setFilter] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<string|null>(null)

  // Load backend + local colors
  useEffect(()=>{
    api.get<any>('/api/v1/settings').then(r=>{
      setSettings(r.settings)
      setDraft(r.settings)
      // hydrate colors from backend overrides + localStorage
      const local = (()=>{ try{ return JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')}catch{return {}}})()
      const colors: Record<string,string> = {}
      Object.keys(COLOR_DEFAULTS).forEach(k=> {
        const v = r.settings[k] || local[k] || COLOR_DEFAULTS[k]
        if (v) colors[k]=String(v)
      })
      applyColors(colors)
    }).catch(()=> setMsg('Backend settings unavailable — using local only'))
    api.get<any>('/api/v1/settings/schema').then(setSchema).catch(()=>{})
    // Also apply saved local colors immediately
    try{
      const local = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
      if (Object.keys(local).length) applyColors(local)
    }catch{}
  },[])

  const groups: Group[] = schema?.groups || [
    { id:'appearance', label:'Appearance', icon:'🎨', fields:['PRIMARY_COLOR','BACKGROUND','SURFACE','TEXT','BORDER']},
    { id:'engine', label:'Engine', icon:'⚙️', fields:['MONTE_CARLO_SIMULATIONS','CHAOS_LEVEL_DEFAULT']},
  ]

  const currentGroup = useMemo(()=> groups.find(g=> g.id===active) || groups[0], [groups, active])

  const filteredFields = useMemo(()=>{
    if (!currentGroup) return []
    const q = filter.toLowerCase()
    return currentGroup.fields.filter(f=> !q || f.toLowerCase().includes(q) || String(draft[f]??'').toLowerCase().includes(q))
  }, [currentGroup, filter, draft])

  const setField = (k:string, v:any)=>{
    setDraft(d=> ({...d, [k]: v}))
    if (COLOR_FIELDS.has(k)) {
      const upd = { [k]: v }
      applyColors(upd)
      // persist locally for instant reload
      try{
        const prev = JSON.parse(localStorage.getItem('f1-settings-colors')||'{}')
        localStorage.setItem('f1-settings-colors', JSON.stringify({...prev, [k]: v}))
      }catch{}
    }
  }

  const save = async()=>{
    setSaving(true); setMsg(null)
    try{
      // Only send dirty diff
      const diff: Record<string,any> = {}
      const base = settings || {}
      Object.entries(draft).forEach(([k,v])=>{
        if (JSON.stringify(base[k]) !== JSON.stringify(v)) diff[k]=v
      })
      if (!Object.keys(diff).length) { setMsg('No changes to save'); setSaving(false); return }
      const res = await api.post<any>('/api/v1/settings', diff)
      setSettings(res.settings)
      setDraft(res.settings)
      setMsg(`Saved ${Object.keys(diff).length} fields — overrides live until restart.`)
      // also persist colors locally
      const colors: Record<string,string> = {}
      Object.keys(COLOR_DEFAULTS).forEach(k=> { if (draft[k]) colors[k]=String(draft[k]) })
      if (Object.keys(colors).length) localStorage.setItem('f1-settings-colors', JSON.stringify(colors))
    }catch(e:any){ setMsg(e.message || 'Save failed')}
    finally{ setSaving(false)}
  }

  const reset = async()=>{
    if (!confirm('Reset all runtime overrides?')) return
    setSaving(true)
    try{
      const r = await api.post<any>('/api/v1/settings/reset', {})
      setSettings(r.settings); setDraft(r.settings)
      localStorage.removeItem('f1-settings-colors')
      // revert CSS to defaults
      applyColors(COLOR_DEFAULTS)
      setMsg('Reset — overrides cleared.')
    }catch(e:any){ setMsg(e.message)}
    finally{ setSaving(false)}
  }

  const applyPreset = (name:string)=>{
    const presets: Record<string, Record<string,any>> = {
      conservative: { CHAOS_LEVEL_DEFAULT: 20, GRID_WEIGHT_DEFAULT: 65, WET_INFLUENCE_DEFAULT: 30, RELIABILITY_INFLUENCE_DEFAULT: 70, STRATEGY_AGGRESSIVENESS_DEFAULT: 30, MONTE_CARLO_SIMULATIONS: 10000 },
      aggressive: { CHAOS_LEVEL_DEFAULT: 75, GRID_WEIGHT_DEFAULT: 40, WET_INFLUENCE_DEFAULT: 70, RELIABILITY_INFLUENCE_DEFAULT: 30, STRATEGY_AGGRESSIVENESS_DEFAULT: 80, MONTE_CARLO_SIMULATIONS: 15000 },
      qualifying: { CHAOS_LEVEL_DEFAULT: 25, GRID_WEIGHT_DEFAULT: 75, MONTE_CARLO_SIMULATIONS: 5000, ENABLE_ENSEMBLE: true },
      race: { CHAOS_LEVEL_DEFAULT: 50, GRID_WEIGHT_DEFAULT: 55, MONTE_CARLO_SIMULATIONS: 12000, ENABLE_ENSEMBLE: true },
      dark: { PRIMARY_COLOR: '#FF3B30', BACKGROUND: '#0A0C10', SURFACE: '#15181F', SURFACE_ALT: '#1C2028', BORDER: '#2B3039', TEXT: '#F1F2F5' },
      light: { PRIMARY_COLOR: '#E10600', BACKGROUND: '#F4F5F7', SURFACE: '#FFFFFF', SURFACE_ALT: '#EEF0F3', BORDER: '#E3E5EA', TEXT: '#15151E' },
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

  if (!settings) return <div className="px-4 sm:px-8 py-8">Loading settings…</div>

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
            <p className="text-sub fs-11 mt-1 max-w-2xl">Change app colors live, swap models, tune Monte Carlo, cache, data sources, security, monitoring — massive tunings for the entire project. Overrides are in-memory (Redis mirrored) and survive until restart; <code className="f1-mono fs-11">.env</code> is source of truth on reboot. Use presets, search, export/import JSON.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={save} disabled={saving} className="btn-primary">{saving?'Saving…':'Save changes'}</button>
            <button onClick={reset} className="btn-ghost">Reset overrides</button>
            <button onClick={exportJson} className="btn-ghost">Export JSON</button>
            <label className="btn-ghost cursor-pointer">Import JSON<input type="file" accept=".json" onChange={importJson} className="hidden"/></label>
          </div>
        </div>
        {msg && <div className="mt-3 p-2 rounded-lg surface-alt fs-11">{msg}</div>}
      </div>

      {/* Search + presets */}
      <div className="card p-4 flex flex-wrap items-center gap-3">
        <input value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Filter fields (e.g. CHAOS, REDIS, CORS)" className="f1-input flex-1 min-w-[220px]" />
        <span className="fs-11 text-sub">Presets:</span>
        <button onClick={()=> applyPreset('conservative')} className="badge">Conservative</button>
        <button onClick={()=> applyPreset('aggressive')} className="badge">Aggressive</button>
        <button onClick={()=> applyPreset('qualifying')} className="badge">Qualifying</button>
        <button onClick={()=> applyPreset('race')} className="badge">Race</button>
        <button onClick={()=> applyPreset('dark')} className="badge">Dark</button>
        <button onClick={()=> applyPreset('light')} className="badge">Light</button>
        <span className="fs-11 text-sub ml-auto">{Object.keys(draft).length} keys</span>
      </div>

      <div className="grid lg:grid-cols-[220px_1fr] gap-4">
        {/* Left nav */}
        <div className="card p-2 h-fit">
          {(groups).map(g=> (
            <button key={g.id} onClick={()=> setActive(g.id)} className={`w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 ${active===g.id?'bg-black text-white':'hover:bg-black/5'}`}>
              <span>{g.icon}</span><span className="fs-11 font-bold">{g.label}</span><span className="ml-auto fs-11 opacity-60">{g.fields.length}</span>
            </button>
          ))}
          <div className="mt-3 p-3 surface-alt rounded-lg fs-11 text-sub">
            Tip: colors apply <strong>live</strong> as you pick them. Monte Carlo &amp; model fields affect next <code className="f1-mono">POST /predictions</code> immediately via runtime overrides.
          </div>
        </div>

        {/* Fields */}
        <div className="card p-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="f1-display font-bold">{currentGroup.label}</h2>
            <span className="fs-11 text-sub">{filteredFields.length} / {currentGroup.fields.length} fields</span>
          </div>
          <p className="fs-11 text-sub mt-1">Group <code className="f1-mono fs-11">{currentGroup.id}</code> — every key is patchable via <code className="f1-mono fs-11">POST /api/v1/settings</code>.</p>

          <div className="mt-4 space-y-4">
            {filteredFields.map(name=>{
              const v = draft[name]
              const isOverridden = settings[name] !== undefined && JSON.stringify(settings[name]) !== JSON.stringify(v)
              // But we compare draft vs initial settings — show dirty
              const dirty = settings && JSON.stringify(settings[name]) !== JSON.stringify(v)
              return (
                <div key={name} className={`p-3 rounded-lg ${dirty?'border' : 'border border-transparent'}`} style={{ borderColor: dirty ? 'var(--amber)' : undefined, background: dirty? 'var(--surface-alt)' : undefined }}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="f1-mono text-xs font-bold break-all">{name}</span>
                        {dirty && <span className="fs-11 px-1.5 py-0.5 rounded bg-amber-500 text-white">dirty</span>}
                        {typeof v === 'boolean' && <span className="fs-11 text-sub">{v?'ON':'OFF'}</span>}
                      </div>
                      <div className="fs-11 text-sub break-all opacity-70">Current: <span className="font-mono">{JSON.stringify(settings[name])}</span></div>
                    </div>
                    <div className="w-[200px] sm:w-[260px] shrink-0">
                      <FieldInput name={name} value={v} onChange={(nv)=> setField(name, nv)} />
                    </div>
                  </div>
                </div>
              )
            })}
            {filteredFields.length===0 && <div className="p-8 text-center opacity-60 fs-11">No fields match “{filter}”.</div>}
          </div>

          {/* Raw JSON for power users */}
          <details className="mt-6">
            <summary className="fs-11 font-bold cursor-pointer">Raw JSON — all settings (power users)</summary>
            <textarea value={JSON.stringify(draft, null, 2)} onChange={e=>{
              try{ const obj = JSON.parse(e.target.value); setDraft(obj)}catch{}
            }} className="f1-input mt-2 min-h-[260px] font-mono text-[11px] leading-relaxed" />
            <div className="fs-11 text-sub mt-1">Paste → Save. This is the exact payload sent to <code className="f1-mono">POST /api/v1/settings</code>. Sensitive values are masked with <code>***</code> on read.</div>
          </details>
        </div>
      </div>

      {/* Footer meta */}
      <div className="card p-4 flex flex-wrap items-center gap-3 fs-11 text-sub">
        <span>Settings source: <code className="f1-mono">backend/app/config/settings.py</code> + runtime overrides</span>
        <span className="ml-auto">Docs: <code className="f1-mono">GET /api/v1/settings/schema</code> &amp; <code>GET /docs</code></span>
      </div>
    </div>
  )
}
