import { useEffect, useState } from 'react'
import { ext } from '../../api/extended'
import { F1Chart } from '../../components/charts/F1Chart'

export function LiveWinProbPage(){
  const [raceId]=useState('au')
  const [data,setData]=useState<any>(null)
  const [live,setLive]=useState<any>(null)
  useEffect(()=>{ ext.winProb(raceId).then(setData).catch(console.error) },[raceId])
  useEffect(()=>{
    const url = ext.winProbStream('latest', raceId)
    const es = new EventSource(url)
    es.onmessage = e=> { try{ setLive(JSON.parse(e.data)) }catch{} }
    es.onerror=()=> es.close()
    return ()=> es.close()
  },[raceId])
  if(!data) return <div className="p-8">Loading live win prob…</div>
  const labels = data.points.map((p:any)=>`Lap ${p.lap}`)
  const topCodes = [...new Set(data.points.flatMap((p:any)=>p.top3.map((t:any)=>t.code)))].slice(0,4) as string[]
  const datasets = topCodes.map((code,i)=>{
    const colors=['#E10600','#00D2BE','#1E41FF','#FF8700']
    return { label: code, data: data.points.map((p:any)=> (p.probs[code]||0)*100), borderColor: colors[i%4], backgroundColor: colors[i%4]+'33', tension:0.35, fill:false }
  })
  return <div className="p-6 max-w-6xl mx-auto space-y-6">
    <h1 className="text-2xl font-bold">Live Win-Probability — baseball-style for F1</h1>
    <p className="text-sm opacity-70">SSE re-sims on every gap/pit/SC event. Monte Carlo re-runs in ms. {live?`Live: ${live.leader} ${ (live.probabilities?.[live.leader]?.win*100||0).toFixed(1)}%`:'Connecting…'}</p>
    <div className="bg-white dark:bg-zinc-900 rounded-xl p-4 shadow"><F1Chart type="line" data={{labels, datasets}} options={{responsive:true, plugins:{legend:{position:'bottom'}}, scales:{y:{min:0,max:100,title:{display:true,text:'Win %'}}}}} /></div>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{data.points.slice(-1)[0]?.top3.map((t:any)=><div key={t.code} className="rounded-lg p-3 bg-zinc-100 dark:bg-zinc-800"><div className="font-mono font-bold">{t.code}</div><div className="text-2xl">{(t.p*100).toFixed(1)}%</div></div>)}</div>
  </div>
}
