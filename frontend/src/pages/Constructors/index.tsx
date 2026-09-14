import { useQuery } from '@tanstack/react-query'
import { fetchTeams, fetchPowerRankings } from '../../api/constructors'
import { F1Chart } from '../../components/charts/F1Chart'

export function ConstructorsPage(){
  const {data:teams}=useQuery({queryKey:['constructors','teams'], queryFn: fetchTeams})
  const {data:rankings}=useQuery({queryKey:['constructors','power'], queryFn: fetchPowerRankings})
  const teamList:any[] = ((teams as any)?.data ?? teams) as any[] || []
  const rankList:any[] = ((rankings as any)?.data ?? rankings) as any[] || []
  const TEAM_META: Record<string, { color:string, note:string }> = {
    mercedes: { color:'#00A19B', note:'Works — 2026 PU 50/50' },
    redbull: { color:'#3671C6', note:'Red Bull Powertrains + Ford' },
    ferrari: { color:'#E8002D', note:'Works' },
    mclaren: { color:'#FF8000', note:'2025 Champions' },
    astonmartin: { color:'#229971', note:'Honda 2026' },
    williams: { color:'#1E6FCE', note:'Mercedes customer' },
    audi: { color:'#BB0A30', note:'NEW 2026 — Works' },
    alpine: { color:'#0090FF', note:'Renault' },
    haas: { color:'#9198A1', note:'Ferrari customer' },
    racingbulls: { color:'#3F5FCC', note:'Red Bull family' },
    cadillac: { color:'#9C7A19', note:'NEW 2026 — GM 2029 PU' },
  }
  const powerChart = {
    labels: rankList.slice(0,11).map((r:any)=> r.team||r.name),
    datasets:[{ label:'Power', data: rankList.slice(0,11).map((r:any)=> r.power ?? r.score ?? 50), backgroundColor: rankList.slice(0,11).map((r:any)=> TEAM_META[(r.team||'').toLowerCase()]?.color || '#ccc'), borderRadius:4 }]
  }
  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/f1_cartoon.png" alt="F1 cartoon" loading="lazy" className="w-full h-56 object-cover" />
          <div className="p-6">
            <h2 className="f1-display text-2xl font-black">Constructors — 2026 Grid</h2>
            <p className="fs-11 text-sub mt-1">11 teams, 22 drivers. Audi & Cadillac join, 50/50 PU (400kW ICE + 350kW elec), sustainable fuels, active aero. Power rankings from <code className="f1-mono">team_data.get_team_power_rankings()</code>.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge" style={{ background:'#BB0A30', color:'#fff'}}>AUDI NEW</span>
              <span className="badge" style={{ background:'#9C7A19', color:'#fff'}}>CADILLAC NEW</span>
              <span className="badge">11 Teams</span>
              <span className="badge">2026 Regs</span>
            </div>
          </div>
        </div>
      </div>

      {/* Power rankings chart */}
      <div className="card p-4">
        <div className="f1-display font-bold">Power Rankings — 2026</div>
        <p className="fs-11 text-sub">Team power (strength + PU + aero) — Audi/Cadillac debut with 2026 PU advantage.</p>
        <F1Chart type="bar" height={260} data={powerChart as any} options={{ indexAxis:'y' as const, plugins:{legend:{display:false}}}} />
      </div>

      {/* Teams grid — modern cards */}
      <div>
        <div className="f1-display font-bold text-lg">Teams — Car by Car</div>
        <p className="fs-11 text-sub">Team-accurate colours from `constants.py:TEAM_COLORS`, car silhouette from `car_parts.png`.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          {(teamList.length? teamList : Array.from({length:11},(_,i)=>({ name:`Team ${i+1}`, color:'#ccc' }))).map((t:any)=>{
            const key = (t.team_id||t.id||t.name||'').toLowerCase()
            const meta = TEAM_META[key] || { color: t.color||t.color_hex||'#ccc', note:'' }
            const isNew = ['audi','cadillac'].includes(key)
            return (
              <div key={t.id||t.name} className="card p-0 overflow-hidden group hover:shadow-xl transition-shadow">
                <div className="h-2" style={{ background: meta.color }} />
                <div className="p-4">
                  <div className="flex items-center gap-3">
                    <img src="/media/car_parts.png" alt="car" className="w-14 h-10 object-contain opacity-90 group-hover:scale-105 transition-transform" loading="lazy" />
                    <div>
                      <div className="f1-display font-bold flex items-center gap-2">{t.name} {isNew && <span className="px-2 py-0.5 rounded-full text-white fs-11 text-[10px]" style={{ background: meta.color}}>2026 NEW</span>}</div>
                      <div className="fs-11 text-sub">{meta.note}</div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    <span className="team-bar" style={{ background: meta.color }} />
                    <span className="fs-11">PU: {key.includes('mercedes')||key==='williams'?'Mercedes':key.includes('redbull')?'Red Bull/Ford':key==='ferrari'?'Ferrari':key==='audi'?'Audi':key==='cadillac'?'Cadillac (GM 2029)':'—'}</span>
                  </div>
                  <div className="mt-3 fs-11 text-sub">Drivers: {(t.drivers||[]).slice(0,2).map((d:any)=> d.name||d.code).join(' · ') || '— see Standings'}</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Circuit context */}
      <div className="card p-0 overflow-hidden">
        <img src="/media/circuit2.png" alt="Circuit" loading="lazy" className="w-full h-48 object-cover" />
        <div className="p-4">
          <div className="f1-display font-bold">2026 Circuits — Active Aero Everywhere</div>
          <p className="fs-11 text-sub mt-1">X-mode (Straight, low drag) on every designated straight, Z-mode (Corner) elsewhere. Overtake Mode replaces DRS — within 1s → +0.5MJ, 350kW to 337 km/h. Pitlane image: <code className="f1-mono">circuit_data.py</code> DRS zones.</p>
        </div>
      </div>
    </div>
  )
}
