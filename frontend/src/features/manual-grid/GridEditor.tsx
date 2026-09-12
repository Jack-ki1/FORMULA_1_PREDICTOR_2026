import { useState } from 'react'
import { useDrivers } from '../../hooks/useH2H'
export function GridEditor({value,onChange}:{value:Record<string,number>|null;onChange:(g:Record<string,number>)=>void}){
  const {data:drivers}=useDrivers()
  const codes = drivers?.map((d:any)=> d.code) || []
  const [grid,setGrid]=useState<Record<string,number>>(value||{})
  const setPos=(code:string, pos:string)=>{
    const n=parseInt(pos)||0
    const next={...grid, [code]: n}
    setGrid(next); onChange(next)
  }
  if(!codes.length) return <div className="card p-4 text-sub">Loading drivers…</div>
  return (
    <div className="card p-4">
      <div className="f1-display font-bold mb-2">Manual Grid Editor</div>
      <div className="fs-11 text-sub mb-3">Assign each driver's starting position P1–P22. Drag-less select version preserved for parity.</div>
      <div className="grid-editor-list space-y-1">
        {codes.slice(0,22).map((code:string)=>
          <div key={code} className="grid-row">
            <span className="f1-mono fs-11 font-bold w-8">{grid[code]||'-'}</span>
            <span className="fs-11 font-semibold flex-1">{code}</span>
            <select value={grid[code]||''} onChange={e=> setPos(code, e.target.value)} className="f1-select" style={{maxWidth:'120px'}}>
              <option value="">—</option>
              {Array.from({length:22},(_,i)=> i+1).map(n=><option key={n} value={n}>P{n}</option>)}
            </select>
          </div>
        )}
      </div>
    </div>
  )
}
