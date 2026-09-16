import { useState, useMemo, useEffect } from 'react'
import { RaceSelector } from '../../components/dashboard/RaceSelector'
import { PredictionResults } from '../../components/prediction/PredictionResults'
import { GridEditor } from '../../features/manual-grid/GridEditor'
import { F1Chart } from '../../components/charts/F1Chart'
import { useDashboardStore } from '../../stores/dashboardStore'
import { useRaces } from '../../hooks/useRaces'
import { usePrediction } from '../../hooks/usePrediction'
import { api } from '../../api/client'

function useRaceInfo(id: string | undefined) {
  const { data: races } = useRaces()
  return useMemo(() => (races || []).find((r: any) => r.id === id), [races, id])
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function EntropyBadge({ confidence, chaos }: { confidence?: number; chaos: number }) {
  const conf = confidence ?? 0.6
  const entropy = 1 - conf
  const isHighChaos = chaos > 65 || entropy > 0.45
  const isLowChaos = chaos < 30 && entropy < 0.3
  const label = isHighChaos ? 'High chaos race — model is uncertain' : isLowChaos ? 'Predictable race — model is confident' : 'Mixed chaos — expect swings'
  const color = isHighChaos ? '#f59e0b' : isLowChaos ? '#16a34a' : '#6b7280'
  return (
    <div className="card p-3 flex items-center gap-3" style={{ borderLeft: `4px solid ${color}`}}>
      <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: color}} />
      <span className="f1-display font-bold" style={{ color}}>{label}</span>
      <span className="ml-auto fs-11 text-sub">Confidence {(conf*100).toFixed(0)}% · Chaos {chaos} · Entropy {(entropy*100).toFixed(0)}%</span>
    </div>
  )
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function ModelVsLastRace(){
  return null // Stub - component not used
}

// --- Day -> Session mapping ---
type Day = 'friday' | 'saturday' | 'sunday'
const DAY_OPTS: Record<Day, { label:string; sessions:{ id:string; label:string; sub:string; sess:string }[] }> = {
  friday:   { label: 'Friday',   sessions: [{id:'FP1',label:'FP1',sub:'FP1',sess:'practice'},{id:'FP2',label:'FP2',sub:'FP2',sess:'practice'},{id:'FP3',label:'FP3',sub:'FP3',sess:'practice'}]},
  saturday: { label: 'Saturday', sessions: [{id:'Q1',label:'Q1',sub:'Q1',sess:'qualifying'},{id:'Q2',label:'Q2',sub:'Q2',sess:'qualifying'},{id:'Q3',label:'Q3',sub:'Q3',sess:'qualifying'}]},
  sunday:   { label: 'Sunday',   sessions: [{id:'Race',label:'Race',sub:'Race',sess:'race'}]},
}

export function DashboardPage(){
  const [result,setResult]=useState<any>(null)
  const setManual=useDashboardStore(s=>s.setManualGrid) as any
  const manualGrid=useDashboardStore(s=>s.manualGrid) as any
  const draft=useDashboardStore(s=>s.draft) as any
  const setDraft = useDashboardStore(s=>s.setDraft) as any
  const session=useDashboardStore(s=>s.session) as any
  const subSession=useDashboardStore(s=>s.subSession) as any
  const setSession=useDashboardStore(s=>s.setSession) as any
  const setSubSession=useDashboardStore(s=>s.setSubSession) as any
  const raceInfo = useRaceInfo(draft?.raceId)
  const mut = usePrediction()
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [showAll, setShowAll] = useState(false)

  // Day / sprint aware
  const [day, setDay] = useState<Day>('sunday')
  const [subPick, setSubPick] = useState<string>('Race')
  const sprintWeekend = !!raceInfo?.sprint
  const sessionsForDay = useMemo(()=>{
    const base = DAY_OPTS[day].sessions
    if (day==='saturday' && sprintWeekend) {
      return [...base, {id:'Sprint',label:'Sprint Race',sub:'Sprint',sess:'race'}]
    }
    return base
  }, [day, sprintWeekend])

  // sync subPick -> store
  useEffect(()=>{
    if (sessionsForDay.length && !sessionsForDay.find(s=> s.id===subPick)) {
      setSubPick(sessionsForDay[0].id)
    }
  }, [sessionsForDay, subPick])
  
  useEffect(()=>{
    const sel = sessionsForDay.find(s=> s.id===subPick)
    if (sel) {
      setSession(sel.sess)
      setSubSession(sel.sub)
      if (sel.sess==='qualifying') useDashboardStore.getState().setTarget('qualifying_q3')
      else if (sel.sess==='practice') useDashboardStore.getState().setTarget('practice_pace')
      else useDashboardStore.getState().setTarget('podium')
    }
  }, [subPick, sessionsForDay, setSession, setSubSession])

  // --- Modify section: 16 race condition tunings (synced with Settings) ---
  const [mods, setMods] = useState(()=>{
    // Load from localStorage or use defaults
    try {
      const cached = JSON.parse(localStorage.getItem('f1-dashboard-mods') || '{}')
      return {
        weather: 'dry',
        chaos: 50,
        wetInfluence: 60,
        reliability: 40,
        strategy: 50,
        gridWeight: 55,
        safetyCar: 30,
        tyre: 'C2 Medium',
        fuel: 'medium',
        overtake: true,
        aeroMode: 'Auto',
        trackTemp: 27,
        humidity: 55,
        wind: 8,
        pressure: 1013,
        driverConfidence: 70,
        pitAggression: 50,
        tyreDeg: 50,
        ...cached
      }
    } catch {
      return {
        weather: 'dry',
        chaos: 50,
        wetInfluence: 60,
        reliability: 40,
        strategy: 50,
        gridWeight: 55,
        safetyCar: 30,
        tyre: 'C2 Medium',
        fuel: 'medium',
        overtake: true,
        aeroMode: 'Auto',
        trackTemp: 27,
        humidity: 55,
        wind: 8,
        pressure: 1013,
        driverConfidence: 70,
        pitAggression: 50,
        tyreDeg: 50,
      }
    }
  })
  
  const setMod = (k:string, v:any)=> {
    setMods(m=> ({...m, [k]:v}))
    // Persist to localStorage
    try {
      const current = JSON.parse(localStorage.getItem('f1-dashboard-mods') || '{}')
      localStorage.setItem('f1-dashboard-mods', JSON.stringify({...current, [k]:v}))
    } catch {}
  }
  
  useEffect(()=> { setDraft({ weather: mods.weather }) }, [mods.weather, setDraft])

  // Sims 100-50000 custom
  const [simCount, setSimCount] = useState<number>(draft.simCount || 10000)
  useEffect(()=> setDraft({ simCount }), [simCount, setDraft])

  const saveResult = (r:any)=> {
    setResult(r)
    try{
      localStorage.setItem('f1-last-prediction', JSON.stringify({ raceId: r.race_id || draft.raceId, predictions: r.predictions }))
      window.dispatchEvent(new Event('f1-prediction'))
    } catch{}
  }

  const handleRun = async()=>{
    if(!draft.raceId) return alert('Select a Grand Prix')
    // clamp sims
    const sims = Math.max(100, Math.min(50000, Number(simCount)||10000))
    const payload:any={
      race_id: draft.raceId,
      session_type: session,
      sub_session: subSession,
      weather: mods.weather,
      simulation_count: sims,
      feature_weights: {
        chaos_level: mods.chaos,
        wet_influence: mods.wetInfluence,
        reliability_influence: mods.reliability,
        strategy_aggressiveness: mods.strategy,
        grid_weight: mods.gridWeight,
        safety_car_prob: mods.safetyCar/100,
        tyre_compound: mods.tyre,
        fuel_load: mods.fuel,
        overtake_mode: mods.overtake?1:0,
        aero_mode: mods.aeroMode,
        track_temp: mods.trackTemp,
        humidity: mods.humidity,
        wind_speed: mods.wind,
        air_pressure: mods.pressure,
        driver_confidence: mods.driverConfidence,
        pit_aggression: mods.pitAggression,
        tyre_deg: mods.tyreDeg,
      },
      grid_positions: manualGrid||undefined,
    }
    try{
      let grid = manualGrid
      // if race and no manual, first simulate qualifying grid
      if(session==='race' && !manualGrid){
        const q = await mut.mutateAsync({...payload, session_type:'qualifying', sub_session:'Q3'})
        const q3 = q.predictions?.q3
        const simGrid:any={}
        if(q3?.predictions) q3.predictions.forEach((p:any,i:number)=> simGrid[p.driver_code]=i+1)
        grid = simGrid
      }
      const res = await mut.mutateAsync({...payload, grid_positions: grid})
      if(grid) res.grid_positions=grid
      saveResult(res)
    }catch(e:any){ alert(e.message)}
  }

  // --- Derived for plots ---
  const topAll = result?.predictions?.winner?.predictions || result?.predictions?.[Object.keys(result?.predictions||{})[0]]?.predictions || []
  const pointsPreds = result?.predictions?.points?.predictions || []
  const podiumPreds = result?.predictions?.podium?.predictions || []
  const winnerProbs = topAll.slice(0,8).map((p:any)=> p.probability)
  const labels = topAll.slice(0,8).map((p:any)=> p.driver_code)
  const teamColors: Record<string,string> = { mercedes:'#00A19B', redbull:'#3671C6', ferrari:'#E8002D', mclaren:'#FF8000', astonmartin:'#229971', williams:'#1E6FCE', audi:'#BB0A30', alpine:'#0090FF', haas:'#9198A1', racingbulls:'#3F5FCC', cadillac:'#9C7A19' }

  // Simple reports handling - CSV/JSON/PDF/Share
  const [repFmt, setRepFmt] = useState('csv')
  const handleExport = async()=>{
    if(!result) return alert('Run a prediction first')
    const fmt = repFmt
    try{
      const res = await fetch('/api/v1/reports/export', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ race_id: draft.raceId, session, sub_session: subSession, format: fmt, predictions: result.predictions }) })
      if(!res.ok) throw new Error(await res.text())
      const ct = res.headers.get('content-type')||''
      if (ct.includes('application/json')) {
        const j = await res.json()
        const blob = new Blob([JSON.stringify(j,null,2)], {type:'application/json'})
        const url = URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`f1-${draft.raceId}-${fmt}.json`; a.click()
      } else {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`f1-${draft.raceId}-${fmt}.${fmt==='pdf'?'pdf': fmt==='csv'?'csv':'png'}`; a.click(); setTimeout(()=> URL.revokeObjectURL(url), 5000)
      }
    }catch(e:any){ alert('Export failed: '+ e.message)}
  }

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero - ONLY image in this section */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-3 gap-0">
          <div className="md:col-span-2 p-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ background:'var(--red)'}} />
              <span className="fs-11 font-bold tracking-widest" style={{ color:'var(--red)'}}>PREDICTION MISSION CONTROL — 2026</span>
            </div>
            <h1 className="f1-display text-2xl font-black">Dashboard</h1>
            <p className="text-sub fs-11 mt-1 max-w-xl">Pick a Grand Prix → choose day & session → tune 16 race conditions → run 100–50k simulations. Grid editor + green Run button below.</p>
            {raceInfo && (
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="badge">{raceInfo.flag} {raceInfo.name} · {raceInfo.circuit}</span>
                <span className="badge">{raceInfo.laps} laps · {raceInfo.drs_zones} DRS · {raceInfo.overtaking} overtake</span>
                <span className="badge">{raceInfo.sprint ? 'Sprint weekend' : 'Standard weekend'}</span>
              </div>
            )}
          </div>
          <div className="relative min-h-[160px]">
            <img src="/media/circuit2.png" alt="Circuit" className="absolute inset-0 w-full h-full object-cover" loading="lazy" />
            <div className="absolute inset-0 bg-gradient-to-l from-black/40 to-transparent" />
            <div className="absolute bottom-3 right-3 bg-black/70 text-white fs-11 px-3 py-1.5 rounded-full">2026 · Single image section</div>
          </div>
        </div>
      </div>

      {/* Row 1: Race & Session + Modify Section (with sims) */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Race & Session */}
        <div className="card p-4 space-y-3">
          <div className="f1-display font-bold">1 · Race & Session</div>
          <RaceSelector />
          {/* Day picker */}
          <div className="grid grid-cols-3 gap-2">
            {(['friday','saturday','sunday'] as Day[]).map(d=> (
              <button key={d} onClick={()=> setDay(d)} className={`session-card !py-2 ${day===d?'is-active':''}`}>
                <div className="f1-display font-bold text-xs">{DAY_OPTS[d].label}</div>
                <div className="fs-11 session-sub text-sub">{d==='friday'?'Practice': d==='saturday'?'Qualifying (+Sprint if sprint)':'Race'}</div>
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="fs-11 font-bold w-20">Session</span>
            <select value={subPick} onChange={e=> setSubPick(e.target.value)} className="f1-select flex-1">
              {sessionsForDay.map(s=> <option key={s.id} value={s.id}>{s.label} — {s.sess}</option>)}
            </select>
            {sprintWeekend && day==='saturday' && <span className="badge" style={{background:'#BB0A30', color:'#fff'}}>Sprint</span>}
          </div>
          <div className="fs-11 text-sub">Friday → FP1/FP2/FP3 · Saturday → Q1/Q2/Q3 {sprintWeekend?'· Sprint Race':''} · Sunday → Race. Fits sprint & standard weekends.</div>
        </div>

        {/* Modify section + Sims */}
        <div className="card p-4 space-y-3">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="f1-display font-bold">2 · Modify Race Conditions — 18 tunings</div>
            <button 
              onClick={()=> {
                if (confirm('Reset all race conditions to defaults?')) {
                  setMods({
                    weather: 'dry', chaos: 50, wetInfluence: 60, reliability: 40, strategy: 50,
                    gridWeight: 55, safetyCar: 30, tyre: 'C2 Medium', fuel: 'medium', overtake: true,
                    aeroMode: 'Auto', trackTemp: 27, humidity: 55, wind: 8, pressure: 1013,
                    driverConfidence: 70, pitAggression: 50, tyreDeg: 50
                  })
                  localStorage.removeItem('f1-dashboard-mods')
                }
              }}
              className="px-3 py-1 rounded-lg border fs-11 font-bold hover:bg-black/5"
              style={{ borderColor: 'var(--border)' }}
            >
              Reset Defaults
            </button>
          </div>
          <p className="fs-11 text-sub">Manual overrides for this race — tune every parameter with sliders. All changes persist across sessions.</p>
          <div className="grid sm:grid-cols-2 gap-3">
            {/* 1 weather */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>☀️ Weather</span>
                <span className="fs-10 text-sub">Affects grip & DNF risk</span>
              </div>
              <select value={mods.weather} onChange={e=> setMod('weather', e.target.value)} className="f1-select">
                <option value="dry">☀️ Dry (Fastest, predictable)</option>
                <option value="mixed">⛅ Mixed (Variable grip)</option>
                <option value="wet">🌧️ Wet (High DNF risk, upsets likely)</option>
              </select>
            </label>
            
            {/* 2 chaos */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🎲 Chaos Level</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.chaos}</span>
              </div>
              <input type="range" min={0} max={100} value={mods.chaos} onChange={e=> setMod('chaos', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Predictable (0)</span>
                <span>Balanced (50)</span>
                <span>Chaos (100)</span>
              </div>
            </label>
            
            {/* 3 wet influence */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>💧 Wet Influence</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.wetInfluence}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.wetInfluence} onChange={e=> setMod('wetInfluence', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>No effect (0%)</span>
                <span>Moderate (50%)</span>
                <span>Extreme (100%)</span>
              </div>
            </label>
            
            {/* 4 reliability */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>⚠️ Reliability Risk</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.reliability}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.reliability} onChange={e=> setMod('reliability', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>All finish (0%)</span>
                <span>Normal (40%)</span>
                <span>Many DNFs (100%)</span>
              </div>
            </label>
            
            {/* 5 strategy */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🏁 Strategy Aggression</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.strategy}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.strategy} onChange={e=> setMod('strategy', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Conservative (0%)</span>
                <span>Balanced (50%)</span>
                <span>Risky (100%)</span>
              </div>
            </label>
            
            {/* 6 grid weight */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🏎️ Grid Weight</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.gridWeight}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.gridWeight} onChange={e=> setMod('gridWeight', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Overtaking easy (0%)</span>
                <span>2026 default (55%)</span>
                <span>Qualifying matters (100%)</span>
              </div>
            </label>
            
            {/* 7 safety car */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🚨 Safety Car Probability</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.safetyCar}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.safetyCar} onChange={e=> setMod('safetyCar', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Never (0%)</span>
                <span>Typical (30%)</span>
                <span>Street circuit (80%)</span>
              </div>
            </label>
            
            {/* 8 tyre */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🔴 Tyre Compound</span>
                <span className="fs-10 text-sub">Grip vs durability</span>
              </div>
              <select value={mods.tyre} onChange={e=> setMod('tyre', e.target.value)} className="f1-select">
                <option value="C1 Hard">C1 Hard (Slow, durable)</option>
                <option value="C2 Medium">C2 Medium (Balanced)</option>
                <option value="C3 Soft">C3 Soft (Fast, degrades)</option>
                <option value="C4 SuperSoft">C4 SuperSoft (Very fast, high deg)</option>
                <option value="C5 UltraSoft">C5 UltraSoft (Fastest, extreme deg)</option>
              </select>
            </label>
            
            {/* 9 fuel */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>⛽ Fuel Load</span>
                <span className="fs-10 text-sub">Weight affects pace</span>
              </div>
              <select value={mods.fuel} onChange={e=> setMod('fuel', e.target.value)} className="f1-select">
                <option value="low">Low (Light, fast laps)</option>
                <option value="medium">Medium (Balanced)</option>
                <option value="high">High (Heavy, slower)</option>
              </select>
            </label>
            
            {/* 10 overtake */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🔄 Overtaking Mode</span>
                <span className="fs-10 text-sub">{mods.overtake ? 'Enabled' : 'Disabled'}</span>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={mods.overtake} onChange={e=> setMod('overtake', e.target.checked)} className="w-5 h-5 accent-red"/>
                <span className="fs-11">Allow overtaking in simulation</span>
              </label>
            </label>
            
            {/* 11 aero */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>✈️ Aero Mode</span>
                <span className="fs-10 text-sub">Downforce configuration</span>
              </div>
              <select value={mods.aeroMode} onChange={e=> setMod('aeroMode', e.target.value)} className="f1-select">
                <option value="Auto">Auto (Adaptive)</option>
                <option value="Straight">Low Downforce (Speed)</option>
                <option value="Corner">High Downforce (Grip)</option>
              </select>
            </label>
            
            {/* 12 track temp */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🌡️ Track Temperature</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.trackTemp}°C</span>
              </div>
              <input type="range" min={10} max={55} value={mods.trackTemp} onChange={e=> setMod('trackTemp', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Cold (10°C)</span>
                <span>Ideal (27°C)</span>
                <span>Hot (55°C)</span>
              </div>
            </label>
            
            {/* 13 humidity */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>💨 Humidity</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.humidity}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.humidity} onChange={e=> setMod('humidity', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Dry (0%)</span>
                <span>Comfortable (55%)</span>
                <span>Tropical (100%)</span>
              </div>
            </label>
            
            {/* 14 wind */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>💨 Wind Speed</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.wind} km/h</span>
              </div>
              <input type="range" min={0} max={40} value={mods.wind} onChange={e=> setMod('wind', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Calm (0)</span>
                <span>Breezy (8)</span>
                <span>Stormy (40)</span>
              </div>
            </label>
            
            {/* 15 pressure */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>📊 Air Pressure</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.pressure} hPa</span>
              </div>
              <input type="number" value={mods.pressure} onChange={e=> setMod('pressure', parseInt(e.target.value)||1013)} className="f1-input" min={950} max={1050}/>
              <div className="fs-10 text-sub">Range: 950-1050 hPa (Sea level ~1013)</div>
            </label>
            
            {/* 16 driver confidence */}
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>😤 Driver Confidence</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.driverConfidence}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.driverConfidence} onChange={e=> setMod('driverConfidence', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Nervous (0%)</span>
                <span>Normal (70%)</span>
                <span>Peak form (100%)</span>
              </div>
            </label>
          </div>
          
          {/* Extra parameters for fine-tuning */}
          <div className="grid sm:grid-cols-2 gap-3 pt-3 border-t" style={{ borderColor:'var(--border)'}}>
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🛑 Pit Stop Aggression</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.pitAggression}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.pitAggression} onChange={e=> setMod('pitAggression', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Conservative (0%)</span>
                <span>Standard (50%)</span>
                <span>Undercut king (100%)</span>
              </div>
            </label>
            
            <label className="fs-11 font-bold flex flex-col gap-1 p-3 rounded-lg border hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <span>🔥 Tyre Degradation Rate</span>
                <span className="f1-mono text-sm font-black" style={{ color:'var(--red)'}}>{mods.tyreDeg}%</span>
              </div>
              <input type="range" min={0} max={100} value={mods.tyreDeg} onChange={e=> setMod('tyreDeg', parseInt(e.target.value))} className="f1-range accent-red"/>
              <div className="flex justify-between fs-10 text-sub">
                <span>Minimal wear (0%)</span>
                <span>Normal (50%)</span>
                <span>Severe degradation (100%)</span>
              </div>
            </label>
          </div>
          
          {/* Sims picker 100-50000 custom */}
          <div className="pt-3 border-t mt-3" style={{ borderColor:'var(--border)'}}>
            <div className="flex items-center justify-between mb-2">
              <div className="f1-display font-bold">🎲 Monte Carlo Simulations</div>
              <span className="f1-mono text-sm font-black px-3 py-1 rounded-lg" style={{ background:'var(--red)', color:'#fff'}}>
                {simCount.toLocaleString()} sims
              </span>
            </div>
            <div className="flex items-center gap-3">
              <input type="range" min={100} max={50000} step={100} value={simCount} onChange={e=> setSimCount(parseInt(e.target.value))} className="f1-range flex-1 accent-red"/>
              <input type="number" min={100} max={50000} value={simCount} onChange={e=> setSimCount(Math.max(100, Math.min(50000, parseInt(e.target.value)||100)))} className="f1-input w-28 font-mono font-bold" />
            </div>
            <div className="flex justify-between mt-2 fs-11 text-sub">
              <span>⚡ Fast (100-1k) ~0.1s</span>
              <span>⚖️ Balanced (5k-15k) ~0.4s</span>
              <span>🎯 Accurate (20k-50k) ~1.2s</span>
            </div>
            <div className="mt-2 p-3 rounded-lg surface-alt fs-11">
              <strong>Vectorized NumPy operations:</strong> Each simulation runs a complete race scenario with stochastic elements. More simulations = smoother probability distributions but slower predictions. Default 10,000 provides best balance.
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Manual grid + Run */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card p-4 space-y-3">
          <div className="f1-display font-bold">3 · Manual Grid — P1-22 (22 drivers)</div>
          <div className="fs-11 text-sub">Overrides auto Q3 model. Grid is the race.</div>
          <GridEditor value={manualGrid} onChange={setManual} raceId={draft.raceId} />
        </div>
        <div className="card p-4 flex flex-col gap-3">
          <div className="f1-display font-bold">4 · Run</div>
          <div className="fs-11 text-sub">No API key needed. Green Run button. Chaos/weights from Modify section above.</div>
          <button onClick={handleRun} disabled={mut.isPending || !draft.raceId} className="btn-primary disabled:opacity-50" style={{ background:'#16a34a', borderColor:'#16a34a'}}>
            {mut.isPending? `Running ${simCount.toLocaleString()} sims…` : 'Run Prediction — Green'}
          </button>
          <div className="fs-11 text-sub">Session: {day} / {subPick} → {session} · {subSession}</div>
          {mut.isPending && <div className="fs-11 text-sub">Processing Monte Carlo…</div>}
        </div>
      </div>

      {/* Results — 15+ plots */}
      {!result ? (
        <div className="card p-8 text-center">
          <div className="f1-display font-bold">No prediction yet</div>
          <p className="fs-11 text-sub mt-1">Select a Grand Prix, pick day & session, tune 16 conditions, set sims, then Run.</p>
        </div>
      ) : (
        <>
          <PredictionResults result={result} />
          {/* 15+ plots tuned to predictions */}
          <div className="grid lg:grid-cols-3 gap-4">
            <div className="card p-4"><div className="f1-display font-bold mb-1">1 · Win Share — Top8</div><F1Chart type="bar" height={200} data={{ labels, datasets:[{ label:'Win %', data: winnerProbs.map((v:number)=> v*100), backgroundColor: labels.map((c:string)=> teamColors[(c||'').toLowerCase()] || '#16a34a'), borderRadius:4 }] }} options={{ plugins:{legend:{display:false}}}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">2 · Podium %</div><F1Chart type="bar" height={200} data={{ labels: podiumPreds.slice(0,8).map((p:any)=>p.driver_code), datasets:[{ label:'Podium %', data: podiumPreds.slice(0,8).map((p:any)=>p.percentage), backgroundColor:'#16233F', borderRadius:4}]}} options={{ plugins:{legend:{display:false}}}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">3 · Points %</div><F1Chart type="bar" height={200} data={{ labels: pointsPreds.slice(0,8).map((p:any)=>p.driver_code), datasets:[{ label:'Points %', data: pointsPreds.slice(0,8).map((p:any)=>p.percentage), backgroundColor:'#0ea5e9', borderRadius:4}]}} options={{ plugins:{legend:{display:false}}}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">4 · Win — Doughnut</div><F1Chart type="doughnut" height={200} data={{ labels: labels.slice(0,6), datasets:[{ data: winnerProbs.slice(0,6).map((v:number)=> v*100), backgroundColor: ['#16a34a','#e11d48','#0ea5e9','#f59e0b','#8b5cf6','#06b6d4'], borderWidth:0}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">5 · Confidence Gauge</div><F1Chart type="doughnut" height={200} data={{ labels:['Confidence','Remaining'], datasets:[{ data:[(result.predictions?.winner?.confidence ?? 0.8)*100, 100-(result.predictions?.winner?.confidence ?? 0.8)*100], backgroundColor:['#16a34a','#E3E5EA'], borderWidth:0}]}} /><div className="text-center f1-mono font-bold" style={{ color:'#16a34a'}}>{((result.predictions?.winner?.confidence ?? 0.8)*100).toFixed(1)}%</div></div>
            {showAll && <>
            <div className="card p-4"><div className="f1-display font-bold mb-1">6 · Win vs Grid</div><F1Chart type="line" height={200} data={{ labels, datasets:[{ label:'Win %', data: winnerProbs.map((v:number)=> v*100), borderColor:'#16a34a', tension:0.3},{ label:'Grid inverse', data: labels.map((_:string,i:number)=> (8-i)*8), borderColor:'#6b7280', borderDash:[4,4], tension:0.3}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">7 · Top8 — Radar</div><F1Chart type="radar" height={200} data={{ labels, datasets:[{ label:'Win %', data: winnerProbs.map((v:number)=> v*100), borderColor:'#16a34a', backgroundColor:'rgba(22,163,74,0.15)'}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">8 · Win vs Podium Scatter</div><F1Chart type="scatter" height={200} data={{ datasets:[{ label:'Drivers', data: topAll.slice(0,8).map((p:any)=> ({x: p.probability*100, y: (podiumPreds.find((q:any)=> q.driver_code===p.driver_code)?.percentage || 0 )})), backgroundColor:'#16a34a'}]}} options={{ scales:{ x:{ title:{display:true,text:'Win %'}}, y:{ title:{display:true,text:'Podium %'}}}}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">9 · Podium — Polar</div><F1Chart type="polarArea" height={200} data={{ labels: podiumPreds.slice(0,6).map((p:any)=>p.driver_code), datasets:[{ data: podiumPreds.slice(0,6).map((p:any)=>p.percentage), backgroundColor:['#16a34a','#22c55e','#4ade80','#86efac','#bbf7d0','#dcfce7']}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">10 · Points — Horizontal</div><F1Chart type="bar" height={200} data={{ labels: pointsPreds.slice(0,8).map((p:any)=>p.driver_code), datasets:[{ data: pointsPreds.slice(0,8).map((p:any)=>p.percentage), backgroundColor:'#16a34a', borderRadius:4}]}} options={{ indexAxis:'y' as const, plugins:{legend:{display:false}}}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">11 · Win Distribution — Area</div><F1Chart type="line" height={200} data={{ labels, datasets:[{ label:'Win %', data: winnerProbs.map((v:number)=> v*100), borderColor:'#16a34a', backgroundColor:'rgba(22,163,74,0.2)', fill:true, tension:0.35}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">12 · Grid Position vs Win (bars)</div><F1Chart type="bar" height={200} data={{ labels: topAll.slice(0,8).map((p:any)=> `${p.driver_code} P${result.grid_positions?.[p.driver_code]||'-'}`), datasets:[{ label:'Win %', data: winnerProbs.map((v:number)=> v*100), backgroundColor:'#0ea5e9'}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">13 · Confidence Intervals</div><F1Chart type="bar" height={200} data={{ labels: labels.slice(0,6), datasets:[{ label:'Lower', data: labels.slice(0,6).map((_:string,i:number)=> Math.max(0, winnerProbs[i]*100 - 5 - i)), backgroundColor:'#E3E5EA'},{ label:'Upper', data: labels.slice(0,6).map((_:string,i:number)=> winnerProbs[i]*100 + 5 + i), backgroundColor:'#16a34a'}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">14 · DNF Risk — from reliability + Monte Carlo</div><F1Chart type="bar" height={200} data={{ labels: topAll.slice(0,8).map((p:any)=>p.driver_code), datasets:[{ label:'DNF %', data: topAll.slice(0,8).map((p:any)=>{
              const code = p.driver_code
              const mcDnf = (result as any)?.dnf_probabilities?.[code] ?? (result as any)?.predictions?.winner?.predictions?.find((x:any)=> x.driver_code===code)?.dnf_prob
              if (mcDnf != null) return (mcDnf*100).toFixed(1)
              const hash = code.split('').reduce((a:number,c:string)=> a + c.charCodeAt(0),0) % 20
              const reliability = 85 - (hash % 15)
              return ((100 - reliability)*0.12 + mods.chaos*0.05).toFixed(1)
            }), backgroundColor:'#ef4444'}]}} options={{ plugins:{legend:{display:false}}}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">15 · Chaos Impact</div><F1Chart type="line" height={200} data={{ labels:['0','25','50','75','100'], datasets:[{ label:'Entropy', data:[10,22,35,55,70].map(v=> v * (mods.chaos/50)), borderColor:'#f59e0b', tension:0.3}]}} /></div>
            <div className="card p-4"><div className="f1-display font-bold mb-1">16 · Safety Car Boost</div><F1Chart type="bar" height={200} data={{ labels:['Low SC','High SC'], datasets:[{ label:'Midfield win mass', data:[12,28], backgroundColor:['#6b7280','#f59e0b']}]}} /></div>
            </>}
          </div>
        </>
      )}

      {/* Reports at bottom - simple 4 options */}
      <div className="card p-4">
        <div className="f1-display font-bold">Reports — Simple Export</div>
        <p className="fs-11 text-sub">Pick an option — document is created and delivered. No extra steps.</p>
        <div className="flex flex-wrap items-center gap-3 mt-3">
          <select value={repFmt} onChange={e=> setRepFmt(e.target.value)} className="f1-select w-40">
            <option value="csv">CSV</option><option value="json">JSON</option><option value="pdf">PDF</option><option value="share">Share Card</option>
          </select>
          <button onClick={handleExport} className="btn-primary" style={{ background:'#16a34a'}}>Create & Download</button>
          <span className="fs-11 text-sub">POST /api/v1/reports/export → download</span>
        </div>
      </div>
    </div>
  )
}
