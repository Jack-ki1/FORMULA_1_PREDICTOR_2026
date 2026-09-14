export function SessionCards({ sessions, active, onSelect }: any) {
  return <div className="flex gap-2">{(sessions||['FP1','FP2','Quali','Race']).map((s:string)=><button key={s} onClick={()=>onSelect(s)} className={`px-3 py-2 rounded card ${active===s?'ring-2 ring-red':''}`}>{s}</button>)}</div>
}
