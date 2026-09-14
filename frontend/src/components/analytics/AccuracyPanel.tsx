export function AccuracyPanel({ data }:any){ return <div className="card p-4"><div className="font-bold">Accuracy</div><pre className="fs-11">{JSON.stringify(data,null,2)}</pre></div>}
