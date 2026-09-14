import { useState, useMemo } from 'react'
import { useDrivers, useH2HCompare } from '../../hooks/useH2H'
import { TeamStripe } from '../../components/shared/TeamStripe'
import { DuelRadar } from '../../components/h2h/DuelRadar'
import { F1Chart } from '../../components/charts/F1Chart'

export function H2HPage(){
  const {data:drivers}=useDrivers()
  const mut=useH2HCompare()
  const [a,setA]=useState(''); const [b,setB]=useState('')
  const driverMap = useMemo(()=> {
    const m: Record<string, any> = {}
    ;(drivers||[]).forEach((d:any)=> m[d.code]=d)
    return m
  }, [drivers])
  const racerImg = (code:string) => {
    const idx = (code.charCodeAt(0) + (code.charCodeAt(1)||0)) % 3
    return ['/media/racer1.png','/media/racer2.png','/media/racer3.png'][idx]
  }
  const pctA = mut.data ? (mut.data.win_probability*100) : 50
  const pctB = mut.data ? (mut.data.reverse_probability*100) : 50

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/racer1.png" alt="Duel" loading="lazy" className="w-full h-44 object-cover" />
          <div className="p-6">
            <h2 className="f1-display text-xl font-black">Head-to-Head — 2026 Duel</h2>
            <p className="fs-11 text-sub mt-1">Elo with 400-pt divisor + wet-skill/consistency. Active aero shrinks gaps — 2026 duels are closer than 2025.</p>
            <div className="flex gap-2 mt-3">
              <span className="badge">Elo 400</span><span className="badge">Wet skill</span><span className="badge">Consistency</span><span className="badge">2026 NEW: Active aero</span>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="card p-4">
        <div className="f1-display font-bold mb-3">Pick Your Duel</div>
        <div className="grid sm:grid-cols-3 gap-3">
          <select value={a} onChange={e=>setA(e.target.value)} className="f1-select"><option value="">Driver A</option>{(drivers||[]).map((d:any)=><option key={d.code} value={d.code}>{d.code} — {d.name} ({d.team_id})</option>)}</select>
          <select value={b} onChange={e=>setB(e.target.value)} className="f1-select"><option value="">Driver B</option>{(drivers||[]).map((d:any)=><option key={d.code} value={d.code}>{d.code} — {d.name} ({d.team_id})</option>)}</select>
          <button onClick={()=> mut.mutate({a,b})} disabled={!a||!b||mut.isPending} className="btn-primary disabled:opacity-50">{mut.isPending? 'Calculating…':'Compare — Elo'}</button>
        </div>
        <div className="fs-11 text-sub mt-2">Tip: try VER vs HAM, NOR vs PIA (McLaren teammates), or LEC vs HAM (Ferrari 2026).</div>
      </div>

      {mut.data && (
        <>
          {/* Driver cards */}
          <div className="grid md:grid-cols-3 gap-4 items-stretch">
            <div className="card p-4 text-center">
              <img src={racerImg(mut.data.driver_a.code)} alt={mut.data.driver_a.code} className="w-28 h-28 mx-auto rounded-full object-cover border-4 shadow-lg" style={{ borderColor: driverMap[mut.data.driver_a.code]?.team_color||'#E10600' }} loading="lazy" />
              <div className="f1-display font-black mt-3 flex items-center justify-center gap-2"><TeamStripe color={driverMap[mut.data.driver_a.code]?.team_color} />{mut.data.driver_a.code}</div>
              <div className="fs-11 text-sub">{mut.data.driver_a.name} · #{mut.data.driver_a.number} · {mut.data.driver_a.team_name}</div>
              <div className="grid grid-cols-3 gap-2 mt-3">
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Strength</div><div className="f1-mono">{driverMap[mut.data.driver_a.code]?.strength ?? 75}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Wet</div><div className="f1-mono">{driverMap[mut.data.driver_a.code]?.wet_skill ?? 80}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Reliability</div><div className="f1-mono">{driverMap[mut.data.driver_a.code]?.reliability ?? 88}</div></div>
              </div>
            </div>
            <div className="card p-4 flex flex-col items-center justify-center text-center">
              <div className="f1-display text-3xl font-black" style={{ color:'var(--red)'}}>VS</div>
              <div className="w-full mt-4">
                <div className="flex justify-between fs-11 font-bold"><span>{mut.data.driver_a.code} {pctA.toFixed(1)}%</span><span>{pctB.toFixed(1)}% {mut.data.driver_b.code}</span></div>
                <div className="h-3 rounded-full overflow-hidden bg-black/10 mt-1 flex">
                  <div className="h-full" style={{ width:`${pctA}%`, background: driverMap[mut.data.driver_a.code]?.team_color||'#E10600'}} />
                  <div className="h-full" style={{ width:`${pctB}%`, background: driverMap[mut.data.driver_b.code]?.team_color||'#3671C6'}} />
                </div>
                <div className="fs-11 text-sub mt-1">Elo win probability via <code className="f1-mono">/api/v1/h2h/compare</code></div>
              </div>
              <div className="mt-4 p-3 rounded-lg bg-black text-white w-full">
                <div className="fs-11">2026 Insight</div>
                <div className="fs-11 mt-1" style={{ color:'rgba(255,255,255,.8)'}}>Active aero + 50/50 PU narrows gaps. Overtake Mode (+0.5MJ) can flip this duel on the straight.</div>
              </div>
            </div>
            <div className="card p-4 text-center">
              <img src={racerImg(mut.data.driver_b.code)} alt={mut.data.driver_b.code} className="w-28 h-28 mx-auto rounded-full object-cover border-4 shadow-lg" style={{ borderColor: driverMap[mut.data.driver_b.code]?.team_color||'#3671C6' }} loading="lazy" />
              <div className="f1-display font-black mt-3 flex items-center justify-center gap-2"><TeamStripe color={driverMap[mut.data.driver_b.code]?.team_color} />{mut.data.driver_b.code}</div>
              <div className="fs-11 text-sub">{mut.data.driver_b.name} · #{mut.data.driver_b.number} · {mut.data.driver_b.team_name}</div>
              <div className="grid grid-cols-3 gap-2 mt-3">
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Strength</div><div className="f1-mono">{driverMap[mut.data.driver_b.code]?.strength ?? 75}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Wet</div><div className="f1-mono">{driverMap[mut.data.driver_b.code]?.wet_skill ?? 80}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Reliability</div><div className="f1-mono">{driverMap[mut.data.driver_b.code]?.reliability ?? 88}</div></div>
              </div>
            </div>
          </div>

          {/* Attribute bars */}
          <div className="card p-4">
            <div className="f1-display font-bold mb-3">Attribute Breakdown — Strength vs Wet vs Consistency vs Reliability</div>
            <div className="space-y-3">
              {[
                {k:'strength', label:'Pace (strength)', a: driverMap[mut.data.driver_a.code]?.strength ?? 50, b: driverMap[mut.data.driver_b.code]?.strength ?? 50},
                {k:'wet_skill', label:'Wet Skill', a: driverMap[mut.data.driver_a.code]?.wet_skill ?? 50, b: driverMap[mut.data.driver_b.code]?.wet_skill ?? 50},
                {k:'consistency', label:'Consistency', a: (driverMap[mut.data.driver_a.code]?.consistency ?? 0.5)*100, b: (driverMap[mut.data.driver_b.code]?.consistency ?? 0.5)*100},
                {k:'reliability', label:'Reliability', a: driverMap[mut.data.driver_a.code]?.reliability ?? 85, b: driverMap[mut.data.driver_b.code]?.reliability ?? 85},
              ].map(row=> (
                <div key={row.k} className="grid grid-cols-5 gap-2 items-center">
                  <span className="fs-11 font-bold text-right">{row.label}</span>
                  <div className="col-span-2 flex items-center gap-2">
                    <span className="fs-11 w-8 text-right">{Math.round(row.a)}</span>
                    <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden"><div className="h-full" style={{ width:`${Math.min(100, row.a)}%`, background: driverMap[mut.data.driver_a.code]?.team_color||'#E10600'}} /></div>
                  </div>
                  <div className="col-span-2 flex items-center gap-2">
                    <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden"><div className="h-full" style={{ width:`${Math.min(100, row.b)}%`, background: driverMap[mut.data.driver_b.code]?.team_color||'#3671C6'}} /></div>
                    <span className="fs-11 w-8">{Math.round(row.b)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Radar + win prob bar */}
          <div className="grid lg:grid-cols-2 gap-4">
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">Radar — 5-Axis Skill</div>
              <DuelRadar
                a={{ code: mut.data.driver_a.code, team_color: driverMap[mut.data.driver_a.code]?.team_color, strength: driverMap[mut.data.driver_a.code]?.strength ?? 50, wet_skill: driverMap[mut.data.driver_a.code]?.wet_skill ?? 0.5, consistency: driverMap[mut.data.driver_a.code]?.consistency ?? 0.5, reliability: driverMap[mut.data.driver_a.code]?.reliability ?? 0.9 }}
                b={{ code: mut.data.driver_b.code, team_color: driverMap[mut.data.driver_b.code]?.team_color, strength: driverMap[mut.data.driver_b.code]?.strength ?? 50, wet_skill: driverMap[mut.data.driver_b.code]?.wet_skill ?? 0.5, consistency: driverMap[mut.data.driver_b.code]?.consistency ?? 0.5, reliability: driverMap[mut.data.driver_b.code]?.reliability ?? 0.9 }}
              />
            </div>
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">Win Probability — Visual</div>
              <F1Chart type="bar" height={180} data={{ labels:['Win %'], datasets:[
                { label: mut.data.driver_a.code, data:[pctA], backgroundColor: driverMap[mut.data.driver_a.code]?.team_color||'#E10600' },
                { label: mut.data.driver_b.code, data:[pctB], backgroundColor: driverMap[mut.data.driver_b.code]?.team_color||'#3671C6' },
              ]}} options={{ indexAxis:'y' as const, plugins:{legend:{display:true}}}} />
              <div className="mt-3 p-3 surface-alt rounded-lg fs-11">
                <span className="font-bold">2026 note:</span> Elo does not yet know active aero. Pair this with <a href="/dashboard" className="underline">Dashboard</a> Monte Carlo for GridModel-aware odds.
              </div>
            </div>
          </div>
        </>
      )}
      {mut.isError && <div className="card p-4 text-red border-red/30">Error: {(mut.error as any).message}</div>}
      {!mut.data && !mut.isError && (
        <div className="card p-6 text-center">
          <img src="/media/racer3.png" alt="Racers" className="w-32 h-32 mx-auto rounded-full object-cover opacity-60" loading="lazy" />
          <div className="f1-display font-bold mt-3">Pick two drivers to duel</div>
          <p className="fs-11 text-sub mt-1">800+ drivers in local fallback, 6-axis radar, 2026 Audi/Cadillac rookies included.</p>
        </div>
      )}
    </div>
  )
}
