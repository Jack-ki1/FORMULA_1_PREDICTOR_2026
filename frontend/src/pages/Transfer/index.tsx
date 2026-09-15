import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
export function TransferPage(){
  const [opts,setOpts]=useState<any>(null)
  const [drv,setDrv]=useState('VER'), [team,setTeam]=useState('ferrari'), [res,setRes]=useState<any>(null)
  useEffect(()=>{ ext.transferOpts().then(setOpts).catch(console.error)},[])
  const go=()=> ext.transfer({driver:drv, target_team:team}).then(setRes).catch(e=>alert(e.message))
  if(!opts) return <div className="p-8">Loading…</div>
  return <div className="p-6 max-w-4xl mx-auto space-y-4">
    <h1 className="text-2xl font-bold">Silly-Season Transfer Simulator</h1>
    <p className="text-sm opacity-70">Drag a driver into a different team — Elo-based projected shift quantifies “what if Verstappen at Ferrari”.</p>
    <div className="flex gap-2 flex-wrap">
      <select value={drv} onChange={e=>setDrv(e.target.value)} className="border rounded px-2 py-1">{opts.drivers.map((d:any)=><option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}</select>
      <span className="self-center">→</span>
      <select value={team} onChange={e=>setTeam(e.target.value)} className="border rounded px-2 py-1">{opts.teams.map((t:any)=><option key={t.id} value={t.id}>{t.name}</option>)}</select>
      <button onClick={go} className="px-4 py-1.5 bg-red-600 text-white rounded">Simulate</button>
    </div>
    {res && <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow space-y-2">
      <div className="text-lg font-bold">{res.verdict}</div>
      <div className="grid grid-cols-2 gap-3 text-sm"><div>Win before: {(res.win_prob_before*100).toFixed(1)}%</div><div>Win after: {(res.win_prob_after*100).toFixed(1)}%</div><div className="col-span-2 font-mono">Δ {res.win_delta_pp>0?'+':''}{res.win_delta_pp}pp · car delta {res.delta_strength}</div></div>
      <div className="text-xs opacity-60">New teammates: {res.teammate_comparison.map((t:any)=>t.code).join(', ')}</div>
    </div>}
  </div>
}
