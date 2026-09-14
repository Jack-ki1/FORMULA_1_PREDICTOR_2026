import { useState } from 'react'
import { api } from '../../api/client'
export function AIChatPanel({ apiKey, model, temp }: { apiKey:string; model:string; temp:number }) {
  const [q,setQ]=useState('')
  const [msgs,setMsgs]=useState<{role:string;text:string}[]>([])
  const send=async()=>{
    if(!q.trim()) return
    const user=q; setMsgs(m=>[...m,{role:'user',text:user}]); setQ('')
    try{ const r:any=await api.post('/api/v1/ai/chat',{message:user, model, api_key:apiKey, temperature:temp}); setMsgs(m=>[...m,{role:'ai',text:r.response}]) }catch(e:any){ setMsgs(m=>[...m,{role:'ai',text:`Error: ${e.message}`}])}
  }
  return (<div className="space-y-2"><div className="space-y-1 max-h-64 overflow-auto">{msgs.map((m,i)=><div key={i} className={m.role==='user'?'text-right':''}><span className="fs-11 card p-2 inline-block">{m.text}</span></div>)}</div><div className="flex gap-2"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Ask AI..." className="f1-input flex-1" onKeyDown={e=>e.key==='Enter'&&send()} /><button onClick={send} className="px-3 py-1.5 bg-red text-white rounded">Send</button></div></div>)
}
