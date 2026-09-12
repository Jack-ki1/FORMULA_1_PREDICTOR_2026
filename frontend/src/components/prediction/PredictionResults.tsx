export function PredictionResults({result}:{result:any}){
  if(!result) return <div className="empty-state p-8 text-center text-muted">No prediction yet — select a race and run the engine.</div>
  const targets = Object.keys(result.predictions||{})
  return (
    <div className="space-y-4">
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
                    {summary.predictions.slice(0,12).map((p:any,i:number)=>
                      <tr key={p.driver_code}><td className="f1-mono">{i+1}</td><td className="font-semibold">{p.driver_code}</td><td className="f1-mono">{p.probability.toFixed(4)}</td><td>{p.percentage.toFixed(2)}%</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
