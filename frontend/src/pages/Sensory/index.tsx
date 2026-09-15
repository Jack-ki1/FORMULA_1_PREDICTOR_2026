import { useEffect,useState, useRef } from 'react'
import { ext } from '../../api/extended'
export function SensoryPage(){
  const [raceId,setRaceId]=useState('au'); const [sono,setSono]=useState<any>(null); const [graph,setGraph]=useState<any>(null); const audioRef=useRef<AudioContext|null>(null)
  useEffect(()=>{ ext.sonify(raceId).then(setSono).catch(console.error); ext.rivalry().then(setGraph).catch(console.error)},[raceId])
  const play=()=>{
    if(!sono) return
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    audioRef.current=ctx
    sono.tracks.slice(0,4).forEach((tr:any,i:number)=>{
      const o=ctx.createOscillator(), g=ctx.createGain()
      o.type= tr.instrument as OscillatorType; o.frequency.value= tr.base_freq_hz
      g.gain.value=0.08; o.connect(g).connect(ctx.destination); o.start(ctx.currentTime + i*0.15); o.stop(ctx.currentTime+3)
    })
  }
  return <div className="p-6 max-w-6xl mx-auto space-y-6">
    <h1 className="text-2xl font-bold">Sensory — Sonification · Rivalry Graph</h1>
    <div className="flex gap-2"><input value={raceId} onChange={e=>setRaceId(e.target.value)} className="border rounded px-2 py-1 w-24"/><button onClick={play} className="px-4 py-1.5 bg-violet-600 text-white rounded">▶ Play gaps as tones</button></div>
    {sono && <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow">
      <h3 className="font-bold">Sonification — gap → frequency, degradation → filter</h3>
      <p className="text-xs opacity-60">{sono.note}</p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-3 text-xs">{sono.tracks.map((t:any)=><div key={t.code} className="rounded p-2 bg-zinc-100 dark:bg-zinc-800"><b>{t.code}</b> gap {t.gap_s}s · {t.base_freq_hz}Hz · {t.instrument}</div>)}</div>
      <pre className="mt-3 text-[10px] bg-zinc-950 text-emerald-400 p-2 rounded overflow-auto">{sono.web_audio_snippet}</pre>
    </div>}
    {graph && <div className="rounded-xl p-4 bg-white dark:bg-zinc-900 shadow">
      <h3 className="font-bold">Rivalry Network — Elo force graph</h3>
      <p className="text-xs opacity-60">{graph.note}</p>
      <svg viewBox="0 0 600 380" className="w-full h-[380px] mt-3 bg-zinc-50 dark:bg-zinc-950 rounded">
        {graph.nodes.slice(0,12).map((n:any,i:number)=>{
          const angle=(i/graph.nodes.slice(0,12).length)*Math.PI*2, r=120, cx=300+Math.cos(angle)*r, cy=190+Math.sin(angle)*r
          return <g key={n.id}><circle cx={cx} cy={cy} r={8+ n.elo/300} fill={n.color} stroke="#fff" strokeWidth={2}/><text x={cx} y={cy+22} textAnchor="middle" fontSize="9" fill="currentColor">{n.id}</text></g>
        })}
        {graph.links.slice(0,18).map((l:any,i:number)=>{
          const a= graph.nodes.find((n:any)=>n.id===l.source), b= graph.nodes.find((n:any)=>n.id===l.target)
          if(!a||!b) return null
          const ai= graph.nodes.indexOf(a)%12, bi= graph.nodes.indexOf(b)%12
          const ar=(ai/12)*Math.PI*2, br=(bi/12)*Math.PI*2, r=120
          const x1=300+Math.cos(ar)*r, y1=190+Math.sin(ar)*r, x2=300+Math.cos(br)*r, y2=190+Math.sin(br)*r
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={l.dominance>0.7?'#E10600':'#9CA3AF'} strokeWidth={Math.max(0.5,l.battles/3)} opacity={0.6}/>
        })}
      </svg>
      <div className="text-xs opacity-60 mt-2">Edge thickness = battles, color = dominance · {graph.links.length} edges</div>
    </div>}
  </div>
}
