import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAccuracy, fetchWeights, updateWeights, fetchTargets } from '../../api/analytics'
import { useState, useEffect } from 'react'
export function AnalyticsPage(){
  const {data:acc}=useQuery({queryKey:['analytics','accuracy'], queryFn: fetchAccuracy})
  const {data:weights}=useQuery({queryKey:['analytics','weights'], queryFn: fetchWeights})
  const {data:targets}=useQuery({queryKey:['analytics','targets'], queryFn: fetchTargets})
  const qc=useQueryClient()
  const mut=useMutation({mutationFn:updateWeights, onSuccess:()=> qc.invalidateQueries({queryKey:['analytics','weights']})})
  const [local,setLocal]=useState<any>({})
  useEffect(()=>{ if(weights) setLocal(weights)},[weights])
  return (
    <div className="px-4 sm:px-8 py-6 space-y-4">
      <h2 className="f1-display text-xl font-bold">Analytics & Settings</h2>
      <div className="card p-4">
        <div className="f1-display font-bold mb-2">Model Accuracy</div>
        <div className="grid sm:grid-cols-2 gap-3">{Object.entries((acc?.target_accuracies||acc||{}) as any).map(([k,v]:any)=><div key={k} className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold uppercase">{k}</div><div className="f1-mono text-sm">model {(v.model_accuracy*100).toFixed(1)}% · baseline {(v.baseline_accuracy*100).toFixed(1)}%</div></div>)}</div>
      </div>
      <div className="card p-4">
        <div className="f1-display font-bold mb-2">Feature Weights</div>
        {Object.entries(local||{}).slice(0,5).map(([k,v]:any)=>{
          const val = typeof v==='object'? v.default ?? v.value ?? 50 : v
          return <div key={k} className="flex items-center gap-3 py-2"><span className="fs-11 w-40 uppercase font-semibold">{k}</span><input type="range" min={0} max={100} value={val} onChange={e=> setLocal({...local, [k]: parseInt(e.target.value)})} className="f1-range flex-1"/><span className="f1-mono w-8 text-sm">{val}</span></div>
        })}
        <button onClick={()=> mut.mutate(local)} disabled={mut.isPending} className="btn-primary mt-3">Save Weights (POST /api/v1/analytics/feature-weights)</button>
      </div>
      <div className="card p-4">
        <div className="f1-display font-bold mb-2">Targets</div>
        <div className="flex flex-wrap gap-2">{(targets||[]).map((t:any)=><span key={t.id||t.label} className="badge-purple">{t.label||t.id}</span>)}</div>
      </div>
    </div>
  )
}
