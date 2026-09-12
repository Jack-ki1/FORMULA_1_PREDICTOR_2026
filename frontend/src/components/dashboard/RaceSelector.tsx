import { useRaces } from '../../hooks/useRaces'
import { useDashboardStore } from '../../stores/dashboardStore'
export function RaceSelector(){
  const { data: races } = useRaces()
  const draft = useDashboardStore(s=>s.draft) as any
  const setDraft = useDashboardStore(s=>s.setDraft) as any
  const active = races?.filter((r:any)=> r.status!=='cancelled')||[]
  return (
    <div className="card p-4">
      <div className="f1-display font-bold">Grand Prix</div>
      <select className="f1-select mt-2" value={draft.raceId} onChange={e=> setDraft({raceId:e.target.value})}>
        <option value="">Select a Grand Prix</option>
        {active.map((r:any)=><option key={r.id} value={r.id}>{r.name} — {r.circuit}</option>)}
      </select>
    </div>
  )
}
