import { useDriverStandings, useConstructorStandings } from '../../hooks/useStandings'
import { useDrivers } from '../../hooks/useH2H'
import { TeamStripe } from '../../components/shared/TeamStripe'

export function StandingsPage(){
  const {data: drivers, isLoading: ld} = useDriverStandings()
  const {data: constructors, isLoading: lc} = useConstructorStandings()
  const {data: allDrivers} = useDrivers()
  const colorByCode: Record<string,string> = {}
  ;(allDrivers||[]).forEach((d:any)=> { colorByCode[d.code]=d.team_color })
  const top3 = (drivers?.data||drivers||[]).slice(0,3)
  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      <div className="relative overflow-hidden rounded-xl" style={{ background: `linear-gradient(135deg, #0a0a09 0%, #16233F 100%)` }}>
        <img src="/media/podium_all.png" alt="Podium" className="absolute inset-0 w-full h-full object-cover opacity-30" loading="lazy" />
        <div className="relative p-6 sm:p-8 text-white">
          <h2 className="f1-display text-2xl font-bold">Standings — 2026 Championship</h2>
          <p className="fs-11 mt-1" style={{ color: 'rgba(255,255,255,.75)' }}>Live Jolpica → local fallback • 22 drivers • 11 constructors • Active aero era</p>
        </div>
      </div>

      {top3.length===3 && (
        <div className="grid grid-cols-3 gap-3 items-end">
          {[top3[1], top3[0], top3[2]].map((d:any,i:number)=>{
            const rank = [2,1,3][i]
            const code = d.driver_code||d.code
            const img = rank===1 ? '/media/p1.png' : rank===2 ? '/media/p2.png' : '/media/p3.png'
            return (
              <div key={code} className="card overflow-hidden text-center" style={{ borderTop: `4px solid ${colorByCode[code]||'var(--red)'}` }}>
                <img src={img} alt={`P${rank}`} loading="lazy" className="w-full h-24 object-cover" />
                <div className="p-3">
                  <div className="f1-mono fs-11 font-bold" style={{ color: 'var(--red)' }}>P{rank}</div>
                  <div className="f1-display font-bold text-sm">{d.driver_name||d.name||code}</div>
                  <div className="fs-11 text-sub">{d.team||''}</div>
                  <div className="f1-mono font-bold mt-1">{d.points ?? 0} pts</div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Driver Standings</div>
          {ld? 'Loading…': <div className="overflow-x-auto"><table className="f1-table w-full"><thead><tr><th>#</th><th>Driver</th><th>Pts</th></tr></thead><tbody>{(drivers?.data||drivers||[]).slice(0,22).map((d:any,i:number)=> {
            const code = d.driver_code||d.code
            return <tr key={code||i}><td>{d.position||i+1}</td><td className="flex items-center gap-2"><TeamStripe color={colorByCode[code]} />{d.driver_name||d.name||code}</td><td>{d.points??'-'}</td></tr>
          })}</tbody></table></div>}
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Constructor Standings</div>
          {lc? 'Loading…': <div className="overflow-x-auto"><table className="f1-table w-full"><thead><tr><th>#</th><th>Team</th><th>Pts</th></tr></thead><tbody>{(constructors?.data||constructors||[]).slice(0,11).map((t:any,i:number)=><tr key={t.team||t.name||i}><td>{t.position||i+1}</td><td className="flex items-center gap-2"><TeamStripe color={t.color||t.color_hex} />{t.team||t.name}</td><td>{t.points??'-'}</td></tr>)}</tbody></table></div>}
        </div>
      </div>
      <div className="card p-0 overflow-hidden">
        <img src="/media/circuit1.png" alt="Circuit" loading="lazy" className="w-full h-48 object-cover" />
        <div className="p-4">
          <div className="f1-display font-bold">2026 Regulations — Nimble Cars</div>
          <p className="fs-11 text-sub mt-1">30kg lighter (768kg), 200mm shorter wheelbase, active aero Straight/Corner modes, Overtake Mode + Boost. Close racing by design.</p>
        </div>
      </div>
    </div>
  )
}
