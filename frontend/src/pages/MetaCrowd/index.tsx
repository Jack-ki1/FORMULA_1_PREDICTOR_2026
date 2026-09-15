import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
export function MetaCrowdPage(){
  const [raceId,setRaceId]=useState('au'); const [meta,setMeta]=useState<any>(null); const [crowd,setCrowd]=useState<any>(null); const [picks,setPicks]=useState('VER,HAM,LEC')
  useEffect(()=>{ ext.meta(raceId).then(setMeta).catch(console.error); ext.crowd(raceId).then(setCrowd).catch(()=> setCrowd(null))},[raceId])
  const submit=()=> ext.crowdSubmit(raceId, picks.split(',').map(s=>s.trim().toUpperCase())).then(()=> ext.crowd(raceId).then(setCrowd)).catch(e=>alert(e.message))
  return <div className="p-6 max-w-5xl mx-auto space-y-6">
    <h1 className="text-2xl font-bold">Model vs Crowd · Meta-Confidence</h1>
    <div className="flex gap-2"><input value={raceId} onChange={e=>setRaceId(e.target.value)} className="border rounded px-2 py-1 w-24"/><span className="text-xs opacity-60 self-center">Volatility & divergence</span></div>
    {meta && <div className={`rounded-xl p-4 ${meta.volatility>0.55?'bg-amber-100 dark:bg-amber-950':'bg-emerald-50 dark:bg-emerald-950'}`}>
      <div className="font-bold">{meta.circuit} — {meta.verdict}</div>
      <div className="text-sm">Volatility {meta.volatility} · Predictability {meta.predictability} · Brier proxy {meta.brier_proxy}</div>
      <div className="text-xs opacity-70">SC {meta.factors.safety_car} · Rain {meta.factors.rain} · Overtaking {meta.overtaking} — {meta.advice}</div>
    </div>}
    <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow space-y-2">
      <h3 className="font-bold">Crowd podium (submit yours)</h3>
      <div className="flex gap-2"><input value={picks} onChange={e=>setPicks(e.target.value)} className="flex-1 border rounded px-2 py-1 font-mono" placeholder="VER,HAM,LEC"/><button onClick={submit} className="px-3 py-1 bg-red-600 text-white rounded">Submit</button></div>
      {crowd && <div className="grid md:grid-cols-2 gap-4 text-sm">
        <div><div className="font-semibold">Model top3</div>{crowd.model_top3.map((r:any)=><div key={r.code} className="flex justify-between"><span>{r.code}</span><span>{(r.p*100).toFixed(1)}%</span></div>)}</div>
        <div><div className="font-semibold">Crowd top3 ({crowd.crowd_votes} votes)</div>{crowd.crowd_top3.map((r:any)=><div key={r.code} className="flex justify-between"><span>{r.code}</span><span>{(r.p*100).toFixed(1)}%</span></div>)}</div>
        <div className="md:col-span-2"><div className="font-semibold">Biggest divergence</div>{crowd.divergence.map((d:any)=><div key={d.code} className="flex justify-between"><span>{d.code}</span><span className={d.gap>0?'text-emerald-600':'text-red-600'}>{d.gap>0?'+':''}{(d.gap*100).toFixed(1)}pp</span><span className="opacity-60">M {(d.model*100).toFixed(1)}% C {(d.crowd*100).toFixed(1)}%</span></div>)}</div>
      </div>}
    </div>
  </div>
}
