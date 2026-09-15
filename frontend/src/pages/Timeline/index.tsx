import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
import { F1Chart } from '../../components/charts/F1Chart'
export function TimelinePage(){
  const [raceId,setRaceId]=useState('au')
  const [data,setData]=useState<any>(null)
  useEffect(()=>{ ext.timeline(raceId).then(setData).catch(console.error)},[raceId])
  if(!data) return <div className="p-8">Loading timeline…</div>
  const labels=data.stages
  const top = ['VER','HAM','LEC','NOR'].filter(c=> data.timeline[0].probs[c]!=null)
  const datasets = top.map((code,i)=>{
    const col=['#E10600','#00D2BE','#1E41FF','#FF8700'][i]
    return { label: code, data: data.timeline.map((t:any)=> (t.probs[code]||0)*100), borderColor: col, backgroundColor: col+'33', tension:0.4 }
  })
  return <div className="p-6 max-w-6xl mx-auto space-y-4">
    <h1 className="text-2xl font-bold">Probability Timeline — FP1 → Chequered</h1>
    <p className="text-sm opacity-70">Not a point estimate — a story. Animated line shows how win% moves from practice to flag.</p>
    <div className="flex gap-2"><input value={raceId} onChange={e=>setRaceId(e.target.value)} className="border rounded px-2 py-1 w-24" placeholder="race" /><span className="text-xs opacity-60">e.g. au, mc, sg</span></div>
    <div className="bg-white dark:bg-zinc-900 rounded-xl p-4 shadow"><F1Chart type="line" data={{labels, datasets}} options={{responsive:true, plugins:{legend:{position:'bottom'}}, scales:{y:{min:0,max:60,title:{display:true,text:'Win %'}}}}} /></div>
    <div className="text-xs opacity-60">{data.note}</div>
  </div>
}
