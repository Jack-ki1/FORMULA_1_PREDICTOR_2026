import { useQuery } from '@tanstack/react-query'
import { fetchTeams, fetchPowerRankings } from '../../api/constructors'
export function ConstructorsPage(){
  const {data:teams}=useQuery({queryKey:['constructors','teams'], queryFn: fetchTeams})
  const {data:rankings}=useQuery({queryKey:['constructors','power'], queryFn: fetchPowerRankings})
  return (
    <div className="px-4 sm:px-8 py-6 space-y-4">
      <h2 className="f1-display text-xl font-bold">Constructors</h2>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Teams</div>
          <div className="space-y-2">{(teams||[]).map((t:any)=><div key={t.id||t.name} className="flex items-center gap-2"><span className="team-bar" style={{background: t.color||t.color_hex||'#ccc'}}></span><span className="font-semibold">{t.name}</span></div>)}</div>
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Power Rankings</div>
          <div className="space-y-1">{(rankings||[]).slice(0,11).map((r:any,i:number)=><div key={r.team||i} className="flex justify-between fs-11"><span>{r.team||r.name}</span><span className="f1-mono">{r.power||r.score||'-'}</span></div>)}</div>
        </div>
      </div>
    </div>
  )
}
