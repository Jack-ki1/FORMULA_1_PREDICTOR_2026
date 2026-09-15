import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
export function CommunityPage(){
  const [raceId,setRaceId]=useState('au'); const [user,setUser]=useState('anon'); const [picks,setPicks]=useState('VER,HAM,LEC'); const [board,setBoard]=useState<any>(null); const [market,setMarket]=useState<any>(null); const [streak,setStreak]=useState<any>(null); const [driver,setDriver]=useState('VER'); const [amt,setAmt]=useState(5)
  const load=()=>{ ext.leaderboard(raceId).then(setBoard).catch(console.error); ext.market(raceId).then(setMarket).catch(console.error); ext.streak().then(setStreak).catch(console.error)}
  useEffect(()=>{ load() },[raceId])
  const submitPick=()=> ext.lbSubmit({user, race_id:raceId, picks: picks.split(',').map(s=>s.trim().toUpperCase())}).then(load).catch(e=>alert(e.message))
  const trade=()=> ext.marketTrade(raceId,{user, driver, amount:amt}).then(setMarket).catch(e=>alert(e.message))
  return <div className="p-6 max-w-6xl mx-auto space-y-6">
    <h1 className="text-2xl font-bold">Humans vs Machine · Market · Streak</h1>
    <div className="flex gap-2 flex-wrap"><input value={raceId} onChange={e=>setRaceId(e.target.value)} className="border rounded px-2 py-1 w-20" placeholder="race"/><input value={user} onChange={e=>setUser(e.target.value)} className="border rounded px-2 py-1 w-28" placeholder="username"/></div>
    {streak && <div className="rounded-xl p-4 bg-zinc-900 text-white flex items-center justify-between"><div><div className="text-xs opacity-60">Model form (last 10)</div><div className="text-lg font-bold">{streak.emoji} {streak.badge} — {streak.verdict} ({streak.wins}W-{streak.losses}L)</div></div><div className="flex gap-1">{streak.last10.map((w:boolean,i:number)=><span key={i} className={`w-3 h-3 rounded-full ${w?'bg-emerald-500':'bg-red-500'}`} title={w?'W':'L'}></span>)}</div></div>}
    <div className="grid md:grid-cols-2 gap-4">
      <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow space-y-2">
        <h3 className="font-bold">Leaderboard — same scoring, humans & model</h3>
        <p className="text-xs opacity-60">If model loses to humans, that's a visible motivator to fix it (Tier 1). Actual top3: {board?.actual_top3?.join(', ')}</p>
        <div className="flex gap-2"><input value={picks} onChange={e=>setPicks(e.target.value)} className="flex-1 border rounded px-2 py-1 font-mono" placeholder="VER,HAM,LEC"/><button onClick={submitPick} className="px-3 py-1 bg-red-600 text-white rounded">Submit</button></div>
        <table className="w-full text-sm"><thead><tr><th className="text-left">#</th><th className="text-left">User</th><th>Score</th><th>Picks</th></tr></thead><tbody>{board?.board?.slice(0,8).map((r:any)=><tr key={r.user+r.score} className={r.type==='model'?'bg-amber-50 dark:bg-amber-950 font-bold':''}><td>{r.pos}</td><td>{r.user}{r.type==='model'?' 🤖':''}</td><td className="text-center">{r.score}</td><td className="font-mono text-xs">{r.picks.join(', ')}</td></tr>)}</tbody></table>
      </div>
      <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow space-y-2">
        <h3 className="font-bold">Synthetic Prediction Market — FAKE currency</h3>
        <p className="text-xs opacity-60">Price discovery = crowd wisdom baseline (most credible validation vs model).</p>
        <div className="max-h-56 overflow-auto text-xs space-y-1">{market && Object.entries(market.prices).sort((a:any,b:any)=>b[1]-a[1]).slice(0,10).map(([code,price]:any)=><div key={code} className="flex justify-between"><span className="font-mono">{code}</span><span>{Number(price).toFixed(1)}¢</span></div>)}</div>
        <div className="flex gap-2"><select value={driver} onChange={e=>setDriver(e.target.value)} className="border rounded px-2 py-1">{market && Object.keys(market.prices).slice(0,12).map(c=><option key={c} value={c}>{c}</option>)}</select><input type="number" value={amt} onChange={e=>setAmt(parseFloat(e.target.value)||1)} className="border rounded px-2 py-1 w-20"/><button onClick={trade} className="px-3 py-1 bg-zinc-900 text-white rounded">Buy</button></div>
      </div>
    </div>
  </div>
}
