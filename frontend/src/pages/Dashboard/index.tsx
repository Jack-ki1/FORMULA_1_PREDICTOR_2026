import { useState, useMemo } from 'react'
import { RaceSelector } from '../../components/dashboard/RaceSelector'
import { SessionSelector } from '../../components/dashboard/SessionSelector'
import { WeatherSelector } from '../../components/dashboard/WeatherSelector'
import { PredictionControls } from '../../components/dashboard/PredictionControls'
import { PredictionResults } from '../../components/prediction/PredictionResults'
import { GridEditor } from '../../features/manual-grid/GridEditor'
import { AISidebar } from '../../features/ai-assistant/AISidebar'
import { F1Chart } from '../../components/charts/F1Chart'
import { useDashboardStore } from '../../stores/dashboardStore'
import { exportReport } from '../../api/reports'
import { useRaces } from '../../hooks/useRaces'

function useRaceInfo(id: string | undefined) {
  const { data: races } = useRaces()
  return useMemo(() => (races || []).find((r: any) => r.id === id), [races, id])
}

export function DashboardPage(){
  const [result,setResult]=useState<any>(null)
  const setManual=useDashboardStore(s=>s.setManualGrid) as any
  const manualGrid=useDashboardStore(s=>s.manualGrid) as any
  const draft=useDashboardStore(s=>s.draft) as any
  const session=useDashboardStore(s=>s.session) as any
  const subSession=useDashboardStore(s=>s.subSession) as any
  const targetId=useDashboardStore(s=>s.targetId) as any
  const raceInfo = useRaceInfo(draft?.raceId)
  const saveResult = (r:any)=> {
    setResult(r)
    try{
      localStorage.setItem('f1-last-prediction', JSON.stringify({ raceId: r.race_id || draft.raceId, predictions: r.predictions }))
      window.dispatchEvent(new Event('f1-prediction'))
    } catch{}
  }

  // Derived chart data for 3 core charts
  const top8 = result?.predictions?.winner?.predictions?.slice(0,8) || result?.predictions?.[Object.keys(result?.predictions||{})[0]]?.predictions?.slice(0,8) || []
  const winnerProbs = top8.map((p:any)=> p.probability)
  const labels = top8.map((p:any)=> p.driver_code)
  const teamColors: Record<string,string> = { mercedes:'#00A19B', redbull:'#3671C6', ferrari:'#E8002D', mclaren:'#FF8000', astonmartin:'#229971', williams:'#1E6FCE', audi:'#BB0A30', alpine:'#0090FF', haas:'#9198A1', racingbulls:'#3F5FCC', cadillac:'#9C7A19' }

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero — 2026 context */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-3 gap-0">
          <div className="md:col-span-2 p-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-red animate-pulse" style={{ background:'var(--red)'}} />
              <span className="fs-11 font-bold tracking-widest" style={{ color:'var(--red)'}}>PREDICTION MISSION CONTROL — 2026</span>
            </div>
            <h1 className="f1-display text-2xl font-black">Dashboard</h1>
            <p className="text-sub fs-11 mt-1 max-w-xl">Active aero (Straight/Corner), 50/50 PU (400kW ICE + 350kW ELEC), Overtake Mode + Boost. Pick a Grand Prix and session — the engine does the rest.</p>
            {raceInfo && (
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="badge">{raceInfo.flag} {raceInfo.name} · {raceInfo.circuit}</span>
                <span className="badge">{raceInfo.laps} laps · {raceInfo.drs_zones} DRS · {raceInfo.overtaking} overtake</span>
                <span className="badge">{raceInfo.status === 'completed' ? 'Completed' : 'Upcoming'} {raceInfo.sprint ? '· Sprint' : ''}</span>
              </div>
            )}
          </div>
          <div className="relative min-h-[160px]">
            <img src="/media/circuit2.png" alt="Circuit" className="absolute inset-0 w-full h-full object-cover" loading="lazy" />
            <div className="absolute inset-0 bg-gradient-to-l from-black/40 to-transparent" />
            <div className="absolute bottom-3 right-3 bg-black/70 text-white fs-11 px-3 py-1.5 rounded-full">2026 · 30kg lighter · 768kg</div>
          </div>
        </div>
      </div>

      {/* Controls — well organized grid */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-4 space-y-3">
          <div className="f1-display font-bold">1 · Race & Session</div>
          <RaceSelector />
          <SessionSelector />
          <WeatherSelector />
          <div className="fs-11 text-sub">Weather shifts base_sc +10 (wet) and tyre deg. Session pressure: Q1 0.9×, Q3 1.1×.</div>
        </div>
        <div className="card p-4 space-y-3">
          <div className="f1-display font-bold">2 · Grid</div>
          <div className="fs-11 text-sub">Manual P1–22 overrides auto Q3 model. Grid is the race — drag or select.</div>
          <div id="grid-editor"><GridEditor value={manualGrid} onChange={setManual} /></div>
          <div className="flex items-center gap-2 text-sm">
            <span className="fs-11">Source: {result?.grid_positions? 'auto (Q3 model)' : 'strength-based'}</span>
            <button onClick={()=> document.getElementById('grid-editor')?.scrollIntoView({behavior:'smooth'})} className="btn-ghost text-xs ml-auto">Edit Grid</button>
          </div>
        </div>
        <div className="card p-4 space-y-3">
          <div className="f1-display font-bold">3 · Run</div>
          <PredictionControls onResult={saveResult} />
          <div className="fs-11 text-sub">Sims 100–100k (clamped), chaos 0–100 linear to uniform. AI blend only when `ai_mode=ai` + key.</div>
          <AISidebar />
        </div>
      </div>

      {/* Active Aero 2026 explainer */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold">Active Aero</div>
          <div className="fs-11 text-sub mt-1">Straight Mode (low drag, flaps open on designated straights) vs Corner Mode (high downforce). Available to all, every lap.</div>
          <img src="/media/car_parts.png" alt="Aero" className="w-full h-24 object-contain mt-3 opacity-90" loading="lazy" />
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">Overtake + Boost</div>
          <div className="fs-11 text-sub mt-1">Within 1s → Overtake Mode +0.5MJ, 350kW to 337 km/h (vs 290 km/h taper for leader). Boost button adds strategic deploy.</div>
          <img src="/media/f1_simulation.png" alt="Boost" className="w-full h-24 object-contain mt-3 opacity-90" loading="lazy" />
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">PU & Sustainable Fuel</div>
          <div className="fs-11 text-sub mt-1">50/50 split (400kW ICE + 350kW electric), ERS 2× recovery, MGU-H removed, 100% Advanced Sustainable Fuel.</div>
          <img src="/media/pit_stop.jpg" alt="Pit" className="w-full h-24 object-cover rounded-lg mt-3" loading="lazy" />
        </div>
      </div>

      {/* Results */}
      {!result ? (
        <div className="card p-8 text-center">
          <div className="f1-display font-bold">No prediction yet</div>
          <p className="fs-11 text-sub mt-1">Select a Grand Prix above and hit Run — 2026 active aero era, 22 drivers, calibrated probabilities.</p>
          <img src="/media/f1_cartoon.png" alt="Cartoon" className="w-64 mx-auto mt-4 opacity-80" loading="lazy" />
        </div>
      ) : (
        <>
          {/* 3 core charts */}
          <div className="grid lg:grid-cols-3 gap-4">
            <div className="card p-4">
              <div className="f1-display font-bold mb-1">Podium Distribution</div>
              <p className="fs-11 text-sub mb-3">Top 8 win probability — sums to 1.00 (enforced).</p>
              <F1Chart type="bar" height={220} data={{ labels, datasets:[{ label:'Win %', data: winnerProbs.map((v:number)=> v*100), backgroundColor: labels.map((c:string)=> teamColors[(c||'').toLowerCase()] || '#E10600'), borderRadius:4 }] }} options={{ plugins:{legend:{display:false}}}} />
            </div>
            <div className="card p-4">
              <div className="f1-display font-bold mb-1">Model Confidence</div>
              <p className="fs-11 text-sub mb-3">Confidence gauge (0–1) + drift score {result.model_drift_score?.toFixed(3) ?? '—'}.</p>
              <F1Chart type="doughnut" height={220} data={{ labels:['Confidence','Remaining'], datasets:[{ data:[(result.predictions?.winner?.confidence ?? 0.8)*100, 100-(result.predictions?.winner?.confidence ?? 0.8)*100], backgroundColor:['#E10600','#E3E5EA'], borderWidth:0}] }} />
              <div className="text-center f1-mono text-lg font-bold mt-2" style={{ color:'var(--red)'}}>{((result.predictions?.winner?.confidence ?? 0.8)*100).toFixed(1)}%</div>
            </div>
            <div className="card p-4">
              <div className="f1-display font-bold mb-1">Points Probabilities</div>
              <p className="fs-11 text-sub mb-3">Top 10 points — wide margin absorbs one bad session.</p>
              <F1Chart type="bar" height={220} data={{ labels: (result.predictions?.points?.predictions?.slice(0,8).map((p:any)=>p.driver_code) || labels), datasets:[{ label:'Points %', data: (result.predictions?.points?.predictions?.slice(0,8).map((p:any)=>p.percentage) || winnerProbs.map((v:number)=>v*100)), backgroundColor:'#16233F', borderRadius:4}] }} options={{ plugins:{legend:{display:false}}}} />
            </div>
          </div>

          {/* Session analysis — 2026 style */}
          <div className="card p-4">
            <div className="f1-display font-bold">Session Analysis — 2026</div>
            <p className="fs-11 text-sub">Practice pace (FP1 0.95×, FP2 1.00×, FP3 1.05×) · Qualifying pressure · Race chaos. Grid: {Object.keys(result.grid_positions||{}).length} drivers.</p>
            <div className="grid md:grid-cols-3 gap-3 mt-3">
              <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Grid Source</div><div className="fs-11 text-sub">{result.grid_positions ? 'Auto Q3 model or manual P1-22' : 'Strength-based + noise'}</div></div>
              <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Weather</div><div className="fs-11 text-sub">{result.weather} · base_sc {result.race_id ? '55 +10 if wet' : '—'}</div></div>
              <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Sims</div><div className="fs-11 text-sub">{result.simulation_count ?? '—'} Monte Carlo laps · vectorised `argsort`</div></div>
            </div>
          </div>

          <PredictionResults result={result} />

          {/* Tire strategy */}
          <div className="card p-4">
            <div className="f1-display font-bold mb-2">Tyre Strategy — Pirelli Compounds</div>
            <p className="fs-11 text-sub">2026 cars are 30kg lighter, floor 100mm narrower — tyre deg re-tuned for sustainable fuel era. Strategy from `pit_strategy.py`.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {['C1 Hard','C2 Medium','C3 Soft','C4','C5'].map(c=> <span key={c} className="badge">{c}</span>)}
            </div>
          </div>

          <div className="card p-4 flex flex-col sm:flex-row items-center gap-3">
            <select id="export-format" defaultValue="csv" className="f1-select" style={{maxWidth:'160px'}}><option value="csv">CSV</option><option value="json">JSON</option><option value="pdf">PDF</option><option value="share">Share</option></select>
            <button onClick={()=>{
              const fmt=(document.getElementById('export-format') as HTMLSelectElement).value
              exportReport({race_id:draft.raceId, session, sub_session:subSession, target_id:targetId, format:fmt, predictions: result.predictions})
            }} className="btn-primary">Export</button>
            <span className="fs-11 text-sub">`POST /api/v1/reports/export` → download. Also saved to `localStorage f1-last-prediction` for Reports.</span>
            <span className="ml-auto fs-11 text-sub">Winner: {result.predictions?.winner?.predictions?.[0]?.driver_code} · {((result.predictions?.winner?.confidence ?? 0)*100).toFixed(0)}%</span>
          </div>
        </>
      )}
    </div>
  )
}
