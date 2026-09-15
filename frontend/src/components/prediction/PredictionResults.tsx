import { PodiumReveal } from './PodiumReveal'
import { TeamStripe } from '../shared/TeamStripe'
import { useDrivers } from '../../hooks/useH2H'
import { TireStrategy } from './TireStrategy'
export function PredictionResults({result}:{result:any}){
  const { data: drivers } = useDrivers()
  const colorByCode: Record<string,string> = {}
  ;(drivers||[]).forEach((d:any)=> colorByCode[d.code]=d.team_color)
  if(!result) return <div className="empty-state p-8 text-center text-muted">No prediction yet — select a race and run the engine.</div>
  const targets = Object.keys(result.predictions||{})
  const topDriver = targets[0] ? result.predictions[targets[0]]?.predictions?.[0]?.driver_code : undefined
  const topDriversForStrategy = targets[0] ? result.predictions[targets[0]]?.predictions?.slice(0,6).map((p:any)=> ({ driver_code: p.driver_code, team_color: colorByCode[p.driver_code]})) : []
  return (
    <div className="space-y-4">
      {topDriver && (
        <PodiumReveal trigger={`${result.race_id}-${result.session_type}-${topDriver}`} label={topDriver} />
      )}
      {topDriversForStrategy.length > 0 && <TireStrategy drivers={topDriversForStrategy} />}
      <div className="grid md:grid-cols-2 gap-4">
        {targets.map(tid=>{
          const summary=result.predictions[tid]
          return (
            <div key={tid} className="card p-4">
              <div className="f1-display font-bold">{summary.target_label} <span className="fs-11 text-sub">· confidence {(summary.confidence*100).toFixed(1)}%</span></div>
              <div className="f1-table mt-3">
                <div className="overflow-x-auto">
                  <table className="f1-table w-full">
                    <thead><tr><th>#</th><th>Driver</th><th>Prob</th><th>%</th></tr></thead>
                    <tbody>
                      {summary.predictions.slice(0,12).map((p:any,i:number)=>(
                        <tr key={p.driver_code}><td className="f1-mono">{i+1}</td><td className="font-semibold flex items-center gap-2"><TeamStripe color={colorByCode[p.driver_code]} size="small" />{p.driver_code}</td><td className="f1-mono">{p.probability.toFixed(4)}</td><td>{p.percentage.toFixed(2)}%</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
