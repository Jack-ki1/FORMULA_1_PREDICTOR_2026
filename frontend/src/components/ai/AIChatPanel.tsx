import { useState } from 'react'
import { api } from '../../api/client'

export function AIChatPanel({ apiKey, model, temp }: { apiKey:string; model:string; temp:number }) {
  const [q,setQ]=useState('')
  const [msgs,setMsgs]=useState<{role:string;text:string}[]>([])
  const isFree = model.startsWith('puter:')
  const send=async()=>{
    if(!q.trim()) return
    if(!isFree && !apiKey) { setMsgs(m=>[...m,{role:'ai',text:'Enter API key first (or pick a Free puter:* model)'}]); return }
    const user=q; setMsgs(m=>[...m,{role:'user',text:user}]); setQ('')
    try{ 
      let text=''
      if(isFree){
        const puterModel = model.replace('puter:','')
        if(typeof window !== 'undefined' && (window as any).puter?.ai?.chat){
          const resp = await (window as any).puter.ai.chat(user, { model: puterModel })
          text = typeof resp === 'string' ? resp : (resp?.message?.content || resp?.text || JSON.stringify(resp))
        } else {
          // Load Puter if not present
          await new Promise<void>((resolve, reject)=>{
            if(document.querySelector('script[src*="puter"]')) return resolve()
            const s=document.createElement('script'); s.src='https://js.puter.com/v2/'; s.onload=()=> resolve(); s.onerror=()=> reject(new Error('Failed to load Puter.js')); document.head.appendChild(s)
          })
          const resp = await (window as any).puter.ai.chat(user, { model: puterModel })
          text = typeof resp === 'string' ? resp : (resp?.message?.content || resp?.text || JSON.stringify(resp))
        }
      } else {
        const r:any=await api.post('/api/v1/ai/chat',{message:user, model, api_key:apiKey, temperature:temp})
        text = r.response
      }
      setMsgs(m=>[...m,{role:'ai',text}]) 
    }catch(e:any){ setMsgs(m=>[...m,{role:'ai',text:`Error: ${e.message}`}])}
  }
  return (
    <div className="space-y-2">
      <div className="fs-11 text-sub">{isFree ? 'Free via Puter.js — no API key, User-Pays (you pay $0)' : 'Requires API key — session-only, never stored'}</div>
      <div className="space-y-1 max-h-64 overflow-auto">{msgs.map((m,i)=><div key={i} className={m.role==='user'?'text-right':''}><span className="fs-11 card p-2 inline-block max-w-[85%] whitespace-pre-wrap">{m.text}</span></div>)}</div>
      <div className="flex gap-2">
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder={isFree ? `Chat with ${model} (free)…` : 'Ask AI…'} className="f1-input flex-1" onKeyDown={e=>e.key==='Enter'&&send()} />
        <button onClick={send} className="px-3 py-1.5 bg-red text-white rounded">Send</button>
      </div>
    </div>
  )
}
