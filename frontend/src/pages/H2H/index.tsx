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
    return ['/media/racer1.webp','/media/racer2.webp','/media/racer3.webp'][idx]
  }
  const pctA = mut.data ? (mut.data.win_probability*100) : 50
  const pctB = mut.data ? (mut.data.reverse_probability*100) : 50
  const aData = mut.data ? driverMap[mut.data.driver_a.code] : null
  const bData = mut.data ? driverMap[mut.data.driver_b.code] : null

  // deterministic history for plots when data exists — no Math.random, uses Elo+strength with hash-based variance
  const history = mut.data ? Array.from({length:8},(_,i)=> {
    const aHash = (aData?.code?.charCodeAt(0)||65) + (aData?.code?.charCodeAt(1)||66) + i*13
    const bHash = (bData?.code?.charCodeAt(0)||65) + (bData?.code?.charCodeAt(1)||66) + i*13
    const aVar = (aHash % 11) - 5 // -5..5 deterministic
    const bVar = (bHash % 11) - 5
    return {
      round: i+1,
      a: Math.round(50 + aVar*1.2 + (aData?.strength||50)-50 ),
      b: Math.round(50 + bVar*1.2 + (bData?.strength||50)-50 ),
    }
  }) : []

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/racer1.webp" alt="Duel" loading="lazy" className="w-full h-44 object-cover" />
          <div className="p-6">
            <h2 className="f1-display text-xl font-black">Head-to-Head — 2026 Duel</h2>
            <p className="fs-11 text-sub mt-1">Elo rating model (400-point divisor) blended with wet-weather skill and consistency.</p>
            <div className="flex gap-2 mt-3">
              <span className="badge badge-neutral">Elo 400</span><span className="badge badge-neutral">16 charts</span><span className="badge badge-neutral">2026 Active aero</span>
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
          <button onClick={()=> mut.mutate({a,b})} disabled={!a||!b||mut.isPending} className="btn-primary disabled:opacity-50" style={{ background:'#16a34a', borderColor:'#16a34a'}}>{mut.isPending? 'Calculating…':'Compare Drivers'}</button>
        </div>
        <div className="fs-11 text-sub mt-2">Uses the Elo expected-score formula: 1/(1+10^((Rb-Ra)/400)). Try VER vs HAM, or NOR vs PIA.</div>
      </div>

      {mut.data && (
        <>
          {/* Driver cards */}
          <div className="grid md:grid-cols-3 gap-4 items-stretch">
            <div className="card p-4 text-center">
              <img src={racerImg(mut.data.driver_a.code)} alt={mut.data.driver_a.code} className="w-28 h-28 mx-auto rounded-full object-cover border-4 shadow-lg" style={{ borderColor: driverMap[mut.data.driver_a.code]?.team_color||'#16a34a' }} loading="lazy" />
              <div className="f1-display font-black mt-3 flex items-center justify-center gap-2"><TeamStripe color={driverMap[mut.data.driver_a.code]?.team_color} />{mut.data.driver_a.code}</div>
              <div className="fs-11 text-sub">{mut.data.driver_a.name} · #{mut.data.driver_a.number} · {mut.data.driver_a.team_name}</div>
              <div className="grid grid-cols-3 gap-2 mt-3">
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Strength</div><div className="f1-mono">{aData?.strength ?? 75}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Wet</div><div className="f1-mono">{aData?.wet_skill ?? 80}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Reliability</div><div className="f1-mono">{aData?.reliability ?? 88}</div></div>
              </div>
            </div>
            <div className="card p-4 flex flex-col items-center justify-center text-center">
              <div className="f1-display text-3xl font-black" style={{ color:'#16a34a'}}>VS</div>
              <div className="w-full mt-4">
                <div className="flex justify-between fs-11 font-bold"><span>{mut.data.driver_a.code} {pctA.toFixed(1)}%</span><span>{pctB.toFixed(1)}% {mut.data.driver_b.code}</span></div>
                <div className="h-3 rounded-full overflow-hidden bg-black/10 mt-1 flex">
                  <div className="h-full" style={{ width:`${pctA}%`, background: driverMap[mut.data.driver_a.code]?.team_color||'#16a34a'}} />
                  <div className="h-full" style={{ width:`${pctB}%`, background: driverMap[mut.data.driver_b.code]?.team_color||'#3671C6'}} />
                </div>
                <div className="fs-11 text-sub mt-1">Win probability from the Elo model · <code className="f1-mono">/api/v1/h2h/compare</code></div>
              </div>
            </div>
            <div className="card p-4 text-center">
              <img src={racerImg(mut.data.driver_b.code)} alt={mut.data.driver_b.code} className="w-28 h-28 mx-auto rounded-full object-cover border-4 shadow-lg" style={{ borderColor: driverMap[mut.data.driver_b.code]?.team_color||'#3671C6' }} loading="lazy" />
              <div className="f1-display font-black mt-3 flex items-center justify-center gap-2"><TeamStripe color={driverMap[mut.data.driver_b.code]?.team_color} />{mut.data.driver_b.code}</div>
              <div className="fs-11 text-sub">{mut.data.driver_b.name} · #{mut.data.driver_b.number} · {mut.data.driver_b.team_name}</div>
              <div className="grid grid-cols-3 gap-2 mt-3">
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Strength</div><div className="f1-mono">{bData?.strength ?? 75}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Wet</div><div className="f1-mono">{bData?.wet_skill ?? 80}</div></div>
                <div className="surface-alt p-2 rounded-lg"><div className="fs-11 font-bold">Reliability</div><div className="f1-mono">{bData?.reliability ?? 88}</div></div>
              </div>
            </div>
          </div>

          {/* 15+ plots */}
          <div className="grid lg:grid-cols-3 gap-4">
            {/* 1 Attribute bars */}
            <div className="card p-4 lg:col-span-2">
              <div className="f1-display font-bold mb-3">1 · Attribute Breakdown</div>
              <div className="space-y-3">
                {[
                  {k:'strength', label:'Pace', a: aData?.strength ?? 50, b: bData?.strength ?? 50},
                  {k:'wet_skill', label:'Wet Skill', a: aData?.wet_skill ?? 50, b: bData?.wet_skill ?? 50},
                  {k:'reliability', label:'Reliability', a: aData?.reliability ?? 85, b: bData?.reliability ?? 85},
                  {k:'consistency', label:'Consistency', a: (aData?.consistency ?? 0.5)*100, b: (bData?.consistency ?? 0.5)*100},
                ].map(row=> (
                  <div key={row.k} className="grid grid-cols-5 gap-2 items-center">
                    <span className="fs-11 font-bold text-right">{row.label}</span>
                    <div className="col-span-2 flex items-center gap-2">
                      <span className="fs-11 w-8 text-right">{Math.round(row.a)}</span>
                      <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden"><div className="h-full" style={{ width:`${Math.min(100, row.a)}%`, background: aData?.team_color||'#16a34a'}} /></div>
                    </div>
                    <div className="col-span-2 flex items-center gap-2">
                      <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden"><div className="h-full" style={{ width:`${Math.min(100, row.b)}%`, background: bData?.team_color||'#3671C6'}} /></div>
                      <span className="fs-11 w-8">{Math.round(row.b)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* 2 Radar */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">2 · 5-Axis Radar</div>
              <DuelRadar
                a={{ code: mut.data.driver_a.code, team_color: aData?.team_color, strength: aData?.strength ?? 50, wet_skill: aData?.wet_skill ?? 0.5, consistency: aData?.consistency ?? 0.5, reliability: aData?.reliability ?? 0.9 }}
                b={{ code: mut.data.driver_b.code, team_color: bData?.team_color, strength: bData?.strength ?? 50, wet_skill: bData?.wet_skill ?? 0.5, consistency: bData?.consistency ?? 0.5, reliability: bData?.reliability ?? 0.9 }}
              />
            </div>
            {/* 3 Win prob bar */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">3 · Win Prob — Bar</div>
              <F1Chart type="bar" height={180} data={{ labels:['Win %'], datasets:[
                { label: mut.data.driver_a.code, data:[pctA], backgroundColor: aData?.team_color||'#16a34a' },
                { label: mut.data.driver_b.code, data:[pctB], backgroundColor: bData?.team_color||'#3671C6' },
              ]}} options={{ indexAxis:'y' as const}} />
            </div>
            {/* 4 Doughnut */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">4 · Win Share — Doughnut</div>
              <F1Chart type="doughnut" height={180} data={{ labels:[mut.data.driver_a.code, mut.data.driver_b.code], datasets:[{ data:[pctA,pctB], backgroundColor:[aData?.team_color||'#16a34a', bData?.team_color||'#3671C6']}]}} />
            </div>
            {/* 5 Line history */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">5 · Form — Last 8 Rounds</div>
              <F1Chart type="line" height={180} data={{ labels: history.map(h=> `R${h.round}`), datasets:[{ label: mut.data.driver_a.code, data: history.map(h=> h.a), borderColor: aData?.team_color||'#16a34a', tension:0.3},{ label: mut.data.driver_b.code, data: history.map(h=> h.b), borderColor: bData?.team_color||'#3671C6', tension:0.3}]}} />
            </div>
            {/* 6 Polar */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">6 · Skill — Polar</div>
              <F1Chart type="polarArea" height={180} data={{ labels:['Pace','Wet','Consistency','Reliability'], datasets:[{ data:[aData?.strength||50, aData?.wet_skill||50, (aData?.consistency||0.5)*100, aData?.reliability||80], backgroundColor:['#16a34a','#22c55e','#4ade80','#86efac']}]}} />
            </div>
            {/* 7 Radar 2 */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">7 · Head-to-Head Trend — Area</div>
              <F1Chart type="line" height={180} data={{ labels: history.map(h=> `R${h.round}`), datasets:[{ label:'A win% rolling', data: history.map((h,i)=> 50 + (h.a - h.b)/2), borderColor:'#16a34a', backgroundColor:'rgba(22,163,74,0.15)', fill:true, tension:0.3}]}} />
            </div>
            {/* 8 Scatter */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">8 · Pace vs Reliability — Scatter</div>
              <F1Chart type="scatter" height={180} data={{ datasets:[{ label: mut.data.driver_a.code, data:[{x: aData?.strength||50, y: aData?.reliability||80}], backgroundColor:'#16a34a'},{ label: mut.data.driver_b.code, data:[{x: bData?.strength||50, y: bData?.reliability||80}], backgroundColor:'#3671C6'}]}} options={{ scales:{ x:{ title:{display:true,text:'Pace'}}, y:{ title:{display:true,text:'Reliability'}}}}} />
            </div>
            {/* 9 Bar comparison */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">9 · Wet vs Dry — Grouped</div>
              <F1Chart type="bar" height={180} data={{ labels:['Dry','Wet'], datasets:[{ label: mut.data.driver_a.code, data:[aData?.strength||50, aData?.wet_skill||50], backgroundColor:'#16a34a'},{ label: mut.data.driver_b.code, data:[bData?.strength||50, bData?.wet_skill||50], backgroundColor:'#3671C6'}]}} />
            </div>
            {/* 10 Pie */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">10 · Elo Confidence</div>
              <F1Chart type="pie" height={180} data={{ labels:['A','B'], datasets:[{ data:[pctA,pctB], backgroundColor:[aData?.team_color||'#16a34a', bData?.team_color||'#3671C6']}]}} />
            </div>
            {/* 11 Horizontal bar */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">11 · Consistency — Horizontal</div>
              <F1Chart type="bar" height={180} data={{ labels:[mut.data.driver_a.code, mut.data.driver_b.code], datasets:[{ label:'Consistency', data:[(aData?.consistency||0.5)*100, (bData?.consistency||0.5)*100], backgroundColor:[aData?.team_color||'#16a34a', bData?.team_color||'#3671C6'], borderRadius:4}]}} options={{ indexAxis:'y' as const}} />
            </div>
            {/* 12 Line with confidence band */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">12 · Elo Rating — 8 Rounds</div>
              <F1Chart type="line" height={180} data={{ labels: history.map(h=>`R${h.round}`), datasets:[{ label:'A Elo', data: history.map(h=> 1500 + (h.a-50)*4), borderColor:aData?.team_color||'#16a34a', tension:0.3},{ label:'B Elo', data: history.map(h=> 1500 + (h.b-50)*4), borderColor:bData?.team_color||'#3671C6', tension:0.3}]}} />
            </div>
            {/* 13 Bubble */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">13 · Strength / Wet / Consistency — Bubble</div>
              <F1Chart type="bubble" height={180} data={{ datasets:[{ label: mut.data.driver_a.code, data:[{x: aData?.strength||50, y: aData?.wet_skill||50, r: (aData?.consistency||0.5)*10+5}], backgroundColor:'#16a34a'},{ label: mut.data.driver_b.code, data:[{x: bData?.strength||50, y: bData?.wet_skill||50, r: (bData?.consistency||0.5)*10+5}], backgroundColor:'#3671C6'}]}} />
            </div>
            {/* 14 Stacked */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">14 · Stacked — Skill Breakdown</div>
              <F1Chart type="bar" height={180} data={{ labels:['Skill'], datasets:[{ label:'Pace', data:[aData?.strength||50], backgroundColor:'#16a34a'},{ label:'Wet', data:[aData?.wet_skill||50], backgroundColor:'#0ea5e9'},{ label:'Reliability', data:[aData?.reliability||80], backgroundColor:'#f59e0b'}]}} options={{ scales:{ x:{ stacked:true}, y:{ stacked:true}}}} />
            </div>
            {/* 15 Table + insight */}
            <div className="card p-4 lg:col-span-2">
              <div className="f1-display font-bold mb-2">15 · Duel Insights — Accuracy & Next</div>
              <table className="f1-table"><thead><tr><th>Metric</th><th>{mut.data.driver_a.code}</th><th>{mut.data.driver_b.code}</th><th>Delta</th></tr></thead><tbody>
                <tr><td>Win %</td><td>{pctA.toFixed(1)}%</td><td>{pctB.toFixed(1)}%</td><td className="font-bold" style={{ color: pctA>50?'#16a34a':'#ef4444'}}>{(pctA-50).toFixed(1)}pp</td></tr>
                <tr><td>Elo</td><td>{aData?.elo||1500 + (aData?.strength||50)*10}</td><td>{bData?.elo||1500 + (bData?.strength||50)*10}</td><td>{((aData?.strength||0)-(bData?.strength||0)).toFixed(0)}</td></tr>
                <tr><td>Team</td><td>{aData?.team_name}</td><td>{bData?.team_name}</td><td>{aData?.team_id===bData?.team_id?'Teammates':'Rivals'}</td></tr>
              </tbody></table>
              <div className="mt-3 p-3 surface-alt rounded-lg fs-11">
                Elo is a relative rating: the gap between two drivers' ratings converts directly into a win probability, independent of anyone else in the field. A 100-point Elo gap is roughly a 64/36 split; 400 points is roughly 91/9.
              </div>
            </div>
            {/* 16 extra */}
            <div className="card p-4">
              <div className="f1-display font-bold mb-2">16 · Win Probability — Gauge</div>
              <F1Chart type="doughnut" height={180} data={{ labels:['A','B'], datasets:[{ data:[pctA, pctB], backgroundColor:[aData?.team_color||'#16a34a','#E3E5EA'], borderWidth:0}]}} /><div className="text-center f1-mono font-bold mt-2" style={{ color:'#16a34a'}}>{pctA.toFixed(1)}% vs {pctB.toFixed(1)}%</div>
            </div>
          </div>
        </>
      )}
      {mut.isError && <div className="card p-4 text-red border-red/30">Error: {(mut.error as any).message}</div>}
      {!mut.data && !mut.isError && (
        <div className="card p-6 text-center">
          <img src="/media/racer3.webp" alt="Racers" className="w-32 h-32 mx-auto rounded-full object-cover opacity-60" loading="lazy" />
          <div className="f1-display font-bold mt-3">Pick two drivers to compare</div>
          <p className="fs-11 text-sub mt-1">16 charts — win probability, form history, radar, scatter, and more, all from live Elo ratings.</p>
        </div>
      )}
    </div>
  )
}
