import { useState, useMemo, useEffect } from 'react'
import { useDrivers } from '../../hooks/useH2H'
import { TeamStripe } from '../../components/shared/TeamStripe'
import { F1Chart } from '../../components/charts/F1Chart'
import { api } from '../../api/client'

const CHIPS = [
  { id:'wildcard', name:'Wildcard', icon:'🃏', desc:'Unlimited transfers', when:'Once/season', color:'#8b5cf6' },
  { id:'limitless', name:'Limitless', icon:'♾️', desc:'No budget cap + unlimited', when:'One GP', color:'#E10600' },
  { id:'extra_drs', name:'Extra DRS', icon:'⚡', desc:'3× boost (stacks 2×)', when:'Once', color:'#0ea5e9' },
  { id:'no_negative', name:'No Negative', icon:'🛡️', desc:'Negatives → 0', when:'Once', color:'#16a34a' },
  { id:'autopilot', name:'Autopilot', icon:'🤖', desc:'Top scorer auto captain', when:'Once', color:'#f59e0b' },
  { id:'final_fix', name:'Final Fix', icon:'🔧', desc:'Change 1 driver after quali', when:'Once', color:'#6b7280' },
]

function priceForDriver(d:any): number {
  const base = 3 + (Number(d?.strength)||50)*0.27
  return Math.round(base*2)/2
}
function priceForTeam(power:number): number {
  return Math.max(3, Math.round((10 + (Number(power)||50)*0.22)*2)/2)
}
function driverImg(code:string){
  const idx = (code.charCodeAt(0) + (code.charCodeAt(1)||0)) % 3
  return ['/media/racer1.png','/media/racer2.png','/media/racer3.png'][idx]
}

export function ConstructorsPage(){
  const {data:allDrivers, isLoading, isError, error} = useDrivers() as any
  const drivers = useMemo(()=> (Array.isArray(allDrivers) ? allDrivers : []) as any[], [allDrivers])
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>(['VER','HAM','LEC','PIA','BOR'])
  const [selectedTeams, setSelectedTeams] = useState<string[]>(['mclaren','ferrari'])
  const [boost, setBoost] = useState<string>('VER')
  const [chip, setChip] = useState<string | null>(null)
  const [predicted, setPredicted] = useState<any>(null)
  const [predError, setPredError] = useState<string|null>(null)

  const driverPrices = useMemo(()=>{
    const m: Record<string,number> = {}
    drivers.forEach((d:any)=> { if(d?.code) m[d.code]=priceForDriver(d) })
    return m
  }, [drivers])
  const teamPower: Record<string, number> = { mercedes:329, mclaren:305, ferrari:278, redbull:185, astonmartin:112, williams:98, racingbulls:67, alpine:62, audi:58, haas:45, cadillac:39 }
  const teamPrices: Record<string, number> = useMemo(()=>{
    const m: Record<string,number>={}
    Object.entries(teamPower).forEach(([id,p])=> m[id]=priceForTeam(p as number))
    return m
  }, [])
  const teamMeta: Record<string,{color:string, name:string}> = {
    mercedes:{color:'#00A19B', name:'Mercedes'}, mclaren:{color:'#FF8000', name:'McLaren'}, ferrari:{color:'#E8002D', name:'Ferrari'},
    redbull:{color:'#3671C6', name:'Red Bull'}, astonmartin:{color:'#229971', name:'Aston Martin'}, williams:{color:'#1E6FCE', name:'Williams'},
    audi:{color:'#BB0A30', name:'Audi'}, alpine:{color:'#0090FF', name:'Alpine'}, haas:{color:'#9198A1', name:'Haas'},
    racingbulls:{color:'#3F5FCC', name:'Racing Bulls'}, cadillac:{color:'#9C7A19', name:'Cadillac'},
  }

  const totalCost = useMemo(()=>{
    const dCost = selectedDrivers.reduce((s,c)=> s + (driverPrices[c]||0), 0)
    const tCost = selectedTeams.reduce((s,c)=> s + (teamPrices[c]||0), 0)
    return Math.round((dCost+tCost)*10)/10
  }, [selectedDrivers, selectedTeams, driverPrices, teamPrices])
  const remaining = Math.round((100 - totalCost)*10)/10

  useEffect(()=>{
    if (!drivers.length) return
    setPredError(null)
    api.post<any>('/api/v1/predictions', { race_id:'au', session_type:'race', simulation_count:1500 }).then(res=>{
      const probs = res.winner_probabilities || {}
      const fantasy: Record<string, number> = {}
      Object.entries(probs).forEach(([code,p])=>{
        const prob = Number(p) || 0
        fantasy[code] = Math.round((prob*25*1.4 + prob*8 + prob*6)*10)/10
      })
      setPredicted(fantasy)
    }).catch((e:any)=> {
      setPredError(e?.message || 'Prediction failed')
      const mock: Record<string,number> = {}
      drivers.slice(0,10).forEach((d:any)=> mock[d.code]= Math.round((Math.random()*20+5)*10)/10)
      setPredicted(mock)
    })
  }, [drivers.length])

  const toggleDriver = (code:string)=>{
    if (selectedDrivers.includes(code)) {
      if (selectedDrivers.length>1) setSelectedDrivers(s=> s.filter(c=> c!==code))
    } else {
      if (selectedDrivers.length<5) setSelectedDrivers(s=> [...s, code])
      else alert('5 drivers max — deselect one first')
    }
  }
  const toggleTeam = (id:string)=>{
    if (selectedTeams.includes(id)) {
      if (selectedTeams.length>1) setSelectedTeams(s=> s.filter(c=> c!==id))
    } else {
      if (selectedTeams.length<2) setSelectedTeams(s=> [...s, id])
      else alert('2 constructors max')
    }
  }

  const valuePicks = useMemo(()=>{
    if (!predicted || !drivers.length) return []
    return drivers.map((d:any)=> ({
      code: d.code, name: d.name, team: d.team_id, color: d.team_color, price: driverPrices[d.code]||10, pred: predicted[d.code]||0,
      ppm: predicted[d.code] ? (predicted[d.code] / (driverPrices[d.code]||10)) : 0
    })).sort((a,b)=> b.ppm - a.ppm).slice(0,8)
  }, [drivers, driverPrices, predicted])

  const fantasyScore = useMemo(()=>{
    if (!predicted) return 0
    const sumDrivers = selectedDrivers.reduce((s,c)=> s + (predicted[c]||0), 0)
    const boostBonus = predicted[boost]||0
    const teamScore = selectedTeams.reduce((s,id)=>{
      const tDrivers = drivers.filter((d:any)=> (d.team_id||'').toLowerCase()===id)
      return s + tDrivers.reduce((a:number,d:any)=> a + (predicted[d.code]||0)*0.6, 0)
    },0)
    const chipMult = chip==='extra_drs' && selectedDrivers.includes(boost) ? (predicted[boost]||0) : 0
    return Math.round((sumDrivers + boostBonus + teamScore + chipMult)*10)/10
  }, [predicted, selectedDrivers, selectedTeams, boost, chip, drivers])

  const bestCaptain = useMemo(()=> valuePicks[0] || null, [valuePicks])
  const bestValue = useMemo(()=> [...valuePicks].sort((a,b)=> b.ppm - a.ppm)[0] || null, [valuePicks])
  const differential = useMemo(()=> drivers.filter((d:any)=> !['VER','HAM','LEC'].includes(d.code)).map((d:any)=> ({code:d.code, pred:predicted?.[d.code]||0, price:driverPrices[d.code]})).sort((a,b)=> b.pred - a.pred)[0] || null, [drivers, predicted, driverPrices])

  if (isError) {
    return <div className="px-4 sm:px-8 py-6"><div className="card p-6 text-red-600">Fantasy data failed: {String((error as any)?.message||error)} <button onClick={()=> window.location.reload()} className="underline">Reload</button></div></div>
  }

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero — Fantasy with budget bar */}
      <div className="card p-0 overflow-hidden">
        <div className="grid lg:grid-cols-5 gap-0">
          <div className="lg:col-span-3 p-6">
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 rounded-full bg-black text-white fs-11 font-bold">FANTASY 2026</span>
              <span className="px-2 py-1 rounded-full fs-11" style={{ background:'#16a34a', color:'#fff'}}>Monte Carlo powered</span>
            </div>
            <h2 className="f1-display text-2xl font-black mt-2">Build your $100M Team</h2>
            <p className="fs-11 text-sub mt-1">5 drivers + 2 constructors · Prices from form, predicted points from simulation — value beats hype. Research: fantasy.formula1.com · FanAmp 2026.</p>
            <div className="mt-4">
              <div className="flex items-center justify-between fs-11 font-bold"><span>Budget</span><span className={`f1-mono ${remaining>=0?'text-green-600':'text-red-600'}`}>{totalCost.toFixed(1)}M / 100M · {remaining>=0? `${remaining.toFixed(1)}M left` : `OVER ${Math.abs(remaining).toFixed(1)}M`}</span></div>
              <div className="w-full h-2 bg-black/10 rounded-full overflow-hidden mt-1">
                <div className="h-full transition-all" style={{ width:`${Math.min(100, totalCost)}%`, background: remaining>=0?'#16a34a':'#ef4444'}} />
              </div>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black">{fantasyScore.toFixed(1)}</div><div className="fs-11">Predicted pts</div></div>
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black">{boost} 2×</div><div className="fs-11">Boost</div></div>
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black">{chip? CHIPS.find(c=>c.id===chip)?.name : '—'}</div><div className="fs-11">Chip</div></div>
            </div>
            {isLoading && <div className="fs-11 text-sub mt-2">Loading drivers…</div>}
            {predError && <div className="fs-11 text-amber-600 mt-1">Prediction fallback: {predError}</div>}
          </div>
          <div className="lg:col-span-2 relative min-h-[280px] bg-black">
            <img src="/media/podium_all.png" alt="Fantasy" className="absolute inset-0 w-full h-full object-cover opacity-60" loading="lazy" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
              <div className="f1-display font-bold">Your Team at a glance</div>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {selectedDrivers.map(c=> {
                  const d = drivers.find((x:any)=> x.code===c)
                  return <span key={c} className="px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1" style={{ background: d?.team_color||'#6b7280', color:'#fff'}}><span className="w-2 h-2 rounded-full bg-white/80" />{c} {driverPrices[c]}M</span>
                })}
                {selectedTeams.map(id=> <span key={id} className="px-2 py-1 rounded-full text-xs font-bold" style={{ background: teamMeta[id]?.color||'#0ea5e9', color:'#fff'}}>{id.toUpperCase()} {teamPrices[id]}M</span>)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scoring explainer */}
      <div className="card p-4">
        <div className="f1-display font-bold">Scoring — 2026 verified · Chips · Strategy</div>
        <div className="grid md:grid-cols-3 gap-3 mt-3 fs-11">
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Qualifying</div><div className="text-sub mt-1">P1 10 → P10 1, P11-20 0, NC -5. Constructors: both Q3 10, both Q2 5, one Q3 3, one Q2 1, both Q1 -1, DSQ -5.</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Race & Sprint</div><div className="text-sub mt-1">Race P1 25→P10 1, DNF -20. Sprint P1 8→P8 1, DNF -10 (halved). Gains +1, overtakes +1, fastest 10 (sprint 5), Driver of Day +10. Constructors = sum drivers.</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Transfers & Prices</div><div className="text-sub mt-1">2 free/GP, 1 carry → max 3, extra -10. Wildcard unlimited (cap kept), Limitless no cap. Tier A &gt;18.5M: ±0.3/0.1, Tier B: ±0.6/0.2 via 3-race PPM. Floor $3M.</div></div>
        </div>
        <div className="flex flex-wrap gap-1.5 mt-3">
          {CHIPS.map(c=> <span key={c.id} className="px-2 py-1 rounded-full text-white fs-11 flex items-center gap-1" style={{ background:c.color}}><span>{c.icon}</span>{c.name} · {c.when}</span>)}
        </div>
      </div>

      {/* Builder — drivers + teams */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card p-4">
          <div className="flex items-center justify-between">
            <div className="f1-display font-bold">Builder — 5 drivers</div>
            <span className="fs-11 px-2 py-1 rounded-full" style={{ background: remaining>=0?'#dcfce7':'#fee2e2', color: remaining>=0?'#16a34a':'#ef4444'}}>{selectedDrivers.length}/5</span>
          </div>
          {drivers.length===0? <div className="p-8 text-center text-sub fs-11">Loading 23 drivers… <a href="http://localhost:5000/api/v1/h2h/drivers" target="_blank" className="underline">API 5000</a></div> :
          <div className="grid sm:grid-cols-2 gap-2 mt-3">
            {drivers.slice(0,23).map((d:any)=>{
              const sel = selectedDrivers.includes(d.code)
              const price = driverPrices[d.code]
              const pred = predicted?.[d.code]
              const isBoost = boost===d.code
              return (
                <button key={d.code} onClick={()=> toggleDriver(d.code)} className={`p-3 rounded-xl border text-left flex items-center gap-3 transition-all ${sel?'bg-green-50 shadow-md scale-[1.01]':'hover:bg-black/5 hover:shadow'}`} style={{ borderColor: sel?'#16a34a':'var(--border)', borderWidth: sel?2:1}}>
                  <img src={driverImg(d.code)} alt={d.code} className="w-10 h-10 rounded-full object-cover border-2" style={{ borderColor: d.team_color}} onError={(e)=> (e.currentTarget.style.display='none')} />
                  <div className="flex-1 min-w-0">
                    <div className="f1-display font-bold text-sm flex items-center gap-1.5"><TeamStripe color={d.team_color} />{d.code} <span className="font-normal text-xs">— {d.name.split(' ').pop()}</span> {isBoost && <span className="px-1.5 py-0.5 rounded bg-black text-white fs-11">2×</span>}</div>
                    <div className="fs-11 text-sub">{d.team_id} · <span className="font-bold" style={{ color: d.team_color}}>{price}M</span> · pred {pred!=null? pred.toFixed(1):'—'} pts · <span style={{ color: pred && pred/price>1.2?'#16a34a':'inherit'}}>PPM {pred!=null? (pred/price).toFixed(2):'—'}</span></div>
                  </div>
                  <span className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold ${sel?'bg-green-600 text-white border-green-600':'bg-white'}`}>{sel?'✓':''}</span>
                </button>
              )
            })}
          </div>
          }
        </div>
        <div className="space-y-4">
          <div className="card p-4">
            <div className="f1-display font-bold">2 Constructors</div>
            <div className="grid gap-2 mt-3">
              {Object.entries(teamPower).map(([id,power])=>{
                const sel = selectedTeams.includes(id)
                const price = teamPrices[id]
                const meta = teamMeta[id]
                return (
                  <button key={id} onClick={()=> toggleTeam(id)} className={`p-3 rounded-xl border flex items-center gap-3 text-left ${sel?'bg-green-50 shadow' : 'hover:bg-black/5'}`} style={{ borderColor: sel?'#16a34a':'var(--border)', borderWidth: sel?2:1}}>
                    <span className="w-2 h-10 rounded-full" style={{ background: meta.color}} />
                    <div className="flex-1">
                      <div className="f1-display font-bold text-sm">{meta.name}</div>
                      <div className="fs-11 text-sub">{power} power · {price}M</div>
                    </div>
                    <span className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${sel?'bg-green-600 text-white border-green-600':'bg-white'}`}>{sel?'✓':''}</span>
                  </button>
                )
              })}
            </div>
          </div>
          <div className="card p-4">
            <div className="f1-display font-bold">Boost & Chip</div>
            <label className="fs-11 font-bold mt-2 block">2× Boost driver
              <select value={boost} onChange={e=> setBoost(e.target.value)} className="f1-select mt-1">
                {selectedDrivers.map(c=> <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-2 mt-3">
              {CHIPS.map(c=> (
                <button key={c.id} onClick={()=> setChip(chip===c.id? null : c.id)} className={`p-2.5 rounded-xl border text-left transition-all ${chip===c.id?'text-white shadow' : 'hover:shadow'}`} style={{ background: chip===c.id? c.color:'#fff', borderColor: chip===c.id? c.color:'var(--border)', color: chip===c.id?'#fff':undefined}}>
                  <div className="fs-11 font-bold flex items-center gap-1">{c.icon} {c.name}</div><div className="fs-11 opacity-80">{c.desc}</div><div className="fs-11 opacity-60">{c.when}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-4 border-l-4" style={{ borderLeftColor:'#16a34a'}}>
          <div className="fs-11 font-bold" style={{ color:'#16a34a'}}>★ BEST CAPTAIN</div>
          <div className="f1-display font-black text-lg">{bestCaptain? `${bestCaptain.code} — ${bestCaptain.name}` : '—'}</div>
          <div className="fs-11 text-sub">{bestCaptain? `${bestCaptain.pred.toFixed(1)} pts · ${bestCaptain.price}M · ${bestCaptain.ppm.toFixed(2)} PPM` : 'Predicted top scorer'}</div>
          <button onClick={()=> bestCaptain && setBoost(bestCaptain.code)} className="btn-primary mt-2 w-full" style={{ background:'#16a34a'}}>Set as Boost 2×</button>
        </div>
        <div className="card p-4 border-l-4" style={{ borderLeftColor:'#0ea5e9'}}>
          <div className="fs-11 font-bold" style={{ color:'#0ea5e9'}}>💎 BEST VALUE</div>
          <div className="f1-display font-black text-lg">{bestValue? `${bestValue.code} — ${bestValue.price}M` : '—'}</div>
          <div className="fs-11 text-sub">{bestValue? `${bestValue.ppm.toFixed(2)} PPM · ${bestValue.pred.toFixed(1)} pts — beats $14.3M avg` : 'Cheapest PPM'}</div>
          <button onClick={()=> bestValue && toggleDriver(bestValue.code)} className="btn-ghost mt-2 w-full">Add to team</button>
        </div>
        <div className="card p-4 border-l-4" style={{ borderLeftColor:'#f59e0b'}}>
          <div className="fs-11 font-bold" style={{ color:'#f59e0b'}}>🚀 DIFFERENTIAL</div>
          <div className="f1-display font-black text-lg">{differential? differential.code : '—'}</div>
          <div className="fs-11 text-sub">{differential? `${differential.pred.toFixed(1)} pts — low owned, high upside` : 'Low owned pick'}</div>
          <button onClick={()=> differential && toggleDriver(differential.code)} className="btn-ghost mt-2 w-full">Add differential</button>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold">Value Picks — PPM Ranking</div>
          <p className="fs-11 text-sub">Points per million — avoids mid-priced trap ($10-18M). Top 8 by PPM.</p>
          {valuePicks.length? <div className="mt-3 space-y-1.5">
            {valuePicks.map((v:any,i:number)=> (
              <div key={v.code} className={`flex items-center gap-2 p-1.5 rounded-lg ${i===0?'bg-green-50 border border-green-200':''}`}>
                <span className="f1-mono w-6 font-bold">{i+1}</span>
                <span className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold" style={{ background: v.color}}>{v.code.slice(0,2)}</span>
                <span className="f1-mono w-10 font-bold">{v.code}</span>
                <span className="fs-11 w-14">{v.price}M</span>
                <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden"><div className="h-full" style={{ width:`${Math.min(100, v.ppm*28)}%`, background: i===0?'#16a34a':'#6b7280'}} /></div>
                <span className="fs-11 w-16 text-right font-bold" style={{ color: i===0?'#16a34a':undefined}}>{v.ppm.toFixed(2)} PPM</span>
                <span className="fs-11 w-14 text-right">{v.pred.toFixed(1)} pts</span>
              </div>
            ))}
          </div> : <div className="fs-11 text-sub mt-3">Predicted points loading…</div>}
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">Predicted Fantasy — Your 7</div>
          {predicted? <F1Chart type="bar" height={240} data={{
            labels: [...selectedDrivers, ...selectedTeams.map(t=> t.toUpperCase())],
            datasets:[{ label:'Predicted pts', data:[...selectedDrivers.map(c=> predicted?.[c]||0), ...selectedTeams.map(id=> {
              const tDrivers = drivers.filter((d:any)=> (d.team_id||'').toLowerCase()===id)
              return tDrivers.reduce((s:number,d:any)=> s + (predicted?.[d.code]||0)*0.6,0)
            })], backgroundColor: [...selectedDrivers.map(c=> drivers.find((d:any)=> d.code===c)?.team_color || '#16a34a'), ...selectedTeams.map(()=> '#0ea5e9')], borderRadius:6 }]
          }} options={{ indexAxis:'y' as const, plugins:{legend:{display:false}}}} /> : <div className="h-[240px] flex items-center justify-center text-sub fs-11">Loading prediction…</div>}
          <div className="fs-11 text-sub mt-2">Monte Carlo win prob → fantasy (quali + race + bonuses) + boost + chip. Stacked 2× = + one copy.</div>
        </div>
      </div>

      <div className="card p-4">
        <div className="f1-display font-bold">Price Change Predictor — Next GP</div>
        <p className="fs-11 text-sub">Tier A {'>'}18.5M: -0.3/-0.1/+0.1/+0.3 · Tier B: -0.6/-0.2/+0.2/+0.6 via 3-race PPM avg. Floor $3M.</p>
        <div className="grid md:grid-cols-3 gap-2 mt-3">
          {valuePicks.slice(0,3).map((v:any)=> (
            <div key={v.code} className="p-3 rounded-lg border flex items-center gap-2" style={{ borderColor:'#16a34a', background:'#dcfce7'}}>
              <span className="text-green-600">↗</span><span className="f1-mono font-bold">{v.code}</span><span className="fs-11">likely +{v.price>18.5?'0.3':'0.6'}M — {v.ppm.toFixed(2)} PPM</span>
            </div>
          ))}
          {[...valuePicks].sort((a,b)=> a.ppm - b.ppm).slice(0,2).map((v:any)=> (
            <div key={v.code} className="p-3 rounded-lg border flex items-center gap-2" style={{ borderColor:'#ef4444', background:'#fee2e2'}}>
              <span className="text-red-600">↘</span><span className="f1-mono font-bold">{v.code}</span><span className="fs-11">risk {v.price>18.5?'-0.3':'-0.6'}M</span>
            </div>
          ))}
        </div>
        <div className="fs-11 text-sub mt-2">Tip: bring rising assets before deadline to grow budget — sell falling before they hit $3M floor.</div>
      </div>
    </div>
  )
}
