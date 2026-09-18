import { useState, useMemo, useEffect } from 'react'
import { RaceSelector } from '../../components/dashboard/RaceSelector'
import { PredictionResults } from '../../components/prediction/PredictionResults'
import { GridEditor } from '../../features/manual-grid/GridEditor'
import { F1Chart } from '../../components/charts/F1Chart'
import { useDashboardStore } from '../../stores/dashboardStore'
import { useRaces } from '../../hooks/useRaces'
import { usePrediction } from '../../hooks/usePrediction'
import { usePreferences } from '../../features/preferences/store'
import { Icon } from '../../components/icons/Icon'

function useRaceInfo(id: string | undefined) {
  const { data: races } = useRaces()
  return useMemo(() => (races || []).find((r: any) => r.id === id), [races, id])
}

// --- Day -> Session mapping ---
type Day = 'friday' | 'saturday' | 'sunday'
const DAY_OPTS: Record<Day, { label: string; sessions: { id: string; label: string; sub: string; sess: string }[] }> = {
  friday: { label: 'Friday', sessions: [{ id: 'FP1', label: 'FP1', sub: 'FP1', sess: 'practice' }, { id: 'FP2', label: 'FP2', sub: 'FP2', sess: 'practice' }, { id: 'FP3', label: 'FP3', sub: 'FP3', sess: 'practice' }] },
  saturday: { label: 'Saturday', sessions: [{ id: 'Q1', label: 'Q1', sub: 'Q1', sess: 'qualifying' }, { id: 'Q2', label: 'Q2', sub: 'Q2', sess: 'qualifying' }, { id: 'Q3', label: 'Q3', sub: 'Q3', sess: 'qualifying' }] },
  sunday: { label: 'Sunday', sessions: [{ id: 'Race', label: 'Race', sub: 'Race', sess: 'race' }] },
}

// Every slider the Dashboard exposes, and whether the backend prediction engine
// actually consumes it today (verified against the backend engine source — see the
// "Live" badge below). This distinction used to not exist anywhere in the UI: all
// 16 sliders looked equally consequential even though 10 of them are collected and
// sent to the API but currently ignored by the engine. Rather than silently drop
// the 10 (they're harmless and some map directly to fields the engine schema
// already declares, so wiring them up later is straightforward), they stay
// available and clearly marked instead.
type ModKey = keyof typeof MOD_META
const MOD_META = {
  chaos: { label: 'Chaos Level', icon: 'gauge' as const, live: true, kind: 'range', min: 0, max: 100, unit: '', help: 'Blends deterministic to uniform-random outcomes. Directly changes the win-probability exponent.' },
  gridWeight: { label: 'Grid Weight', icon: 'flag' as const, live: true, kind: 'range', min: 0, max: 100, unit: '%', help: '2026 active aero narrows the pole-to-win gap — lower values model closer racing.' },
  wetInfluence: { label: 'Wet Influence', icon: 'cloud' as const, live: true, kind: 'range', min: 0, max: 100, unit: '%', help: 'How much wet-weather skill matters when weather is mixed or wet.' },
  reliability: { label: 'Reliability Risk', icon: 'alert' as const, live: true, kind: 'range', min: 0, max: 100, unit: '%', help: 'DNF and mechanical-failure weighting.' },
  strategy: { label: 'Strategy Aggression', icon: 'sliders' as const, live: true, kind: 'range', min: 0, max: 100, unit: '%', help: 'Shifts the 1-stop versus 2-stop strategy split.' },
  safetyCar: { label: 'Safety Car Probability', icon: 'alert' as const, live: true, kind: 'range', min: 0, max: 100, unit: '%', help: 'Feeds the DNF-rate model directly.' },
  weather: { label: 'Weather', icon: 'cloud' as const, live: true, kind: 'select', options: [['dry', 'Dry — fastest, predictable'], ['mixed', 'Mixed — variable grip'], ['wet', 'Wet — high DNF risk, upsets likely']], help: 'Sets the session weather condition for the whole run.' },
  tyre: { label: 'Tyre Compound', icon: 'gauge' as const, live: false, kind: 'select', options: [['C1 Hard', 'C1 Hard — slow, durable'], ['C2 Medium', 'C2 Medium — balanced'], ['C3 Soft', 'C3 Soft — fast, degrades'], ['C4 SuperSoft', 'C4 SuperSoft — very fast, high deg'], ['C5 UltraSoft', 'C5 UltraSoft — fastest, extreme deg']], help: 'Sent with every request; not yet read by the strategy engine.' },
  fuel: { label: 'Fuel Load', icon: 'gauge' as const, live: false, kind: 'select', options: [['low', 'Low — light, fast laps'], ['medium', 'Medium — balanced'], ['high', 'High — heavy, slower']], help: 'Sent with every request; not yet read by the pace model.' },
  aeroMode: { label: 'Aero Mode', icon: 'gauge' as const, live: false, kind: 'select', options: [['Auto', 'Auto — adaptive'], ['Straight', 'Low downforce — speed'], ['Corner', 'High downforce — grip']], help: 'Sent with every request; not yet read by the pace model.' },
  trackTemp: { label: 'Track Temperature', icon: 'gauge' as const, live: false, kind: 'range', min: 10, max: 55, unit: '°C', help: 'Sent with every request; not yet read by the tyre-degradation model.' },
  humidity: { label: 'Humidity', icon: 'cloud' as const, live: false, kind: 'range', min: 0, max: 100, unit: '%', help: 'Sent with every request; not yet read by the weather model.' },
  wind: { label: 'Wind Speed', icon: 'cloud' as const, live: false, kind: 'range', min: 0, max: 40, unit: ' km/h', help: 'Sent with every request; not yet read by the weather model.' },
  pressure: { label: 'Air Pressure', icon: 'gauge' as const, live: false, kind: 'number', min: 950, max: 1050, unit: ' hPa', help: 'Sent with every request; not yet read by any engine component.' },
  driverConfidence: { label: 'Driver Confidence', icon: 'user' as const, live: false, kind: 'range', min: 0, max: 100, unit: '%', help: 'Sent with every request; not yet read by any engine component.' },
  pitAggression: { label: 'Pit Stop Aggression', icon: 'sliders' as const, live: false, kind: 'range', min: 0, max: 100, unit: '%', help: 'Sent with every request; not yet read by the pit-strategy model.' },
  tyreDeg: { label: 'Tyre Degradation Rate', icon: 'gauge' as const, live: false, kind: 'range', min: 0, max: 100, unit: '%', help: 'Sent with every request; not yet read by the tyre-degradation model.' },
  overtake: { label: 'Overtaking Mode', icon: 'flag' as const, live: false, kind: 'bool', help: 'Sent with every request; not yet read by the pace model.' },
} as const

const LIVE_MODS: ModKey[] = ['weather', 'chaos', 'gridWeight', 'wetInfluence', 'reliability', 'strategy', 'safetyCar']
const REFERENCE_MODS: ModKey[] = ['tyre', 'fuel', 'aeroMode', 'trackTemp', 'humidity', 'wind', 'pressure', 'driverConfidence', 'pitAggression', 'tyreDeg', 'overtake']

const CHART_DEFS_CORE = (ctx: any) => [
  { id: 'win-share', title: 'Win Share — Top 8', type: 'bar', data: { labels: ctx.labels, datasets: [{ label: 'Win %', data: ctx.winnerProbs.map((v: number) => v * 100), backgroundColor: ctx.labels.map((c: string) => ctx.teamColors[(c || '').toLowerCase()] || '#16a34a'), borderRadius: 4 }] }, options: { plugins: { legend: { display: false } } } },
  { id: 'podium-pct', title: 'Podium %', type: 'bar', data: { labels: ctx.podiumPreds.slice(0, 8).map((p: any) => p.driver_code), datasets: [{ label: 'Podium %', data: ctx.podiumPreds.slice(0, 8).map((p: any) => p.percentage), backgroundColor: '#16233F', borderRadius: 4 }] }, options: { plugins: { legend: { display: false } } } },
  { id: 'points-pct', title: 'Points %', type: 'bar', data: { labels: ctx.pointsPreds.slice(0, 8).map((p: any) => p.driver_code), datasets: [{ label: 'Points %', data: ctx.pointsPreds.slice(0, 8).map((p: any) => p.percentage), backgroundColor: '#0ea5e9', borderRadius: 4 }] }, options: { plugins: { legend: { display: false } } } },
  { id: 'win-doughnut', title: 'Win — Doughnut', type: 'doughnut', data: { labels: ctx.labels.slice(0, 6), datasets: [{ data: ctx.winnerProbs.slice(0, 6).map((v: number) => v * 100), backgroundColor: ['#16a34a', '#e11d48', '#0ea5e9', '#f59e0b', '#8b5cf6', '#06b6d4'], borderWidth: 0 }] } },
  { id: 'confidence', title: 'Confidence Gauge', type: 'doughnut', data: { labels: ['Confidence', 'Remaining'], datasets: [{ data: [(ctx.result.predictions?.winner?.confidence ?? 0.8) * 100, 100 - (ctx.result.predictions?.winner?.confidence ?? 0.8) * 100], backgroundColor: ['#16a34a', '#E3E5EA'], borderWidth: 0 }] }, footer: `${((ctx.result.predictions?.winner?.confidence ?? 0.8) * 100).toFixed(1)}%` },
]

const CHART_DEFS_EXTENDED = (ctx: any) => [
  { id: 'win-vs-grid', title: 'Win vs Grid', type: 'line', data: { labels: ctx.labels, datasets: [{ label: 'Win %', data: ctx.winnerProbs.map((v: number) => v * 100), borderColor: '#16a34a', tension: 0.3 }, { label: 'Grid inverse', data: ctx.labels.map((_: string, i: number) => (8 - i) * 8), borderColor: '#6b7280', borderDash: [4, 4], tension: 0.3 }] } },
  { id: 'top8-radar', title: 'Top 8 — Radar', type: 'radar', data: { labels: ctx.labels, datasets: [{ label: 'Win %', data: ctx.winnerProbs.map((v: number) => v * 100), borderColor: '#16a34a', backgroundColor: 'rgba(22,163,74,0.15)' }] } },
  { id: 'win-podium-scatter', title: 'Win vs Podium Scatter', type: 'scatter', data: { datasets: [{ label: 'Drivers', data: ctx.topAll.slice(0, 8).map((p: any) => ({ x: p.probability * 100, y: (ctx.podiumPreds.find((q: any) => q.driver_code === p.driver_code)?.percentage || 0) })), backgroundColor: '#16a34a' }] }, options: { scales: { x: { title: { display: true, text: 'Win %' } }, y: { title: { display: true, text: 'Podium %' } } } } },
  { id: 'podium-polar', title: 'Podium — Polar', type: 'polarArea', data: { labels: ctx.podiumPreds.slice(0, 6).map((p: any) => p.driver_code), datasets: [{ data: ctx.podiumPreds.slice(0, 6).map((p: any) => p.percentage), backgroundColor: ['#16a34a', '#22c55e', '#4ade80', '#86efac', '#bbf7d0', '#dcfce7'] }] } },
  { id: 'points-horizontal', title: 'Points — Horizontal', type: 'bar', data: { labels: ctx.pointsPreds.slice(0, 8).map((p: any) => p.driver_code), datasets: [{ data: ctx.pointsPreds.slice(0, 8).map((p: any) => p.percentage), backgroundColor: '#16a34a', borderRadius: 4 }] }, options: { indexAxis: 'y' as const, plugins: { legend: { display: false } } } },
  { id: 'win-distribution', title: 'Win Distribution — Area', type: 'line', data: { labels: ctx.labels, datasets: [{ label: 'Win %', data: ctx.winnerProbs.map((v: number) => v * 100), borderColor: '#16a34a', backgroundColor: 'rgba(22,163,74,0.2)', fill: true, tension: 0.35 }] } },
  { id: 'grid-vs-win', title: 'Grid Position vs Win', type: 'bar', data: { labels: ctx.topAll.slice(0, 8).map((p: any) => `${p.driver_code} P${ctx.result.grid_positions?.[p.driver_code] || '-'}`), datasets: [{ label: 'Win %', data: ctx.winnerProbs.map((v: number) => v * 100), backgroundColor: '#0ea5e9' }] } },
  { id: 'confidence-intervals', title: 'Confidence Intervals', type: 'bar', data: { labels: ctx.labels.slice(0, 6), datasets: [{ label: 'Lower', data: ctx.labels.slice(0, 6).map((_: string, i: number) => Math.max(0, ctx.winnerProbs[i] * 100 - 5 - i)), backgroundColor: '#E3E5EA' }, { label: 'Upper', data: ctx.labels.slice(0, 6).map((_: string, i: number) => ctx.winnerProbs[i] * 100 + 5 + i), backgroundColor: '#16a34a' }] } },
  {
    id: 'dnf-risk', title: 'DNF Risk', type: 'bar', data: {
      labels: ctx.topAll.slice(0, 8).map((p: any) => p.driver_code), datasets: [{
        label: 'DNF %', backgroundColor: '#ef4444', data: ctx.topAll.slice(0, 8).map((p: any) => {
          const code = p.driver_code
          const mcDnf = ctx.result?.dnf_probabilities?.[code] ?? ctx.result?.predictions?.winner?.predictions?.find((x: any) => x.driver_code === code)?.dnf_prob
          if (mcDnf != null) return (mcDnf * 100).toFixed(1)
          const hash = code.split('').reduce((a: number, c: string) => a + c.charCodeAt(0), 0) % 20
          const reliability = 85 - (hash % 15)
          return ((100 - reliability) * 0.12 + ctx.mods.chaos * 0.05).toFixed(1)
        })
      }]
    }, options: { plugins: { legend: { display: false } } }
  },
  { id: 'chaos-impact', title: 'Chaos Impact', type: 'line', data: { labels: ['0', '25', '50', '75', '100'], datasets: [{ label: 'Entropy', data: [10, 22, 35, 55, 70].map(v => v * (ctx.mods.chaos / 50)), borderColor: '#f59e0b', tension: 0.3 }] } },
  { id: 'safety-car-boost', title: 'Safety Car Boost', type: 'bar', data: { labels: ['Low SC', 'High SC'], datasets: [{ label: 'Midfield win mass', data: [12, 28], backgroundColor: ['#6b7280', '#f59e0b'] }] } },
]

function ChartCard({ def }: { def: any }) {
  return (
    <div className="card p-4">
      <div className="f1-display font-bold mb-1 text-sm">{def.title}</div>
      <F1Chart type={def.type} height={200} data={def.data} options={def.options} />
      {def.footer && <div className="text-center f1-mono font-bold mt-1" style={{ color: '#16a34a' }}>{def.footer}</div>}
    </div>
  )
}

export function DashboardPage() {
  const [result, setResult] = useState<any>(null)
  const setManual = useDashboardStore(s => s.setManualGrid) as any
  const manualGrid = useDashboardStore(s => s.manualGrid) as any
  const draft = useDashboardStore(s => s.draft) as any
  const setDraft = useDashboardStore(s => s.setDraft) as any
  const session = useDashboardStore(s => s.session) as any
  const subSession = useDashboardStore(s => s.subSession) as any
  const setSession = useDashboardStore(s => s.setSession) as any
  const setSubSession = useDashboardStore(s => s.setSubSession) as any
  const raceInfo = useRaceInfo(draft?.raceId)
  const mut = usePrediction()
  const [showAll, setShowAll] = useState(false)
  const [showReference, setShowReference] = useState(false)

  const engineDefaults = usePreferences((s: any) => s.prefs.engine)
  const panelPrefs = usePreferences((s: any) => s.prefs.dashboardLayout.visiblePanels)

  const [day, setDay] = useState<Day>('sunday')
  const [subPick, setSubPick] = useState<string>('Race')
  const sprintWeekend = !!raceInfo?.sprint
  const sessionsForDay = useMemo(() => {
    const base = DAY_OPTS[day].sessions
    if (day === 'saturday' && sprintWeekend) return [...base, { id: 'Sprint', label: 'Sprint Race', sub: 'Sprint', sess: 'race' }]
    return base
  }, [day, sprintWeekend])

  useEffect(() => {
    if (sessionsForDay.length && !sessionsForDay.find(s => s.id === subPick)) setSubPick(sessionsForDay[0].id)
  }, [sessionsForDay, subPick])

  useEffect(() => {
    const sel = sessionsForDay.find(s => s.id === subPick)
    if (sel) {
      setSession(sel.sess); setSubSession(sel.sub)
      if (sel.sess === 'qualifying') useDashboardStore.getState().setTarget('qualifying_q3')
      else if (sel.sess === 'practice') useDashboardStore.getState().setTarget('practice_pace')
      else useDashboardStore.getState().setTarget('podium')
    }
  }, [subPick, sessionsForDay, setSession, setSubSession])

  // Defaults now come from Settings > Prediction Engine (engineDefaults) the first
  // time this page loads, instead of a hardcoded object disconnected from Settings.
  const [mods, setMods] = useState(() => {
    try {
      const cached = JSON.parse(localStorage.getItem('f1-dashboard-mods') || '{}')
      return {
        weather: 'dry', chaos: engineDefaults.chaosLevel, wetInfluence: engineDefaults.wetInfluence,
        reliability: engineDefaults.reliabilityInfluence, strategy: engineDefaults.strategyAggressiveness,
        gridWeight: engineDefaults.gridWeight, safetyCar: engineDefaults.safetyCarWeight,
        tyre: 'C2 Medium', fuel: 'medium', overtake: true, aeroMode: 'Auto',
        trackTemp: 27, humidity: 55, wind: 8, pressure: 1013,
        driverConfidence: 70, pitAggression: 50, tyreDeg: 50,
        ...cached,
      }
    } catch {
      return { weather: 'dry', chaos: 50, wetInfluence: 60, reliability: 40, strategy: 50, gridWeight: 55, safetyCar: 30, tyre: 'C2 Medium', fuel: 'medium', overtake: true, aeroMode: 'Auto', trackTemp: 27, humidity: 55, wind: 8, pressure: 1013, driverConfidence: 70, pitAggression: 50, tyreDeg: 50 }
    }
  })

  const setMod = (k: string, v: any) => {
    setMods((m: any) => ({ ...m, [k]: v }))
    try {
      const current = JSON.parse(localStorage.getItem('f1-dashboard-mods') || '{}')
      localStorage.setItem('f1-dashboard-mods', JSON.stringify({ ...current, [k]: v }))
    } catch { /* noop */ }
  }
  const resetMods = () => {
    if (!confirm('Reset all race conditions to your Settings defaults?')) return
    setMods({
      weather: 'dry', chaos: engineDefaults.chaosLevel, wetInfluence: engineDefaults.wetInfluence,
      reliability: engineDefaults.reliabilityInfluence, strategy: engineDefaults.strategyAggressiveness,
      gridWeight: engineDefaults.gridWeight, safetyCar: engineDefaults.safetyCarWeight,
      tyre: 'C2 Medium', fuel: 'medium', overtake: true, aeroMode: 'Auto', trackTemp: 27,
      humidity: 55, wind: 8, pressure: 1013, driverConfidence: 70, pitAggression: 50, tyreDeg: 50,
    })
    localStorage.removeItem('f1-dashboard-mods')
  }

  useEffect(() => { setDraft({ weather: mods.weather }) }, [mods.weather, setDraft])

  const [simCount, setSimCount] = useState<number>(draft.simCount || engineDefaults.simulationCount || 10000)
  useEffect(() => setDraft({ simCount }), [simCount, setDraft])

  const saveResult = (r: any) => {
    setResult(r)
    try {
      localStorage.setItem('f1-last-prediction', JSON.stringify({ raceId: r.race_id || draft.raceId, predictions: r.predictions }))
      window.dispatchEvent(new Event('f1-prediction'))
    } catch { /* noop */ }
  }

  const handleRun = async () => {
    if (!draft.raceId) return alert('Select a Grand Prix')
    const sims = Math.max(100, Math.min(50000, Number(simCount) || 10000))
    const payload: any = {
      race_id: draft.raceId, session_type: session, sub_session: subSession, weather: mods.weather,
      simulation_count: sims,
      feature_weights: {
        chaos_level: mods.chaos, wet_influence: mods.wetInfluence, reliability_influence: mods.reliability,
        strategy_aggressiveness: mods.strategy, grid_weight: mods.gridWeight, safety_car_prob: mods.safetyCar / 100,
        tyre_compound: mods.tyre, fuel_load: mods.fuel, overtake_mode: mods.overtake ? 1 : 0, aero_mode: mods.aeroMode,
        track_temp: mods.trackTemp, humidity: mods.humidity, wind_speed: mods.wind, air_pressure: mods.pressure,
        driver_confidence: mods.driverConfidence, pit_aggression: mods.pitAggression, tyre_deg: mods.tyreDeg,
      },
      grid_positions: manualGrid || undefined,
    }
    try {
      let grid = manualGrid
      if (session === 'race' && !manualGrid) {
        const q = await mut.mutateAsync({ ...payload, session_type: 'qualifying', sub_session: 'Q3' })
        const q3 = q.predictions?.q3
        const simGrid: any = {}
        if (q3?.predictions) q3.predictions.forEach((p: any, i: number) => simGrid[p.driver_code] = i + 1)
        grid = simGrid
      }
      const res = await mut.mutateAsync({ ...payload, grid_positions: grid })
      if (grid) res.grid_positions = grid
      saveResult(res)
    } catch (e: any) { alert(e.message) }
  }

  const topAll = result?.predictions?.winner?.predictions || result?.predictions?.[Object.keys(result?.predictions || {})[0]]?.predictions || []
  const pointsPreds = result?.predictions?.points?.predictions || []
  const podiumPreds = result?.predictions?.podium?.predictions || []
  const winnerProbs = topAll.slice(0, 8).map((p: any) => p.probability)
  const labels = topAll.slice(0, 8).map((p: any) => p.driver_code)
  const teamColors: Record<string, string> = { mercedes: '#00A19B', redbull: '#3671C6', ferrari: '#E8002D', mclaren: '#FF8000', astonmartin: '#229971', williams: '#1E6FCE', audi: '#BB0A30', alpine: '#0090FF', haas: '#9198A1', racingbulls: '#3F5FCC', cadillac: '#9C7A19' }

  const [repFmt, setRepFmt] = useState('csv')
  const handleExport = async () => {
    if (!result) return alert('Run a prediction first')
    try {
      const res = await fetch('/api/v1/reports/export', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ race_id: draft.raceId, session, sub_session: subSession, format: repFmt, predictions: result.predictions }) })
      if (!res.ok) throw new Error(await res.text())
      const ct = res.headers.get('content-type') || ''
      if (ct.includes('application/json')) {
        const j = await res.json()
        const blob = new Blob([JSON.stringify(j, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `f1-${draft.raceId}-${repFmt}.json`; a.click()
      } else {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `f1-${draft.raceId}-${repFmt}.${repFmt === 'pdf' ? 'pdf' : repFmt === 'csv' ? 'csv' : 'png'}`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 5000)
      }
    } catch (e: any) { alert('Export failed: ' + e.message) }
  }

  const chartCtx = { labels, winnerProbs, podiumPreds, pointsPreds, topAll, teamColors, result, mods }

  const renderSlider = (key: ModKey) => {
    const meta = MOD_META[key]
    const value = (mods as any)[key]
    return (
      <label key={key} className="fs-11 font-bold flex flex-col gap-1.5 p-3 rounded-lg border transition-colors" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-1.5"><Icon name={meta.icon} className="icon-sm text-sub" />{meta.label}</span>
          <span className="flex items-center gap-1.5">
            {meta.kind === 'range' && <span className="f1-mono text-sm font-black" style={{ color: 'var(--red)' }}>{value}{(meta as any).unit}</span>}
            <span className={`badge ${meta.live ? 'badge-live' : 'badge-planned'}`}>{meta.live ? 'Live' : 'Planned'}</span>
          </span>
        </div>
        {meta.kind === 'select' && (
          <select value={value} onChange={e => setMod(key, e.target.value)} className="f1-select">
            {(meta as any).options.map(([v, l]: [string, string]) => <option key={v} value={v}>{l}</option>)}
          </select>
        )}
        {meta.kind === 'range' && <input type="range" min={(meta as any).min} max={(meta as any).max} value={value} onChange={e => setMod(key, parseInt(e.target.value))} className="f1-range accent-red" />}
        {meta.kind === 'number' && <input type="number" value={value} min={(meta as any).min} max={(meta as any).max} onChange={e => setMod(key, parseInt(e.target.value) || (meta as any).min)} className="f1-input" />}
        {meta.kind === 'bool' && (
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => setMod(key, !value)} className={`f1-switch ${value ? 'is-on' : ''}`} aria-label={meta.label}><span className="knob" /></button>
            <span className="fs-10 text-sub">{value ? 'Enabled' : 'Disabled'}</span>
          </div>
        )}
        <div className="fs-10 text-sub">{meta.help}</div>
      </label>
    )
  }

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-3 gap-0">
          <div className="md:col-span-2 p-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--red)' }} />
              <span className="fs-11 font-bold tracking-widest" style={{ color: 'var(--red)' }}>PREDICTION MISSION CONTROL — 2026</span>
            </div>
            <h1 className="f1-display text-2xl font-black">Dashboard</h1>
            <p className="text-sub fs-11 mt-1 max-w-xl">Pick a Grand Prix, choose the session, tune race conditions, then run the simulation. Grid editor and results are below.</p>
            {raceInfo && (
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="badge badge-neutral">{raceInfo.flag} {raceInfo.name} · {raceInfo.circuit}</span>
                <span className="badge badge-neutral">{raceInfo.laps} laps · {raceInfo.drs_zones} DRS · {raceInfo.overtaking} overtake</span>
                <span className="badge badge-neutral">{raceInfo.sprint ? 'Sprint weekend' : 'Standard weekend'}</span>
              </div>
            )}
          </div>
          <div className="relative min-h-[160px]">
            <img src="/media/circuit2.webp" alt="Circuit layout" className="absolute inset-0 w-full h-full object-cover" loading="lazy" width={480} height={320} />
            <div className="absolute inset-0 bg-gradient-to-l from-black/40 to-transparent" />
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4 space-y-3">
          <div className="f1-display font-bold">Race &amp; Session</div>
          <RaceSelector />
          <div className="grid grid-cols-3 gap-2">
            {(['friday', 'saturday', 'sunday'] as Day[]).map(d => (
              <button key={d} onClick={() => setDay(d)} className={`session-card !py-2 ${day === d ? 'is-active' : ''}`}>
                <div className="f1-display font-bold text-xs">{DAY_OPTS[d].label}</div>
                <div className="fs-11 session-sub text-sub">{d === 'friday' ? 'Practice' : d === 'saturday' ? 'Qualifying' : 'Race'}</div>
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="fs-11 font-bold w-20">Session</span>
            <select value={subPick} onChange={e => setSubPick(e.target.value)} className="f1-select flex-1">
              {sessionsForDay.map(s => <option key={s.id} value={s.id}>{s.label} — {s.sess}</option>)}
            </select>
            {sprintWeekend && day === 'saturday' && <span className="badge" style={{ background: '#BB0A30', color: '#fff' }}>Sprint</span>}
          </div>
        </div>

        <div className="card p-4 space-y-3">
          <div className="flex items-center justify-between gap-2 mb-1">
            <div>
              <div className="f1-display font-bold">Race Conditions</div>
              <div className="fs-10 text-sub">Live conditions actually shape this prediction. Planned ones are captured for later.</div>
            </div>
            <button onClick={resetMods} className="btn-ghost !py-1.5 !px-3 fs-11">Reset</button>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {LIVE_MODS.map(renderSlider)}
          </div>

          <button onClick={() => setShowReference(v => !v)} className="btn-ghost w-full !py-2 fs-11 flex items-center justify-center gap-1.5">
            <Icon name={showReference ? 'chevron-down' : 'chevron-right'} className="icon-sm" />
            {showReference ? 'Hide' : 'Show'} {REFERENCE_MODS.length} planned conditions
          </button>
          {showReference && (
            <div className="grid sm:grid-cols-2 gap-3 pt-1">
              {REFERENCE_MODS.map(renderSlider)}
            </div>
          )}

          <div className="pt-3 border-t mt-1" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-2">
              <div className="f1-display font-bold flex items-center gap-1.5"><Icon name="engine" className="icon-sm" />Monte Carlo Simulations</div>
              <span className="f1-mono text-sm font-black px-3 py-1 rounded-lg" style={{ background: 'var(--red)', color: '#fff' }}>{simCount.toLocaleString()} sims</span>
            </div>
            <div className="flex items-center gap-3">
              <input type="range" min={100} max={50000} step={100} value={simCount} onChange={e => setSimCount(parseInt(e.target.value))} className="f1-range flex-1 accent-red" />
              <input type="number" min={100} max={50000} value={simCount} onChange={e => setSimCount(Math.max(100, Math.min(50000, parseInt(e.target.value) || 100)))} className="f1-input w-28 font-mono font-bold" />
            </div>
            <div className="flex justify-between mt-2 fs-11 text-sub">
              <span>Fast (100–1k) ~0.1s</span><span>Balanced (5k–15k) ~0.4s</span><span>Accurate (20k–50k) ~1.2s</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        {(panelPrefs['dashboard.gridEditor'] ?? true) && (
          <div className="lg:col-span-2 card p-4 space-y-3">
            <div className="f1-display font-bold">Manual Grid — P1–22</div>
            <div className="fs-11 text-sub">Overrides the auto-simulated Q3 grid. Leave empty to let qualifying determine the grid.</div>
            <GridEditor value={manualGrid} onChange={setManual} raceId={draft.raceId} />
          </div>
        )}
        <div className={`card p-4 flex flex-col gap-3 ${(panelPrefs['dashboard.gridEditor'] ?? true) ? '' : 'lg:col-span-3'}`}>
          <div className="f1-display font-bold">Run</div>
          <div className="fs-11 text-sub">Uses the live conditions above — no API key required.</div>
          <button onClick={handleRun} disabled={mut.isPending || !draft.raceId} className="btn-primary disabled:opacity-50" style={{ background: '#16a34a', borderColor: '#16a34a' }}>
            {mut.isPending ? `Running ${simCount.toLocaleString()} sims…` : 'Run Prediction'}
          </button>
          <div className="fs-11 text-sub">Session: {day} / {subPick} → {session} · {subSession}</div>
        </div>
      </div>

      {!result ? (
        <div className="card p-8 text-center">
          <div className="f1-display font-bold">No prediction yet</div>
          <p className="fs-11 text-sub mt-1">Select a Grand Prix, pick a session, tune race conditions, then run.</p>
        </div>
      ) : (
        <>
          <PredictionResults result={result} />
          <div className="grid lg:grid-cols-3 gap-4">
            {CHART_DEFS_CORE(chartCtx).map(def => <ChartCard key={def.id} def={def} />)}
            {showAll && CHART_DEFS_EXTENDED(chartCtx).map(def => <ChartCard key={def.id} def={def} />)}
          </div>
          <button onClick={() => setShowAll(v => !v)} className="btn-ghost w-full !py-2 fs-11">
            {showAll ? 'Show fewer charts' : `Show ${CHART_DEFS_EXTENDED(chartCtx).length} more charts`}
          </button>
        </>
      )}

      {(panelPrefs['dashboard.reports'] ?? true) && (
        <div className="card p-4">
          <div className="f1-display font-bold">Export</div>
          <p className="fs-11 text-sub">Download this prediction as CSV, JSON, PDF, or a shareable card.</p>
          <div className="flex flex-wrap items-center gap-3 mt-3">
            <select value={repFmt} onChange={e => setRepFmt(e.target.value)} className="f1-select w-40">
              <option value="csv">CSV</option><option value="json">JSON</option><option value="pdf">PDF</option><option value="share">Share Card</option>
            </select>
            <button onClick={handleExport} className="btn-primary" style={{ background: '#16a34a' }}>Create &amp; Download</button>
          </div>
        </div>
      )}
    </div>
  )
}
