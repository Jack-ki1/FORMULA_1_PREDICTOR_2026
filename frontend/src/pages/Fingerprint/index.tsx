import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
export function FingerprintPage(){
  const [data,setData]=useState<any>(null)
  useEffect(()=>{ ext.fingerprint().then(setData).catch(console.error)},[])
  if(!data) return <div className="p-8">Clustering driving styles…</div>
  return <div className="p-6 max-w-5xl mx-auto space-y-4">
    <h1 className="text-2xl font-bold">Driver Style Fingerprint — via telemetry</h1>
    <p className="text-sm opacity-70">{data.method}. {data.note}</p>
    <div className="relative bg-white dark:bg-zinc-900 rounded-xl p-4 shadow h-[520px] overflow-hidden">
      <div className="absolute inset-4 border rounded">
        <div className="absolute top-1/2 left-0 right-0 h-px bg-zinc-200 dark:bg-zinc-700"></div>
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-zinc-200 dark:bg-zinc-700"></div>
        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] opacity-60">Early braker</span>
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] opacity-60">Late braker</span>
        <span className="absolute top-2 left-1/2 -translate-x-1/2 text-[10px] opacity-60">Aggressive throttle</span>
        {data.points.map((p:any)=> <div key={p.code} title={`${p.code} ${p.cluster}`} className="absolute -translate-x-1/2 -translate-y-1/2 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-red-600 text-white" style={{left:`${(p.x+1)*50}%`, top:`${(1-(p.y+1)/2)*100}%`}}>{p.code}</div>)}
      </div>
    </div>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">{data.points.map((p:any)=><div key={p.code} className="rounded p-2 bg-zinc-100 dark:bg-zinc-800"><b>{p.code}</b> {p.cluster} <span className="opacity-60">{p.team}</span></div>)}</div>
    <div className="text-xs opacity-60">Axes: X {data.axes.x} · Y {data.axes.y} · Source: {data.source}</div>
  </div>
}
