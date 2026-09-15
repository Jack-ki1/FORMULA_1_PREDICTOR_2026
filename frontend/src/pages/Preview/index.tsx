import { useEffect,useState } from 'react'
import { ext } from '../../api/extended'
export function PreviewPage(){
  const [raceId,setRaceId]=useState('au'); const [data,setData]=useState<any>(null)
  useEffect(()=>{ ext.preview(raceId).then(setData).catch(e=> setData({error:String(e)}))},[raceId])
  if(!data) return <div className="p-8">Generating preview…</div>
  if(data.error) return <div className="p-8 text-red-600">{data.error}</div>
  return <div className="p-6 max-w-3xl mx-auto space-y-4">
    <h1 className="text-2xl font-bold">Auto-Generated Race-Week Preview</h1>
    <div className="flex gap-2"><input value={raceId} onChange={e=>setRaceId(e.target.value)} className="border rounded px-2 py-1 w-24"/><button onClick={()=> ext.preview(raceId).then(setData)} className="px-3 py-1 bg-zinc-900 text-white rounded">Regenerate</button></div>
    <div className="rounded-xl p-6 bg-white dark:bg-zinc-900 shadow prose dark:prose-invert max-w-none whitespace-pre-wrap text-sm leading-relaxed">{data.article_markdown}</div>
    <div className="flex gap-2 text-xs">Top3: {data.top3?.map((t:any)=>`${t.code} ${(t.win*100).toFixed(1)}%`).join(' · ')} — Wet fave: {data.wet_fave}</div>
    <div className="text-xs opacity-60">{data.disclaimer}</div>
  </div>
}
