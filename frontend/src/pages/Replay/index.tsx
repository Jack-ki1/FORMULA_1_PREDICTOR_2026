import { useState } from 'react'
import { ext } from '../../api/extended'
export function ReplayPage(){
  const [raceId,setRaceId]=useState('au')
  const [lap,setLap]=useState(25)
  const [res,setRes]=useState<any>(null)
  const run=(altered:any)=> ext.branch({race_id:raceId, freeze_lap:lap, altered}).then(setRes).catch(e=> alert(e.message))
  return <div className="p-6 max-w-5xl mx-auto space-y-4">
    <h1 className="text-2xl font-bold">Branch-Point Replay</h1>
    <p className="text-sm opacity-70">Freeze any historical race at lap N, change one variable, re-run Monte Carlo forward. “What if Hamilton pitted one lap earlier?” as a tool.</p>
    <div className="flex flex-wrap gap-2 items-end">
      <label>Race <input value={raceId} onChange={e=>setRaceId(e.target.value)} className="border rounded px-2 py-1 w-20"/></label>
      <label>Lap <input type="number" value={lap} onChange={e=>setLap(parseInt(e.target.value)||25)} className="border rounded px-2 py-1 w-20"/></label>
      <button onClick={()=>run({no_safety_car:true})} className="px-3 py-1.5 bg-zinc-900 text-white rounded">No Safety Car</button>
      <button onClick={()=>run({tire_call:{driver:'HAM', compound:'soft'}})} className="px-3 py-1.5 bg-red-600 text-white rounded">HAM early pit</button>
      <button onClick={()=>run({puncture_driver:'VER'})} className="px-3 py-1.5 bg-zinc-700 text-white rounded">VER puncture</button>
      <button onClick={()=>run({weather:'wet'})} className="px-3 py-1.5 bg-blue-600 text-white rounded">Rain</button>
    </div>
    {res && <div className="grid md:grid-cols-2 gap-4">
      <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow"><h3 className="font-bold">Baseline Top5</h3>{res.baseline_top5.map((r:any)=><div key={r.code} className="flex justify-between"><span>{r.code}</span><span>{(r.win*100).toFixed(1)}%</span></div>)}</div>
      <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow"><h3 className="font-bold">Altered Top5</h3>{res.altered_top5.map((r:any)=><div key={r.code} className="flex justify-between"><span>{r.code}</span><span>{(r.win*100).toFixed(1)}%</span></div>)}</div>
      <div className="md:col-span-2 rounded-xl p-4 bg-amber-50 dark:bg-amber-950">
        <div className="font-semibold">Biggest movers</div>{res.biggest_movers.map((m:any)=><span key={m.code} className="mr-3">{m.code} {m.delta>0?'+':''}{(m.delta*100).toFixed(1)}pp</span>)}
        <div className="text-xs mt-2 opacity-70">{res.explanation?.join(' · ')}</div>
      </div>
    </div>}
  </div>
}
