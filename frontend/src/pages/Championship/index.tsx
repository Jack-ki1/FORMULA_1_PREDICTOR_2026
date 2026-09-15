import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
export function ChampionshipPage(){
  const [data,setData]=useState<any>(null)
  const [noDnf,setNoDnf]=useState(true)
  useEffect(()=>{ ext.counterfactual(noDnf).then(setData).catch(console.error)},[noDnf])
  if(!data) return <div className="p-8">Simulating counterfactual season…</div>
  return <div className="p-6 max-w-5xl mx-auto space-y-4">
    <h1 className="text-2xl font-bold">Counterfactual Championship — pure pace</h1>
    <p className="text-sm opacity-70">Rerun the season with DNFs/red-flags removed. Who *should* have won on pace? {data.note}</p>
    <label className="flex gap-2 items-center"><input type="checkbox" checked={noDnf} onChange={e=>setNoDnf(e.target.checked)}/> Remove DNFs</label>
    <div className="rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow">
      <table className="w-full text-sm"><thead className="bg-zinc-100 dark:bg-zinc-800"><tr><th className="p-2 text-left">#</th><th className="p-2 text-left">Driver</th><th className="p-2 text-right">Points</th></tr></thead>
      <tbody>{data.standings.slice(0,12).map((r:any)=><tr key={r.code} className="border-t"><td className="p-2">{r.pos}</td><td className="p-2 font-mono font-bold">{r.code}</td><td className="p-2 text-right">{r.points}</td></tr>)}</tbody></table>
    </div>
    <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow"><h3 className="font-bold">Biggest movers vs strength</h3>{data.biggest_movers_vs_strength.map((m:any)=><div key={m.code} className="flex justify-between text-sm"><span>{m.code}</span><span>{m.real_rank} → {m.cf_rank} ({m.delta>0?'+':''}{m.delta})</span></div>)}</div>
  </div>
}
