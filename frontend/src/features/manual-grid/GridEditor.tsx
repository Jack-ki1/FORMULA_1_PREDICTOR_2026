import { useEffect, useState } from 'react'
import { useDrivers } from '../../hooks/useH2H'
import { api } from '../../api/client'

export function GridEditor({value,onChange, raceId}:{value:Record<string,number>|null;onChange:(g:Record<string,number>)=>void; raceId?:string}){
  const {data:drivers}=useDrivers()
  const codes = drivers?.map((d:any)=> d.code) || []
  const [grid,setGrid]=useState<Record<string,number>>(value||{})
  const [source,setSource]=useState<string>('manual')
  const [loading,setLoading]=useState(false)
  const [official, setOfficial]=useState<Record<string,number>|null>(null)

  // Try official grid from F1 when race changes
  useEffect(()=>{
    if (!raceId) return
    let cancelled=false
    setLoading(true)
    api.get<any>(`/api/v1/grid/${raceId}`).then(res=>{
      if (cancelled) return
      const g = res.grid as Record<string,number>
      if (g && Object.keys(g).length) {
        setOfficial(g)
        setSource(res.source || 'simulated')
        // If user hasn't set manual yet, auto-fill with official and notify parent
        if (!value || !Object.keys(value).length) {
          setGrid(g)
          onChange(g)
        }
      } else {
        setSource('manual')
      }
    }).catch(()=> setSource('manual')).finally(()=> setLoading(false))
    return ()=> { cancelled=true }
  }, [raceId])

  // sync from parent
  useEffect(()=>{ if(value) setGrid(value)},[value])

  const setPos=(code:string, pos:string)=>{
    const n=parseInt(pos)||0
    const next={...grid, [code]: n}
    // remove if empty
    if (!pos) delete (next as any)[code]
    setGrid(next); onChange(next)
  }

  const useOfficial = ()=> {
    if (official) { setGrid(official); onChange(official) }
  }
  const clear = ()=> { setGrid({}); onChange({}) }

  if(!codes.length) return <div className="card p-4 text-sub">Loading drivers…</div>
  const isOfficial = source==='live'
  return (
    <div className="card p-4">
      <div className="f1-display font-bold mb-2 flex items-center gap-2">Manual Grid Editor <span className={`px-2 py-0.5 rounded-full text-white fs-11 text-[10px] ${isOfficial?'bg-green-600':'bg-zinc-400'}`}>{loading?'loading…': isOfficial?'Official F1 (Jolpica)': source==='simulated'?'Simulated Q1-Q3':'Manual fallback'}</span></div>
      <div className="fs-11 text-sub mb-2">
        Tries official F1 qualifying via <code className="f1-mono">GET /api/v1/grid/{raceId||':raceId'}</code> first — manual is fallback when official not yet available (2026 future). {official? 'Tap “Use official” to restore.': ''}
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        <button onClick={useOfficial} disabled={!official} className="btn-ghost text-xs disabled:opacity-40">Use official grid</button>
        <button onClick={clear} className="btn-ghost text-xs">Clear (auto)</button>
        <span className="fs-11 text-sub self-center">P1–P22 — duplicates highlighted</span>
      </div>
      {/* Duplicate detection */}
      {(()=>{
        const counts: Record<number, number> = {}
        Object.values(grid).forEach(v=> { if(v) counts[v]=(counts[v]||0)+1 })
        const dupes = Object.entries(counts).filter(([,c])=> c>1).map(([k])=>k)
        return dupes.length? <div className="fs-11 text-amber-600 mb-2">Duplicate P{dupes.join(', P')} — fix to run</div> : null
      })()}
      <div className="grid-editor-list space-y-1 max-h-[420px] overflow-auto pr-1">
        {codes.slice(0,23).map((code:string)=>{
          const val = grid[code] || ''
          const isDupe = val && Object.values(grid).filter(v=> v===val).length>1
          return (
            <div key={code} className={`grid-row ${isDupe?'is-duplicate':''}`}>
              <span className="f1-mono fs-11 font-bold w-8">{val || '-'}</span>
              <span className="fs-11 font-semibold flex-1">{code}</span>
              <select value={val} onChange={e=> setPos(code, e.target.value)} className="f1-select" style={{maxWidth:'120px', borderColor: isDupe? 'var(--amber)': undefined}}>
                <option value="">—</option>
                {Array.from({length:23},(_,i)=> i+1).map(n=><option key={n} value={n}>P{n}</option>)}
              </select>
            </div>
          )
        })}
      </div>
      <div className="fs-11 text-sub mt-2">Official source: <code className="f1-mono">grid_model.get_grid_positions</code> — real Jolpica qualifying → simulated Q1-Q3 (22→16→10) → manual fallback. Tables below appear two per row.</div>
    </div>
  )
}
