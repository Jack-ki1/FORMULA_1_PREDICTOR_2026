import { useDashboardStore } from '../../stores/dashboardStore'
const SESSIONS=[{id:'practice',label:'Friday Practice',desc:'FP1 · FP2 · FP3'},{id:'qualifying',label:'Saturday Qualifying',desc:'Q1/Q2/Q3'},{id:'race',label:'Sunday Grand Prix',desc:'Full race prediction'}]
export function SessionSelector(){
  const session=useDashboardStore(s=>s.session) as any
  const setSession=useDashboardStore(s=>s.setSession) as any
  const setTarget=useDashboardStore(s=>s.setTarget) as any
  const setSub=useDashboardStore(s=>s.setSubSession) as any
  return (
    <div id="session-cards" className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {SESSIONS.map(s=>{
        const active=session===s.id
        return <button key={s.id} onClick={()=>{setSession(s.id); if(s.id==='qualifying'){setTarget('qualifying_q3');setSub('Q1')} else if(s.id==='practice'){setTarget('practice_pace');setSub('FP1')} else {setTarget('podium');setSub('Race')}}} className={`session-card ${active?'is-active':''}`}>
          <div className="f1-display font-bold text-sm">{s.label}</div>
          <div className="fs-11 mt-0.5 session-sub text-sub">{s.desc}</div>
        </button>
      })}
    </div>
  )
}
