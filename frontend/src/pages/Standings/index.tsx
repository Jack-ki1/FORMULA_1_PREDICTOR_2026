import { useDriverStandings, useConstructorStandings } from '../../hooks/useStandings'
export function StandingsPage(){
  const {data: drivers, isLoading: ld} = useDriverStandings()
  const {data: constructors, isLoading: lc} = useConstructorStandings()
  return (
    <div className="px-4 sm:px-8 py-6 space-y-4">
      <h2 className="f1-display text-xl font-bold">Standings</h2>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Driver Standings</div>
          {ld? 'Loading…': <div className="overflow-x-auto"><table className="f1-table w-full"><thead><tr><th>#</th><th>Driver</th><th>Pts</th></tr></thead><tbody>{(drivers?.data||drivers||[]).slice(0,22).map((d:any,i:number)=><tr key={d.driver_code||d.code||i}><td>{d.position||i+1}</td><td>{d.driver_name||d.name||d.driver_code||d.code}</td><td>{d.points??'-'}</td></tr>)}</tbody></table></div>}
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold mb-2">Constructor Standings</div>
          {lc? 'Loading…': <div className="overflow-x-auto"><table className="f1-table w-full"><thead><tr><th>#</th><th>Team</th><th>Pts</th></tr></thead><tbody>{(constructors?.data||constructors||[]).slice(0,11).map((t:any,i:number)=><tr key={t.team||t.name||i}><td>{t.position||i+1}</td><td>{t.team||t.name}</td><td>{t.points??'-'}</td></tr>)}</tbody></table></div>}
        </div>
      </div>
    </div>
  )
}
