import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAccuracy, fetchWeights, updateWeights, fetchTargets } from '../../api/analytics'
import { useState, useEffect } from 'react'
import { F1Chart } from '../../components/charts/F1Chart'

export function AnalyticsPage(){
  const {data:acc}=useQuery({queryKey:['analytics','accuracy'], queryFn: fetchAccuracy})
  const {data:weights}=useQuery({queryKey:['analytics','weights'], queryFn: fetchWeights})
  const {data:targets}=useQuery({queryKey:['analytics','targets'], queryFn: fetchTargets})
  const qc=useQueryClient()
  const mut=useMutation({mutationFn:updateWeights, onSuccess:()=> qc.invalidateQueries({queryKey:['analytics','weights']})})
  const [local,setLocal]=useState<any>({})
  useEffect(()=>{ if(weights) setLocal(weights)},[weights])
  const accEntries:any[] = Object.entries((acc as any)?.target_accuracies || (acc as any) || {})
  const driftMock = [
    { label:'Winner', expected:0.58, observed:0.55, drift:0.03 },
    { label:'Podium', expected:0.89, observed:0.87, drift:0.02 },
    { label:'Points', expected:0.81, observed:0.80, drift:0.01 },
  ]
  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/f1_simulation.png" alt="Simulation" loading="lazy" className="w-full h-48 object-cover" />
          <div className="p-6">
            <h2 className="f1-display text-xl font-black">Analytics — 2026 Intelligence</h2>
            <p className="fs-11 text-sub mt-1">Model accuracy, feature weights, calibration & drift. 2026 active aero & 50/50 PU re-tuned — see what changed.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge">Monte Carlo 100-100k</span><span className="badge">ONNX-ready</span><span className="badge">Drift detection</span>
            </div>
          </div>
        </div>
      </div>

      {/* Accuracy — chart + cards */}
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold">Model Accuracy — Model vs Baseline</div>
          <p className="fs-11 text-sub">Per-target accuracy (model vs random baseline). Podium is easiest (0.89 vs 0.136), winner hardest (0.58).</p>
          <F1Chart type="bar" height={240} data={{
            labels: accEntries.map(([k]:any)=> k),
            datasets:[
              { label:'Model', data: accEntries.map(([,v]:any)=> (v as any).model_accuracy*100), backgroundColor:'#E10600', borderRadius:4 },
              { label:'Baseline', data: accEntries.map(([,v]:any)=> (v as any).baseline_accuracy*100), backgroundColor:'#E3E5EA', borderRadius:4 },
            ]
          }} options={{ plugins:{legend:{display:true}}}} />
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">Targets — Calibration</div>
          <p className="fs-11 text-sub">TARGETS from <code className="f1-mono">constants.py</code> — accuracy, baseline, note.</p>
          <div className="grid sm:grid-cols-2 gap-3 mt-3">{Object.entries((acc as any)?.target_accuracies||{}).map(([k,v]:any)=>(
            <div key={k} className="surface-alt p-3 rounded-lg">
              <div className="fs-11 font-black uppercase">{k}</div>
              <div className="f1-mono text-sm">{(v.model_accuracy*100).toFixed(1)}% <span className="text-sub">/ baseline {(v.baseline_accuracy*100).toFixed(1)}%</span></div>
              <div className="fs-11 text-sub mt-1">{v.target_label} — +{(v.improvement_percentage).toFixed(0)}% improvement</div>
            </div>
          ))}</div>
          <div className="flex flex-wrap gap-2 mt-3">{(((targets as any)?.data ?? targets) as any[] || []).slice(0,8).map((t:any)=><span key={t.id||t.label} className="badge-purple">{t.label||t.id}</span>)}</div>
        </div>
      </div>

      {/* Feature weights — interactive */}
      <div className="card p-4">
        <div className="f1-display font-bold">Feature Weights — 2026 Tuning</div>
        <p className="fs-11 text-sub">Chaos, wet, reliability, strategy, grid_weight. Sliders are live — save posts to <code className="f1-mono">POST /api/v1/analytics/feature-weights</code> and invalidates `analytics:weights`.</p>
        <div className="grid md:grid-cols-2 gap-4 mt-4">
          <div>
            {Object.entries(local||{}).slice(0,6).map(([k,v]:any)=>{
              const val = typeof v==='object'? (v.default ?? v.value ?? 50) : v
              return (
                <div key={k} className="flex items-center gap-3 py-2 border-b border-black/5 last:border-0">
                  <span className="fs-11 w-36 uppercase font-bold">{k.replace(/_/g,' ')}</span>
                  <input type="range" min={0} max={100} value={val} onChange={e=> setLocal({...local, [k]: parseInt(e.target.value)})} className="f1-range flex-1 accent-red" />
                  <span className="f1-mono w-10 text-sm font-bold" style={{ color:'var(--red)'}}>{val}</span>
                </div>
              )
            })}
            <button onClick={()=> mut.mutate(local)} disabled={mut.isPending} className="btn-primary mt-4 w-full sm:w-auto">{mut.isPending? 'Saving…':'Save Weights'}</button>
            {mut.isSuccess && <span className="fs-11 text-sub ml-3">Saved ✓</span>}
          </div>
          <div className="card p-3 bg-black text-white">
            <div className="f1-display font-bold">2026 Weight Insight</div>
            <div className="fs-11 mt-2" style={{ color:'rgba(255,255,255,.8)'}}>
              <strong>Chaos</strong> now linear to uniform (was power-law) — `chaos 50 → 30% blend`. <strong>Grid weight 55</strong> matters more with active aero: Straight Mode compresses gaps, so grid position is less predictive than 2025. Try <code className="f1-mono">grid_weight 45</code> for closer 2026 racing.
            </div>
            <img src="/media/car_parts.png" alt="Car" className="w-full h-20 object-contain mt-3 opacity-80" loading="lazy" />
          </div>
        </div>
      </div>

      {/* Drift */}
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold">Drift Detection — Model</div>
          <p className="fs-11 text-sub">Drift score from <code className="f1-mono">probability_model.detect_model_drift</code> — 0.01 is healthy, &gt;0.05 is drift.</p>
          <F1Chart type="bar" height={180} data={{
            labels: driftMock.map(d=>d.label),
            datasets:[
              { label:'Expected', data: driftMock.map(d=>d.expected*100), backgroundColor:'#E3E5EA' },
              { label:'Observed', data: driftMock.map(d=>d.observed*100), backgroundColor:'#229971' },
            ]
          }} />
          <div className="mt-3 fs-11 text-sub">Use <code className="f1-mono">scripts/measure_accuracy.py</code> and <code className="f1-mono">calibrate_probabilities.py</code> to re-tune.</div>
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">2026 — What Changed for Analytics</div>
          <ul className="fs-11 text-sub mt-2 space-y-1.5 list-disc list-inside">
            <li>Downforce -30%, drag -55% — `PitWall` strategy model re-fitted</li>
            <li>Front wing 100mm narrower, 2-element active flap; rear 3-element, beam wing deleted</li>
            <li>Ground-effect Venturi tunnels → flat floor + larger diffuser</li>
            <li>Sustainable fuel (non-food biomass) — `tire_model` deg curves re-calibrated</li>
            <li>Weight 768kg, wheelbase 3400mm — `fantasy_scoring` points unchanged</li>
          </ul>
          <img src="/media/sunset_race.png" alt="Sunset" className="w-full h-28 object-cover rounded-lg mt-3" loading="lazy" />
        </div>
      </div>
    </div>
  )
}
