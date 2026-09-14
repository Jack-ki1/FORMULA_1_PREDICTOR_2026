import { useState, useEffect } from 'react'
import { useDashboardStore } from '../../stores/dashboardStore'
import { api } from '../../api/client'
import { PROVIDERS, MODEL_GROUPS, getProviderForModel } from '../../components/ai/AIModelSelect'

// Declare puter global for Free models
declare global { interface Window { puter: any } }

export function AISidebar(){
  const aiMode=useDashboardStore(s=>s.aiMode) as any
  const setAI=useDashboardStore(s=>s.setAI) as any
  const [open,setOpen]=useState(false)
  const storedModel = useDashboardStore.getState().aiModel as string
  const initialProvider = getProviderForModel(storedModel)
  const [provider, setProvider] = useState<keyof typeof PROVIDERS>(initialProvider)
  const [model,setModel]=useState(storedModel)
  const [weight,setWeight]=useState(useDashboardStore.getState().aiWeight as number)
  const [temp,setTemp]=useState(useDashboardStore.getState().aiTemperature as number)
  const [apiKey,setApiKey]=useState('')
  const [chat,setChat]=useState('')
  const [messages,setMessages]=useState<{role:string;text:string}[]>([])
  const [tab,setTab]=useState<'settings'|'chat'>('settings')

  // When provider changes, auto-switch to first model of that provider
  useEffect(()=>{
    const first = MODEL_GROUPS[provider]?.[0]
    if (first && !MODEL_GROUPS[provider].includes(model)) {
      setModel(first)
      setAI({aiModel:first})
    }
  }, [provider])

  const requiresKey = PROVIDERS[provider].requiresKey
  const isFree = provider === 'free'

  const sendChat=async()=>{
    if(!chat.trim()) return
    if(requiresKey && !apiKey) return alert(`Enter your ${PROVIDERS[provider].label} API key in Settings first — or switch to Free (Puter) for no-key models`)
    const user=chat; setMessages(m=>[...m,{role:'user',text:user}]); setChat('')
    try{
      let responseText = ''
      if(isFree){
        // Puter.js — free, no API key, runs in browser
        const puterModel = model.replace('puter:','')
        if(typeof window !== 'undefined' && (window as any).puter?.ai?.chat){
          const resp = await (window as any).puter.ai.chat(user, { model: puterModel })
          // puter returns string or object
          responseText = typeof resp === 'string' ? resp : (resp?.message?.content || resp?.text || JSON.stringify(resp))
        } else {
          // Fallback: try to load Puter dynamically via CDN if not yet loaded
          await new Promise<void>((resolve, reject)=>{
            if(document.querySelector('script[src*="puter"]')) return resolve()
            const s=document.createElement('script')
            s.src='https://js.puter.com/v2/'
            s.onload=()=> resolve()
            s.onerror=()=> reject(new Error('Failed to load Puter.js'))
            document.head.appendChild(s)
          })
          const resp = await (window as any).puter.ai.chat(user, { model: puterModel })
          responseText = typeof resp === 'string' ? resp : (resp?.message?.content || resp?.text || JSON.stringify(resp))
        }
        if(!responseText) throw new Error('Empty response from Puter')
      } else {
        const res:any=await api.post('/api/v1/ai/chat',{message:user, model, api_key:apiKey, temperature:temp})
        responseText = res.response
      }
      setMessages(m=>[...m,{role:'ai',text: responseText}])
    }catch(e:any){ 
      const msg = e?.message || String(e)
      // If Puter failed (e.g., not signed in), give helpful hint
      if(isFree && msg.includes('puter')){
        setMessages(m=>[...m,{role:'ai',text:`Free model error: ${msg}. Tip: Free Puter models work without an API key — just pick a Free model like puter:gemini-3.8-flash. If it still fails, try signing in at puter.com or switch to Google/OpenAI/Claude with your own key.`}])
      } else {
        setMessages(m=>[...m,{role:'ai',text:`Error: ${msg}`}])
      }
    }
  }

  return (
    <>
      <button onClick={()=>setOpen(v=>!v)} className="ai-sidebar-trigger" style={{display:'flex'}} title={open?'Close AI':'Open AI Assistant'}>🤖</button>
      <div className={`ai-sidebar ${open?'is-open':''}`}>
        <div className="ai-sidebar-content">
          <div className="ai-sidebar-header">
            <div className="ai-sidebar-title"><span className="ai-sidebar-icon">🤖</span> AI Assistant — 4 Providers</div>
            <button onClick={()=>setOpen(false)} className="ai-sidebar-close">×</button>
          </div>
          <div className="ai-sidebar-body">
            <div className="ai-mode-tabs">
              <button onClick={()=>setTab('settings')} className={`ai-mode-tab ${tab==='settings'?'active':''}`}>Settings</button>
              <button onClick={()=>setTab('chat')} className={`ai-mode-tab ${tab==='chat'?'active':''}`}>Chat ({messages.length})</button>
            </div>
            {tab==='settings'? <>
              <div className="ai-sidebar-section">
                <div className="ai-sidebar-section-title">Mode</div>
                <div className="ai-sidebar-options">
                  <button onClick={()=>setAI({aiMode:'normal'})} className={`ai-sidebar-option ${aiMode==='normal'?'active':''}`}><div>⚡ Normal — traditional ML only</div><div className="fs-11 text-sub">Fast, no key, Monte Carlo only</div></button>
                  <button onClick={()=>setAI({aiMode:'ai'})} className={`ai-sidebar-option ${aiMode==='ai'?'active':''}`}><div>🤖 AI-Enhanced — model + LLM</div><div className="fs-11 text-sub">Blends AI adjustments (weight temp) into predictions</div></button>
                </div>
              </div>

              <div className="ai-sidebar-section">
                <div className="ai-sidebar-section-title">Provider — pick one of 4, then a model</div>
                <div className="grid grid-cols-2 gap-2">
                  {(Object.keys(PROVIDERS) as Array<keyof typeof PROVIDERS>).map(p=>(
                    <button key={p} onClick={()=> setProvider(p)} className={`ai-sidebar-option ${provider===p?'active':''}`} style={{ borderColor: provider===p ? PROVIDERS[p].color : undefined }}>
                      <div className="flex items-center gap-2"><span style={{ color: PROVIDERS[p].color }}>{PROVIDERS[p].icon}</span> {PROVIDERS[p].label}</div>
                      <div className="fs-11 text-sub">{PROVIDERS[p].requiresKey ? 'Requires API key' : 'Free — no key'}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="ai-sidebar-model-details">
                <div className="ai-model-details-title">Model — {PROVIDERS[provider].label}</div>
                <select value={model} onChange={e=>{setModel(e.target.value); setAI({aiModel:e.target.value})}} className="ai-select">
                  {MODEL_GROUPS[provider].map(m=> <option key={m} value={m}>{m}</option>)}
                </select>
                <div className="fs-11 text-sub mt-1">
                  {provider==='google' && 'Gemini 3.8 Flash is latest (Sep 2026) — 1M context, $0.75/M input till Dec 31. 3.6 Flash is workhorse.'}
                  {provider==='openai' && 'GPT-6 Astra is flagship, 5.6 Sol/Terra/Luna are 3 tiers. 4o is stable.'}
                  {provider==='claude' && 'Claude Fable 5 is Mythos flagship, Opus 5 is balanced, Haiku is fast.'}
                  {provider==='free' && 'Free via Puter.js — 500+ models, User-Pays (you pay nothing, user covers via Puter account). No key, no server.'}
                </div>

                {requiresKey ? (
                  <div className="ai-sidebar-detail mt-3">
                    <label className="ai-detail-label">{PROVIDERS[provider].keyLabel}</label>
                    <input value={apiKey} onChange={e=>setApiKey(e.target.value)} type="password" placeholder={provider==='google' ? 'AIza...' : provider==='openai' ? 'sk-...' : 'sk-ant-...'} className="f1-input" />
                    <div className="fs-11 text-sub mt-1">Key is session-only, never stored. Insert key → AI works. Get key at {provider==='google' ? 'aistudio.google.com' : provider==='openai' ? 'platform.openai.com' : 'console.anthropic.com'}.</div>
                  </div>
                ) : (
                  <div className="ai-sidebar-detail mt-3 p-3 rounded-lg" style={{ background:'#F3E8FF', border:'1px solid #DDD6FE'}}>
                    <div className="fs-11 font-bold" style={{ color:'#7C3AED'}}>◆ Free — No API key needed</div>
                    <div className="fs-11 text-sub mt-1">Powered by <a href="https://developer.puter.com" target="_blank" rel="noreferrer" className="underline">Puter.js</a> — free, unlimited, 400+ models, User-Pays (user covers via Puter account, you pay $0). Just select a <code>puter:*</code> model and chat — no backend, no key.</div>
                  </div>
                )}

                <div className="ai-sidebar-detail">
                  <label className="ai-detail-label">AI Weight {Math.round(weight*100)}% — how much AI nudges Monte Carlo</label>
                  <input type="range" min={0} max={100} value={Math.round(weight*100)} onChange={e=>{const v=parseInt(e.target.value)/100; setWeight(v); setAI({aiWeight:v})}} className="ai-slider" />
                </div>
                <div className="ai-sidebar-detail">
                  <label className="ai-detail-label">Temperature {temp.toFixed(2)} — creativity</label>
                  <input type="range" min={0} max={100} value={Math.round(temp*100)} onChange={e=>{const v=parseInt(e.target.value)/100; setTemp(v); setAI({aiTemperature:v})}} className="ai-slider" />
                </div>
                <div className="fs-11 text-sub mt-2 p-2 rounded" style={{ background:'#FEF3C7', border:'1px solid #FDE68A'}}>
                  Flow: pick <strong>{PROVIDERS[provider].label}</strong> → pick <strong>{model}</strong> {requiresKey ? '→ insert API key → chat' : '→ chat (no key)'} — AI works.
                </div>
              </div>
            </>: <>
              <div className="ai-chat-container">
                <div className="ai-chat-messages" style={{maxHeight:'320px',overflowY:'auto'}}>
                  {messages.length===0 && <div className="fs-11 text-sub p-2">Ask anything — strategy, 2026 regs, or "{MODEL_GROUPS[provider][0]}" — {isFree ? 'no key needed' : `needs ${PROVIDERS[provider].label} key`}.</div>}
                  {messages.map((m,i)=><div key={i} className={`ai-chat-message ai-chat-message-${m.role}`}>{m.text}</div>)}
                </div>
                <div className="ai-chat-input-area">
                  <input value={chat} onChange={e=>setChat(e.target.value)} onKeyDown={e=>e.key==='Enter'&&sendChat()} placeholder={isFree ? `Chat with ${model} (free, no key)…` : `Ask about F1 — ${model}…`} className="ai-chat-input" />
                  <button onClick={sendChat} className="ai-chat-send">Send</button>
                </div>
                {!isFree && !apiKey && <div className="fs-11 text-sub mt-1">Enter API key in Settings first, or switch to <strong>Free</strong> for no-key models.</div>}
              </div>
            </>}
          </div>
          <div className="ai-sidebar-footer">
            <button onClick={()=>setOpen(false)} className="ai-sidebar-apply">Apply Settings</button>
            <button onClick={()=>{setAI({aiMode:'normal'}); setOpen(false)}} className="ai-sidebar-skip">Use Normal Mode</button>
          </div>
        </div>
      </div>
    </>
  )
}
