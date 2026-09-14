import { useQuery } from '@tanstack/react-query'
import { fetchTeams, fetchPowerRankings } from '../../api/constructors'
export function ConstructorsPage(){
  const {data:teams}=useQuery({queryKey:['constructors','teams'], queryFn: fetchTeams})
  const {data:rankings}=useQuery({queryKey:['constructors','power'], queryFn: fetchPowerRankings})
  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      <div className="card p-0 overflow-hidden">
        <img src="/media/f1_cartoon.png" alt="F1 cartoon" loading="lazy" className="w-full h-48 object-cover" />
        <div className="p-6">
          <h2 className="f1-display text-xl font-bold">Constructors — 2026 Grid</h2>
          <p className="fs-11 text-sub mt-1">11 teams, 22 drivers. 2026 brings Audi & Cadillac, 50/50 power units, sustainable fuels. Power rankings from <code className="f1-mono">team_data.get_team_power_rankings()</code>.</p>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Teams</div>
          <div className="space-y-2">{(((teams as any)?.data ?? teams) || []).map((t:any)=><div key={t.id||t.name} className="flex items-center gap-3 p-2 rounded-lg hover:bg-black/5 transition-colors"><span className="team-bar" style={{background: t.color||t.color_hex||'#ccc'}}></span><img src="/media/car_parts.png" alt="car" className="w-10 h-10 object-contain opacity-80" loading="lazy" /><span className="font-semibold">{t.name}</span></div>)}</div>
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Power Rankings</div>
          <img src="/media/circuit2.png" alt="Circuit" loading="lazy" className="w-full h-32 object-cover rounded-lg mb-3" />
          <div className="space-y-1">{(((rankings as any)?.data ?? rankings) || []).slice(0,11).map((r:any,i:number)=><div key={r.team||i} className="flex justify-between fs-11 p-1.5 rounded hover:bg-black/5"><span className="font-semibold">{i+1}. {r.team||r.name}</span><span className="f1-mono">{typeof r.power==='number'? r.power.toFixed(1): r.score||'-'}</span></div>)}</div>
        </div>
      </div>
    </div>
  )
}
