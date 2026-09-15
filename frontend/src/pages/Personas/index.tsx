import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
export function PersonasPage(){
  const [list,setList]=useState<any[]>([]); const [team,setTeam]=useState('mclaren'); const [msg,setMsg]=useState('Should we pit now under VSC?'); const [res,setRes]=useState<any>(null)
  useEffect(()=>{ ext.personas().then(r=> setList(r.personas)).catch(console.error)},[])
  const ask=()=> ext.personaChat(team,{message:msg, race_id:'au'}).then(setRes).catch(e=>alert(e.message))
  return <div className="p-6 max-w-4xl mx-auto space-y-4">
    <h1 className="text-2xl font-bold">Per-Team Strategist Personas</h1>
    <p className="text-sm opacity-70">Ask the McLaren strategist vs the Williams strategist — genuinely different tones and priorities (title fight vs building).</p>
    <div className="flex flex-wrap gap-2">{list.map((p:any)=><button key={p.team_id} onClick={()=>setTeam(p.team_id)} className={`px-3 py-1 rounded-full text-xs ${team===p.team_id?'bg-red-600 text-white':'bg-zinc-200 dark:bg-zinc-700'}`}>{p.name}</button>)}</div>
    <div className="flex gap-2"><input value={msg} onChange={e=>setMsg(e.target.value)} className="flex-1 border rounded px-3 py-2" placeholder="Ask the strategist…"/><button onClick={ask} className="px-4 py-2 bg-zinc-900 text-white rounded">Ask</button></div>
    {res && <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow"><div className="text-xs opacity-60">{res.persona} · {res.team_win_mass? (res.team_win_mass*100).toFixed(1)+'% win mass':''} · {res.provider}</div><div className="mt-2">{res.response}</div><div className="text-xs mt-2 italic opacity-60">Tone: {res.tone}</div></div>}
  </div>
}
