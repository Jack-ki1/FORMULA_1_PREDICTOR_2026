import { useDashboardStore } from '../../stores/dashboardStore'
export function WeatherSelector(){
  const draft=useDashboardStore(s=>s.draft) as any
  const setDraft=useDashboardStore(s=>s.setDraft) as any
  return (
    <div className="flex items-center gap-2">
      <select className="f1-select" value={draft.weather} onChange={e=> setDraft({weather:e.target.value})}>
        <option value="dry">Dry</option><option value="mixed">Mixed</option><option value="wet">Wet</option>
      </select>
      <select className="f1-select" value={draft.simCount} onChange={e=> setDraft({simCount: parseInt(e.target.value)})}>
        <option value={1000}>1k sims</option><option value={5000}>5k sims</option><option value={10000}>10k sims</option><option value={50000}>50k sims</option>
      </select>
    </div>
  )
}
