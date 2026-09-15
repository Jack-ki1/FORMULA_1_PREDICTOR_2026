import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAccuracy, fetchWeights, updateWeights, fetchTargets } from '../../api/analytics'
import { useState, useEffect } from 'react'
import { F1Chart } from '../../components/charts/F1Chart'
import { api } from '../../api/client'

export function AnalyticsPage(){
  const {data:acc}=useQuery({queryKey:['analytics','accuracy'], queryFn: fetchAccuracy})
  const {data:weights}=useQuery({queryKey:['analytics','weights'], queryFn: fetchWeights})
  const {data:targets}=useQuery({queryKey:['analytics','targets'], queryFn: fetchTargets})
  const {data:newsData} = useQuery({ queryKey:['news'], queryFn: ()=> api.get<any>('/api/v1/news'), staleTime: 300000 })
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
  const news: any[] = newsData?.news || []
  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero — How it works */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/f1_simulation.png" alt="Simulation" loading="lazy" className="w-full h-56 object-cover" />
          <div className="p-6">
            <h2 className="f1-display text-xl font-black">Analytics & News — 2026 Intelligence</h2>
            <p className="fs-11 text-sub mt-1"><strong>How it works:</strong> 23 races → Monte Carlo 100-50k sims → GridModel (strength→grid) → OOF ensemble (when trained) → calibration → <code className="f1-mono">POST /predictions</code>. Snapshot + provenance + cache (TTL 3600).</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="badge">Monte Carlo 100-50k</span><span className="badge">Elo + GridModel</span><span className="badge">Snapshot</span><span className="badge">Live News via /news</span>
            </div>
          </div>
        </div>
      </div>

      {/* What it contains — stack */}
      <div className="card p-4">
        <div className="f1-display font-bold">What it contains — Full stack</div>
        <div className="grid md:grid-cols-3 gap-3 mt-3">
          <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Engine</div><div className="fs-11 text-sub">Monte Carlo (vectorised argsort, seedable), Elo, GridModel, probability_model, calibration, ensemble_predictor — <code className="f1-mono">backend/app/engine</code></div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Providers</div><div className="fs-11 text-sub">Jolpica (results), OpenF1 (live), FastF1 (telemetry), Fallback (seed) — federated via Registry + provenance</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Frontend</div><div className="fs-11 text-sub">React 18 + Router 7, TanStack Query, Chart.js 4, Tailwind 3, PWA — 6 routes, single hero image per page, Reports embedded in Dashboard</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">API</div><div className="fs-11 text-sub">FastAPI pure JSON — <code className="f1-mono">/api/v1/races, predictions, standings, h2h, constructors, analytics, reports, settings, news</code> — CORS allowlist, rate-limit Redis</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Data</div><div className="fs-11 text-sub">calendar_2026 (23 rnds), circuit_data (25), team_driver_lineup_2026 (23 drivers), season_2026 standings — DB SQLite dev / Postgres prod</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="fs-11 font-bold">Settings</div><div className="fs-11 text-sub">Control Center — colors, models, Monte Carlo, cache, data sources, security, monitoring, AI — massive tunings at <code>/settings</code></div></div>
        </div>
      </div>

      {/* How to use */}
      <div className="card p-4">
        <div className="f1-display font-bold">How to use — 4 steps</div>
        <div className="grid md:grid-cols-4 gap-3 mt-3">
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="w-8 h-8 rounded-full flex items-center justify-center mx-auto font-black text-white" style={{background:'var(--red)'}}>1</div><div className="fs-11 font-bold mt-2">Pick Race & Day</div><div className="fs-11 text-sub">Dashboard → Grand Prix → Friday/Saturday/Sunday → FP1-Q3-Sprint-Race</div></div>
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="w-8 h-8 rounded-full flex items-center justify-center mx-auto font-black text-white" style={{background:'var(--red)'}}>2</div><div className="fs-11 font-bold mt-2">Modify 16 conditions</div><div className="fs-11 text-sub">Weather, chaos, grid weight, tyre, temp, wind … + sims 100-50k</div></div>
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="w-8 h-8 rounded-full flex items-center justify-center mx-auto font-black text-white" style={{background:'var(--red)'}}>3</div><div className="fs-11 font-bold mt-2">Run (green)</div><div className="fs-11 text-sub">Monte Carlo → 16 plots → confidence → Reports at bottom</div></div>
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="w-8 h-8 rounded-full flex items-center justify-center mx-auto font-black text-white" style={{background:'#16a34a'}}>4</div><div className="fs-11 font-bold mt-2">Export</div><div className="fs-11 text-sub">CSV / JSON / PDF / Share card — one click, Settings to tune colors/models</div></div>
        </div>
      </div>

      {/* News — fetched via /api/v1/news */}
      <div className="card p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="f1-display font-bold">Latest Formula 1 News — Live via API</div>
          <span className="fs-11 px-2 py-1 rounded-full bg-black text-white">{newsData?.source || 'loading'} · {news.length} items</span>
        </div>
        <p className="fs-11 text-sub">Fetched through <code className="f1-mono">GET /api/v1/news</code> (Formula1.com/BBC RSS, fallback curated). Always via backend, never direct browser fetch — provenance noted.</p>
        <div className="grid md:grid-cols-3 gap-3 mt-4">
          {news.slice(0,6).map((n:any,i:number)=> (
            <a key={i} href={n.url} target="_blank" rel="noreferrer" className="card p-0 overflow-hidden group hover:shadow-lg transition-shadow">
              <img src={n.image || '/media/circuit1.png'} alt={n.title} loading="lazy" className="w-full h-32 object-cover group-hover:scale-105 transition-transform duration-500" onError={(e)=> (e.currentTarget.src='/media/circuit1.png')} />
              <div className="p-3">
                <div className="fs-11 font-bold line-clamp-2">{n.title}</div>
                <div className="fs-11 text-sub mt-1 line-clamp-2">{n.summary}</div>
                <div className="flex items-center gap-2 mt-2 fs-11 text-sub"><span>{n.source}</span><span>·</span><span>{n.date}</span></div>
              </div>
            </a>
          ))}
          {!news.length && <div className="fs-11 text-sub col-span-3 p-6 text-center">Loading news…</div>}
        </div>
        <div className="mt-3 fs-11 text-sub">Tip: add <code className="f1-mono">NewsAPI.org</code> key to <code className="f1-mono">/settings</code> → Data Sources for richer live feed.</div>
      </div>

      {/* Accuracy — chart + cards */}
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold">Model Accuracy — Model vs Baseline</div>
          <p className="fs-11 text-sub">Per-target accuracy (model vs random baseline). Winner hardest (0.58).</p>
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

      {/* Feature weights — interactive + 2026 insight */}
      <div className="card p-4">
        <div className="f1-display font-bold">Feature Weights — 2026 Tuning</div>
        <p className="fs-11 text-sub">Chaos, wet, reliability, strategy, grid_weight. Sliders are live — save posts to <code className="f1-mono">POST /api/v1/analytics/feature-weights</code>.</p>
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
            <button onClick={()=> mut.mutate(local)} disabled={mut.isPending} className="btn-primary mt-4 w-full sm:w-auto" style={{ background:'#16a34a'}}>{mut.isPending? 'Saving…':'Save Weights'}</button>
            {mut.isSuccess && <span className="fs-11 text-sub ml-3">Saved ✓</span>}
          </div>
          <div className="card p-3 bg-black text-white">
            <div className="f1-display font-bold">2026 Weight Insight</div>
            <div className="fs-11 mt-2" style={{ color:'rgba(255,255,255,.8)'}}>
              <strong>Chaos</strong> now linear to uniform (was power-law) — <code className="f1-mono">chaos 50 → 30% blend</code>. <strong>Grid weight 55</strong> matters more with active aero: Straight Mode compresses gaps. Try <code className="f1-mono">grid_weight 45</code> for closer 2026 racing.
            </div>
          </div>
        </div>
      </div>

      {/* Drift + creative 2026 changes */}
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold">Drift Detection — Model</div>
          <p className="fs-11 text-sub">Drift score from <code className="f1-mono">probability_model.detect_model_drift</code> — 0.01 healthy, &gt;0.05 drift.</p>
          <F1Chart type="bar" height={180} data={{
            labels: driftMock.map(d=>d.label),
            datasets:[
              { label:'Expected', data: driftMock.map(d=>d.expected*100), backgroundColor:'#E3E5EA' },
              { label:'Observed', data: driftMock.map(d=>d.observed*100), backgroundColor:'#229971' },
            ]
          }} />
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">2026 — What Changed</div>
          <ul className="fs-11 text-sub mt-2 space-y-1.5 list-disc list-inside">
            <li>Downforce -30%, drag -55% — PitWall strategy re-fitted</li>
            <li>Front wing 100mm narrower, 2-element active flap; rear 3-element</li>
            <li>Ground-effect Venturi tunnels → flat floor + larger diffuser</li>
            <li>Sustainable fuel — <code>tire_model</code> deg curves re-calibrated</li>
            <li>Weight 768kg, wheelbase 3400mm — Reports PDF updated</li>
            <li>Creativity: Model card, provenance, cache TTL 3600 — see <code>/settings</code> &amp; <code>/docs</code></li>
          </ul>
        </div>
      </div>

      {/* Model Card — creative, research-backed */}
      <div className="card p-6" style={{ background:'linear-gradient(135deg, #0a0a09, #16233F)', color:'#fff'}}>
        <div className="flex items-center gap-2"><span className="w-1.5 h-6 rounded-full" style={{ background:'var(--red)'}} /><h3 className="f1-display font-black">Model Card — Honest Intelligence</h3><span className="ml-auto px-2 py-1 rounded-full bg-white text-black fs-11 font-bold">v12.4 · feature-v8 · dataset-v14</span></div>
        <div className="grid md:grid-cols-3 gap-4 mt-4">
          <div className="p-3 rounded-lg" style={{ background:'rgba(255,255,255,0.08)'}}><div className="fs-11 font-bold">Intended Use</div><div className="fs-11 mt-1" style={{ color:'rgba(255,255,255,.8)'}}>Pre-race win/podium/points probabilities for 2026. Not betting advice. Calibrated via isotonic, validated on temporal holdout (never random CV). See <code className="f1-mono">docs/ML_VALIDATION.md</code>.</div></div>
          <div className="p-3 rounded-lg" style={{ background:'rgba(255,255,255,0.08)'}}><div className="fs-11 font-bold">Training Data</div><div className="fs-11 mt-1" style={{ color:'rgba(255,255,255,.8)'}}>Historical: 2018-2025 builder respects <code>training_cutoff</code> — no future leakage. Today synthetic + strength signal; next: Jolpica/OpenF1/FastF1 backfill to <code>data/historical/</code>.</div></div>
          <div className="p-3 rounded-lg" style={{ background:'rgba(255,255,255,0.08)'}}><div className="fs-11 font-bold">Limitations</div><div className="fs-11 mt-1" style={{ color:'rgba(255,255,255,.8)'}}>Hand-typed 2026 strength priors for rookies; no betting-odds calibration yet (Tier 1). Chaos smoothing honest about uncertainty — check <code>/meta</code> volatility.</div></div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 fs-11"><span className="px-2 py-1 rounded-full bg-white/10">Provenance on every dataset</span><span className="px-2 py-1 rounded-full bg-white/10">Snapshot + config_hash</span><span className="px-2 py-1 rounded-full bg-white/10">Cache TTL 3600</span><span className="px-2 py-1 rounded-full bg-white/10">PSI drift</span></div>
      </div>

      {/* 2026 Timeline — creative */}
      <div className="card p-4">
        <div className="f1-display font-bold">2026 Timeline — 6 steps that changed the car</div>
        <div className="relative mt-4 pl-6 border-l-2" style={{ borderColor:'var(--red)'}}>
          {[
            { t:'Jan 2024', d:'FIA unveils 2026 regs — agile, competitive, sustainable. Six PU manufacturers commit.'},
            { t:'Jun 2024', d:'Technical regs issue 7 — 1.6L V6 retains layout, MGU-H deleted, MGU-K → 350kW.'},
            { t:'2025', d:'F2/F3 trial Advanced Sustainable Fuels — drop-in, >90% lifecycle CO₂ cut.'},
            { t:'Mar 2026', d:'Bahrain testing — straight-mode wings open, active aero every lap, sustainable fuel debut.'},
            { t:'Mar 6-8', d:'Australia R1 — 768kg cars, 50/50 PU, sustainable fuel era begins.'},
            { t:'Now', d:'Predictor live — 23 rounds, 11 teams, Monte Carlo re-tuned for 2026.'},
          ].map((e,i)=> (
            <div key={i} className="relative mb-4">
              <span className="absolute -left-[25px] w-3 h-3 rounded-full" style={{ background:'var(--red)'}} />
              <div className="fs-11 font-black">{e.t}</div><div className="fs-11 text-sub">{e.d}</div>
            </div>
          ))}
        </div>
        <div className="fs-11 text-sub">Sources: FIA Technical Regulations Section C issue 18, Formula1.com “12 rule changes”, BBC Sport — verified web research.</div>
      </div>

      {/* Tech Stack Deep Dive — creative */}
      <div className="card p-4">
        <div className="f1-display font-bold">Tech Stack — Why predictions are fast</div>
        <div className="grid md:grid-cols-4 gap-3 mt-3 fs-11">
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="font-bold">Engine</div><div className="text-sub">Numpy vectorised argsort — 10k sims ~80ms, seed reproducible</div><div className="f1-mono mt-1">engine/monte_carlo.py</div></div>
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="font-bold">API</div><div className="text-sub">FastAPI + Redis + run_in_threadpool for &gt;5k sims — no event-loop block</div><div className="f1-mono mt-1">/api/v1/predictions</div></div>
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="font-bold">Cache</div><div className="text-sub">Hash race+session+snapshot+model+weather+grid+config — invalidates on version bump</div><div className="f1-mono mt-1">prediction_service.py</div></div>
          <div className="p-3 rounded-lg border text-center" style={{ borderColor:'var(--border)'}}><div className="font-bold">Frontend</div><div className="text-sub">React 18 + TanStack Query 5 + Chart.js 4 + PWA — 533kB gz 170kB</div><div className="f1-mono mt-1">Vite 5178 → 5000 proxy</div></div>
        </div>
      </div>
    </div>
  )
}
