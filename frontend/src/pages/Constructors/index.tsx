import { useState, useMemo, useEffect } from 'react'
import { useDrivers } from '../../hooks/useH2H'
import { TeamStripe } from '../../components/shared/TeamStripe'
import { F1Chart } from '../../components/charts/F1Chart'
import { api } from '../../api/client'

// Research: F1 Fantasy 2026 — $100M cap, 5 drivers + 2 constructors, price floor $3M, DNF -20 (sprint -10), chip set
const CHIPS = [
  { id:'wildcard', name:'Wildcard', desc:'Unlimited free transfers within budget', when:'Once per season' },
  { id:'limitless', name:'Limitless', desc:'No budget cap + unlimited transfers for one GP — team reverts after', when:'Once' },
  { id:'extra_drs', name:'Extra DRS', desc:'3× driver boost (stacks with 2×)', when:'Once' },
  { id:'no_negative', name:'No Negative', desc:'All negatives set to 0', when:'Once' },
  { id:'autopilot', name:'Autopilot', desc:'Top scorer becomes captain automatically', when:'Once' },
  { id:'final_fix', name:'Final Fix', desc:'Change one driver after qualifying', when:'Once' },
]

function priceForDriver(d:any): number {
  // Synthesize price from strength: 3 + strength*0.27 → ~6-30M, matches 2026 tiering
  const base = 3 + (d.strength||50)*0.27
  return Math.round(base*2)/2 // 0.5 steps
}
function priceForTeam(power:number): number {
  return Math.max(3, Math.round((10 + power*0.22)*2)/2)
}

export function ConstructorsPage(){
  const {data:allDrivers} = useDrivers()
  const drivers = (allDrivers||[]) as any[]
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>(['VER','HAM','LEC','PIA','BOR'])
  const [selectedTeams, setSelectedTeams] = useState<string[]>(['mclaren','ferrari'])
  const [boost, setBoost] = useState<string>('VER')
  const [chip, setChip] = useState<string | null>(null)
  const [budget, setBudget] = useState<number>(100)
  const [predicted, setPredicted] = useState<any>(null)

  // Prices
  const driverPrices = useMemo(()=>{
    const m: Record<string,number> = {}
    drivers.forEach(d=> m[d.code]=priceForDriver(d))
    return m
  }, [drivers])
  const teamPower: Record<string, number> = { mercedes:329, mclaren:305, ferrari:278, redbull:185, astonmartin:112, williams:98, racingbulls:67, alpine:62, audi:58, haas:45, cadillac:39 }
  const teamPrices: Record<string, number> = useMemo(()=>{
    const m: Record<string,number>={}
    Object.entries(teamPower).forEach(([id,p])=> m[id]=priceForTeam(p as number))
    return m
  }, [])

  const totalCost = useMemo(()=>{
    const dCost = selectedDrivers.reduce((s,c)=> s + (driverPrices[c]||0), 0)
    const tCost = selectedTeams.reduce((s,c)=> s + (teamPrices[c]||0), 0)
    return Math.round((dCost+tCost)*10)/10
  }, [selectedDrivers, selectedTeams, driverPrices, teamPrices])
  const remaining = Math.round((budget - totalCost)*10)/10

  // Predicted fantasy points via Monte Carlo (when available) or fallback
  useEffect(()=>{
    if (!selectedDrivers.length) return
    // Try live Monte Carlo for next race (au) to estimate fantasy points
    api.post<any>('/api/v1/predictions', { race_id:'au', session_type:'race', simulation_count:2000 }).then(res=>{
      const probs = res.winner_probabilities || {}
      // Map win prob to fantasy race points + bonuses
      const fantasy: Record<string, number> = {}
      Object.entries(probs).forEach(([code,p])=>{
        const prob = p as number
        // Race points ~ prob*25 scaled + qualifying + bonuses
        const race = prob*25*1.4 // inflate for fantasy
        const quali = prob*8 // pole 10
        const bonus = prob*6 // overtakes/fastest
        fantasy[code] = Math.round((race+quali+bonus)*10)/10
      })
      setPredicted(fantasy)
    }).catch(()=> setPredicted(null))
  }, [selectedDrivers.join(',')])

  const toggleDriver = (code:string)=>{
    if (selectedDrivers.includes(code)) {
      if (selectedDrivers.length>1) setSelectedDrivers(s=> s.filter(c=> c!==code))
    } else {
      if (selectedDrivers.length<5) setSelectedDrivers(s=> [...s, code])
      else alert('5 drivers max')
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
    if (!predicted) return []
    return drivers.map(d=> ({
      code: d.code, name: d.name, team: d.team_id, price: driverPrices[d.code], pred: predicted[d.code]||0,
      ppm: predicted[d.code] ? (predicted[d.code] / (driverPrices[d.code]||1)) : 0
    })).sort((a,b)=> b.ppm - a.ppm).slice(0,6)
  }, [drivers, driverPrices, predicted])

  const fantasyScore = useMemo(()=>{
    if (!predicted) return 0
    const sumDrivers = selectedDrivers.reduce((s,c)=> s + (predicted[c]||0), 0)
    const boostBonus = predicted[boost]||0 // 2× means add one more copy
    const teamScore = selectedTeams.reduce((s,id)=>{
      // team fantasy = sum of its drivers' predicted
      const teamDrivers = drivers.filter(d=> (d.team_id||'').toLowerCase()===id)
      return s + teamDrivers.reduce((a,d)=> a + (predicted[d.code]||0)*0.6, 0)
    },0)
    const chipMult = chip==='extra_drs' && selectedDrivers.includes(boost) ? 1 : 0 // 3× is + one extra copy
    return Math.round((sumDrivers + boostBonus + teamScore + chipMult*(predicted[boost]||0))*10)/10
  }, [predicted, selectedDrivers, selectedTeams, boost, chip, drivers])

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero — Fantasy */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <div className="p-6">
            <h2 className="f1-display text-2xl font-black">FANTASY — 2026 Helper</h2>
            <p className="fs-11 text-sub mt-1">Plan your $100M team: 5 drivers + 2 constructors. Prices from form, predicted points from our Monte Carlo — not tips, but value. Research: <code className="f1-mono">fantasy.formula1.com</code> + FanAmp scoring 2026.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge">$100M cap</span><span className="badge">5+2</span><span className="badge">Floor $3M</span><span className="badge">DNF -20 (sprint -10)</span><span className="badge">6 chips</span>
            </div>
            <div className="mt-4 p-3 rounded-lg flex items-center justify-between" style={{ background: remaining>=0?'#dcfce7':'#fee2e2', border:'1px solid #16a34a'}}>
              <span className="fs-11 font-bold">Budget</span><span className="f1-mono font-black">{totalCost.toFixed(1)}M / {budget}M {remaining>=0? `· ${remaining.toFixed(1)}M left` : `· OVER by ${Math.abs(remaining).toFixed(1)}M`}</span>
            </div>
            <div className="mt-2 f1-mono text-sm font-black">Predicted fantasy: {fantasyScore.toFixed(1)} pts {boost && `· Boost: ${boost} 2×`} {chip? `· Chip: ${chip}`:''}</div>
          </div>
          <img src="/media/f1_cartoon.png" alt="Fantasy" loading="lazy" className="w-full h-56 object-cover" />
        </div>
      </div>

      {/* Scoring explainer — accurate 2026 */}
      <div className="card p-4">
        <div className="f1-display font-bold">How scoring works — 2026 (verified)</div>
        <div className="grid md:grid-cols-3 gap-3 mt-3 fs-11">
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Qualifying</div><div className="text-sub mt-1">P1 10, P2 9 … P10 1, P11-20 0, NC -5. Constructors: both Q3 10, both Q2 5, one Q3 3, one Q2 1, both Q1 -1, DSQ -5 per driver.</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Race</div><div className="text-sub mt-1">P1 25, P2 18, P3 15 … P10 1, 11-22 0, DNF/DSQ/NC -20. Constructors = sum of drivers. Positions gained +1 per place, Overtakes +1 (clean), Fastest Lap +10, Driver of Day +10.</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Sprint</div><div className="text-sub mt-1">P1 8 … P8 1, 9-20 0, DNF -10 (was -20, halved 2026). Gains/losses ±1, overtakes +1, fastest 5.</div></div>
        </div>
        <div className="grid md:grid-cols-2 gap-3 mt-3 fs-11">
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Chips (6)</div><div className="text-sub mt-1">{CHIPS.map(c=> `${c.name} — ${c.desc} (${c.when})`).join(' · ')}</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Strategy</div><div className="text-sub mt-1">Top drivers ~28-30M, cheap $3-6M. Average $14.3M/slot. Constructors {'>'} drivers for value when top team has 2 strong drivers. Budget +10 pts per extra transfer beyond 2 free (1 carry). Prices change via PPM after each GP.</div></div>
        </div>
      </div>

      {/* Builder */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card p-4">
          <div className="f1-display font-bold">Builder — 5 drivers</div>
          <div className="grid sm:grid-cols-2 gap-2 mt-3">
            {drivers.slice(0,23).map(d=>{
              const sel = selectedDrivers.includes(d.code)
              const price = driverPrices[d.code]
              const pred = predicted?.[d.code]
              return (
                <button key={d.code} onClick={()=> toggleDriver(d.code)} className={`p-3 rounded-lg border text-left flex items-center gap-3 ${sel?'border-green-600 bg-green-50':'hover:bg-black/5'}`} style={{ borderColor: sel?'#16a34a':'var(--border)'}}>
                  <span className="w-8 h-8 rounded-full flex items-center justify-center font-black text-white text-xs" style={{ background: d.team_color}}>{d.code.slice(0,2)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="f1-display font-bold text-sm">{d.code} — {d.name}</div>
                    <div className="fs-11 text-sub">{d.team_id} · {price}M · pred {pred? pred.toFixed(1):'—'} pts · PPM {pred? (pred/price).toFixed(2):'—'}</div>
                  </div>
                  <span className={`w-5 h-5 rounded-full border flex items-center justify-center ${sel?'bg-green-600 text-white border-green-600':'bg-white'}`}>{sel?'✓':''}</span>
                </button>
              )
            })}
          </div>
        </div>
        <div className="space-y-4">
          <div className="card p-4">
            <div className="f1-display font-bold">2 Constructors</div>
            <div className="grid gap-2 mt-3">
              {Object.entries(teamPower).map(([id,power])=>{
                const sel = selectedTeams.includes(id)
                const price = teamPrices[id]
                return (
                  <button key={id} onClick={()=> toggleTeam(id)} className={`p-3 rounded-lg border flex items-center gap-2 ${sel?'border-green-600 bg-green-50':''}`}>
                    <span className="w-2 h-8 rounded-full" style={{ background: ({mercedes:'#00A19B', redbull:'#3671C6', ferrari:'#E8002D', mclaren:'#FF8000', astonmartin:'#229971', williams:'#1E6FCE', audi:'#BB0A30', alpine:'#0090FF', haas:'#9198A1', racingbulls:'#3F5FCC', cadillac:'#9C7A19'} as any)[id]||'#ccc'}} />
                    <span className="f1-display font-bold text-sm flex-1 text-left">{id.toUpperCase()}</span>
                    <span className="fs-11">{price}M</span>
                    <span className={`w-5 h-5 rounded-full border flex items-center justify-center ${sel?'bg-green-600 text-white':''}`}>{sel?'✓':''}</span>
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
                <button key={c.id} onClick={()=> setChip(chip===c.id? null : c.id)} className={`p-2 rounded-lg border text-left ${chip===c.id?'bg-black text-white':''}`}>
                  <div className="fs-11 font-bold">{c.name}</div><div className="fs-11 opacity-70">{c.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Value picks + Predicted plot */}
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="f1-display font-bold">Value Picks — PPM (predicted / price)</div>
          <p className="fs-11 text-sub">Best points per million — cheap drivers with upside beat mid-priced ($10-18M) trap. Avg $14.3M/slot.</p>
          <div className="mt-3 space-y-1">
            {valuePicks.map(v=> (
              <div key={v.code} className="flex items-center gap-2">
                <span className="f1-mono w-10 font-bold">{v.code}</span>
                <span className="fs-11 w-16">{v.price}M</span>
                <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden"><div className="h-full" style={{ width:`${Math.min(100, v.ppm*30)}%`, background:'#16a34a'}} /></div>
                <span className="fs-11 w-16 text-right">{v.ppm.toFixed(2)} PPM</span>
                <span className="fs-11 w-14 text-right">{v.pred.toFixed(1)} pts</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-4">
          <div className="f1-display font-bold">Predicted Fantasy — Your team</div>
          <F1Chart type="bar" height={220} data={{
            labels: [...selectedDrivers, ...selectedTeams.map(t=> t.toUpperCase())],
            datasets:[{ label:'Predicted pts', data:[...selectedDrivers.map(c=> predicted?.[c]||0), ...selectedTeams.map(id=> {
              const teamDrivers = drivers.filter(d=> (d.team_id||'').toLowerCase()===id)
              return teamDrivers.reduce((s,d)=> s + (predicted?.[d.code]||0)*0.6,0)
            })], backgroundColor: [...selectedDrivers.map(c=> drivers.find(d=> d.code===c)?.team_color || '#16a34a'), ...selectedTeams.map(()=> '#0ea5e9')], borderRadius:4 }]
          }} options={{ indexAxis:'y' as const}} />
          <div className="fs-11 text-sub mt-2">Powered by Monte Carlo win prob → fantasy scoring (quali + race + bonuses). Use chips to time big moves — Limitless removes cap for one GP.</div>
        </div>
      </div>

      <div className="card p-4">
        <div className="f1-display font-bold">Plan — Transfers & Price Changes</div>
        <div className="grid md:grid-cols-3 gap-3 mt-3 fs-11">
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Transfers</div><div className="text-sub">2 free per GP, 1 carry → max 3. Net basis — revert without cost. Extra = -10 pts. Wildcard = unlimited free (keep cap), Limitless = no cap + unlimited (reverts next week).</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Price changes</div><div className="text-sub">Tier A {'>'}18.5M: -0.3/-0.1/+0.1/+0.3 · Tier B {'<'}18.5M: -0.6/-0.2/+0.2/+0.6 via 3-race avg PPM. Floor $3M (was $4.5M). Predict via budget builder tooltip.</div></div>
          <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Next step</div><div className="text-sub">Lock before qualifying. Set Boost to predicted top scorer. Save team — then compare predicted vs actual at <code className="f1-mono">/standings</code>.</div></div>
        </div>
      </div>
    </div>
  )
}
