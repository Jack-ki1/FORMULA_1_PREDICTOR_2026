import { useState } from 'react'
import { useDashboardStore } from '../../stores/dashboardStore'
import { api } from '../../api/client'
export function AISidebar(){
  const aiMode=useDashboardStore(s=>s.aiMode) as any
  const setAI=useDashboardStore(s=>s.setAI) as any
  const [open,setOpen]=useState(false)
  const [model,setModel]=useState(useDashboardStore.getState().aiModel)
  const [weight,setWeight]=useState(useDashboardStore.getState().aiWeight)
  const [temp,setTemp]=useState(useDashboardStore.getState().aiTemperature)
  const [apiKey,setApiKey]=useState('')
  const [chat,setChat]=useState('')
  const [messages,setMessages]=useState<{role:string;text:string}[]>([])
  const [tab,setTab]=useState<'settings'|'chat'>('settings')
  const sendChat=async()=>{
    if(!chat.trim()) return
    if(!apiKey) return alert('Enter API key in Settings tab first')
    const user=chat; setMessages(m=>[...m,{role:'user',text:user}]); setChat('')
    try{
      const res:any=await api.post('/api/v1/ai/chat',{message:user, model, api_key:apiKey, temperature:temp})
      setMessages(m=>[...m,{role:'ai',text:res.response}])
    }catch(e:any){ setMessages(m=>[...m,{role:'ai',text:`Error: ${e.message}`}])}
  }
  return (
    <>
      <button onClick={()=>setOpen(v=>!v)} className="ai-sidebar-trigger" style={{display:'flex'}}>🤖</button>
      <div className={`ai-sidebar ${open?'is-open':''}`}>
        <div className="ai-sidebar-content">
          <div className="ai-sidebar-header">
            <div className="ai-sidebar-title"><span className="ai-sidebar-icon">🤖</span> AI Assistant</div>
            <button onClick={()=>setOpen(false)} className="ai-sidebar-close">×</button>
          </div>
          <div className="ai-sidebar-body">
            <div className="ai-mode-tabs">
              <button onClick={()=>setTab('settings')} className={`ai-mode-tab ${tab==='settings'?'active':''}`}>Settings</button>
              <button onClick={()=>setTab('chat')} className={`ai-mode-tab ${tab==='chat'?'active':''}`}>Chat</button>
            </div>
            {tab==='settings'? <>
              <div className="ai-sidebar-section">
                <div className="ai-sidebar-section-title">Mode</div>
                <div className="ai-sidebar-options">
                  <button onClick={()=>setAI({aiMode:'normal'})} className={`ai-sidebar-option ${aiMode==='normal'?'active':''}`}><div>⚡ Normal Mode — traditional ML</div></button>
                  <button onClick={()=>setAI({aiMode:'ai'})} className={`ai-sidebar-option ${aiMode==='ai'?'active':''}`}><div>🤖 AI Mode — model + LLM</div></button>
                </div>
              </div>
              <div className="ai-sidebar-model-details">
                <div className="ai-model-details-title">Model</div>
                <select value={model} onChange={e=>{setModel(e.target.value); setAI({aiModel:e.target.value})}} className="ai-select">
                  <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="custom">Custom</option>
                </select>
                <div className="ai-sidebar-detail mt-3">
                  <label className="ai-detail-label">API Key (not stored)</label>
                  <input value={apiKey} onChange={e=>setApiKey(e.target.value)} type="password" placeholder="sk-..." className="f1-input" />
                </div>
                <div className="ai-sidebar-detail">
                  <label className="ai-detail-label">AI Weight {weight}%</label>
                  <input type="range" min={0} max={100} value={weight} onChange={e=>{setWeight(parseInt(e.target.value)); setAI({aiWeight:parseInt(e.target.value)})}} className="ai-slider" />
                </div>
                <div className="ai-sidebar-detail">
                  <label className="ai-detail-label">Temperature {temp.toFixed(1)}</label>
                  <input type="range" min={0} max={100} value={temp*100} onChange={e=>{const v=parseInt(e.target.value)/100; setTemp(v); setAI({aiTemperature:v})}} className="ai-slider" />
                </div>
              </div>
            </>: <>
              <div className="ai-chat-container">
                <div className="ai-chat-messages" style={{maxHeight:'320px',overflowY:'auto'}}>
                  {messages.map((m,i)=><div key={i} className={`ai-chat-message ai-chat-message-${m.role}`}>{m.text}</div>)}
                </div>
                <div className="ai-chat-input-area">
                  <input value={chat} onChange={e=>setChat(e.target.value)} onKeyDown={e=>e.key==='Enter'&&sendChat()} placeholder="Ask about F1 strategy…" className="ai-chat-input" />
                  <button onClick={sendChat} className="ai-chat-send">Send</button>
                </div>
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
