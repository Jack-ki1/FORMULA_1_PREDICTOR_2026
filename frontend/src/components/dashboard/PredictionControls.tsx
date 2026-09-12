import { useDashboardStore } from '../../stores/dashboardStore'
import { usePrediction } from '../../hooks/usePrediction'
import { useState } from 'react'
export function PredictionControls({onResult}:{onResult:(r:any)=>void}){
  const draft=useDashboardStore(s=>s.draft) as any
  const session=useDashboardStore(s=>s.session) as any
  const subSession=useDashboardStore(s=>s.subSession) as any
  const manualGrid=useDashboardStore(s=>s.manualGrid) as any
  const aiMode=useDashboardStore(s=>s.aiMode) as any
  const aiModel=useDashboardStore(s=>s.aiModel) as any
  const aiWeight=useDashboardStore(s=>s.aiWeight) as any
  const aiTemp=useDashboardStore(s=>s.aiTemperature) as any
  const setGrid=useDashboardStore(s=>s.setGridPositions) as any
  const mut=usePrediction()
  const [aiKey, setAiKey]=useState('')
  const handle = async ()=>{
    if(!draft.raceId) return alert('Select a race')
    const payload:any={
      race_id:draft.raceId, session_type:session, sub_session:subSession, weather:draft.weather,
      simulation_count:draft.simCount, feature_weights:{chaos_level:50},
      grid_positions: manualGrid||undefined,
      ai_mode:aiMode, ai_model:aiModel, ai_api_key:aiKey, ai_weight:aiWeight/100, ai_temperature:aiTemp
    }
    try{
      // For race, first simulate grid if no manual
      let grid = manualGrid
      let res:any
      if(session==='race' && !manualGrid){
        const q = await mut.mutateAsync({...payload, session_type:'qualifying', sub_session:'q3'})
        const q3 = q.predictions?.q3
        const simGrid:any={}
        if(q3?.predictions) q3.predictions.forEach((p:any,i:number)=> simGrid[p.driver_code]=i+1)
        grid = simGrid
        setGrid(simGrid, Object.keys(simGrid).length?'simulated':null)
      }
      res = await mut.mutateAsync({...payload, grid_positions: grid})
      if(session==='race' && !manualGrid && grid) res.grid_positions=grid
      onResult(res)
    }catch(e:any){ alert(e.message)}
  }
  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="f1-display font-bold">Run Prediction</div>
      <input placeholder="AI API key (optional)" value={aiKey} onChange={e=> setAiKey(e.target.value)} className="f1-input" />
      <button onClick={handle} disabled={mut.isPending || !draft.raceId} className="btn-primary disabled:opacity-50">
        {mut.isPending?'Running…':'Run Prediction'}
      </button>
      {mut.isPending && <div className="fs-11 text-sub">Processing {draft.simCount.toLocaleString()} simulations with {aiMode==='ai'?'AI enhancement':'ML model'}…</div>}
    </div>
  )
}
