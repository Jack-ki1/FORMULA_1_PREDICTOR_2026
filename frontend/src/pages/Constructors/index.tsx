import { useQuery } from '@tanstack/react-query'
import { fetchTeams, fetchPowerRankings } from '../../api/constructors'
import { useDrivers } from '../../hooks/useH2H'
import { TeamStripe } from '../../components/shared/TeamStripe'
import { useState } from 'react'

export function ConstructorsPage(){
  const {data:teams}=useQuery({queryKey:['constructors','teams'], queryFn: fetchTeams})
  const {data:rankings}=useQuery({queryKey:['constructors','power'], queryFn: fetchPowerRankings})
  const {data:allDrivers}=useDrivers()
  const [expanded, setExpanded] = useState<string | null>('mercedes')
  const teamList:any[] = ((teams as any)?.data ?? teams) as any[] || []
  // Enhance with power rankings and driver details
  const enhanced = teamList.map((t:any)=>{
    const id = (t.id||t.team_id||'').toLowerCase()
    const metaPower = (rankings as any)?.find?.((r:any)=> (r.team_id||r.team||'').toLowerCase()===id) || (Array.isArray(rankings)? (rankings as any).find((r:any)=> (r.team||'').toLowerCase()===id) : null)
    return { ...t, power: metaPower?.points || metaPower?.score || 50, form: metaPower?.form || '—' }
  })

  const TEAM_DETAILS: Record<string, any> = {
    mercedes: { full:'Mercedes-AMG Petronas', base:'Brackley, UK', engine:'Mercedes', principal:'Toto Wolff', chassis:'W15', debut:1970, championships:8, wins:125, color:'#00A19B' },
    redbull: { full:'Red Bull Racing', base:'Milton Keynes, UK', engine:'Honda RBPT + Ford', principal:'Christian Horner', chassis:'RB20', debut:2005, championships:6, wins:118, color:'#3671C6' },
    ferrari: { full:'Scuderia Ferrari', base:'Maranello, IT', engine:'Ferrari', principal:'Frédéric Vasseur', chassis:'SF-24', debut:1950, championships:16, wins:243, color:'#E8002D' },
    mclaren: { full:'McLaren F1 Team', base:'Woking, UK', engine:'Mercedes', principal:'Andrea Stella', chassis:'MCL-38', debut:1966, championships:8, wins:183, color:'#FF8000' },
    astonmartin:{ full:'Aston Martin Aramco', base:'Silverstone, UK', engine:'Mercedes → Honda 2026', principal:'Mike Krack', chassis:'AMR24', debut:2018, championships:0, wins:0, color:'#229971' },
    williams:{ full:'Williams Racing', base:'Grove, UK', engine:'Mercedes', principal:'James Vowles', chassis:'FW46', debut:1977, championships:9, wins:114, color:'#1E6FCE' },
    audi:{ full:'Audi F1 Team', base:'Neuburg, DE', engine:'Audi Works 2026', principal:'Andreas Seidl', chassis:'Audi A1', debut:2026, championships:0, wins:0, color:'#BB0A30' },
    alpine:{ full:'BWT Alpine F1 Team', base:'Enstone, UK', engine:'Renault', principal:'Bruno Famin', chassis:'A524', debut:1977, championships:2, wins:21, color:'#0090FF' },
    haas:{ full:'MoneyGram Haas F1 Team', base:'Kannapolis, US', engine:'Ferrari', principal:'Ayao Komatsu', chassis:'VF-24', debut:2016, championships:0, wins:0, color:'#9198A1' },
    racingbulls:{ full:'Racing Bulls', base:'Faenza, IT', engine:'Honda RBPT', principal:'Laurent Mekies', chassis:'RB04', debut:2026, championships:0, wins:0, color:'#3F5FCC' },
    cadillac:{ full:'Cadillac F1 Team', base:'Fishers, US', engine:'Cadillac (GM 2029)', principal:'Graeme Lowdon', chassis:'Cadillac C1', debut:2026, championships:0, wins:0, color:'#9C7A19' },
  }

  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero — TEAMS */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <div className="p-6">
            <h2 className="f1-display text-2xl font-black">TEAMS — 2026 Grid Breakdown</h2>
            <p className="fs-11 text-sub mt-1">11 teams, 22 drivers. Every team deconstructed: heritage, power unit, base, chassis, titles, and its two drivers — accurate to <code className="f1-mono">team_driver_lineup_2026.py</code> & <code>team_data.py</code>. Tap a team to expand.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge" style={{ background:'#BB0A30', color:'#fff'}}>AUDI DEBUT</span>
              <span className="badge" style={{ background:'#9C7A19', color:'#fff'}}>CADILLAC DEBUT</span>
              <span className="badge">11 Teams · 22 Drivers</span>
              <span className="badge">2026 Regs</span>
            </div>
          </div>
          <img src="/media/f1_cartoon.png" alt="Teams" loading="lazy" className="w-full h-56 object-cover" />
        </div>
      </div>

      {/* Teams — creative expandable grid */}
      <div className="space-y-3">
        {enhanced.map((t:any)=>{
          const id = (t.id||t.team_id||'').toLowerCase()
          const det = TEAM_DETAILS[id] || { full: t.name||t.team_id, base:'—', engine:'—', principal:'—', chassis:'—', debut:'—', championships:0, wins:0, color: t.color||'#ccc' }
          const isOpen = expanded===id
          const drivers = (t.drivers||[]).length ? t.drivers : (allDrivers||[]).filter((d:any)=> (d.team_id||'').toLowerCase()===id).slice(0,2)
          return (
            <div key={id} className="card p-0 overflow-hidden">
              {/* Header row */}
              <button onClick={()=> setExpanded(isOpen? null : id)} className="w-full flex items-center gap-4 p-4 text-left hover:bg-black/5 transition-colors">
                <span className="w-1.5 h-12 rounded-full" style={{ background: det.color}} />
                <img src="/media/car_parts.png" alt="car" className="w-16 h-10 object-contain" loading="lazy" />
                <div className="flex-1 min-w-0">
                  <div className="f1-display font-black flex items-center gap-2">{det.full} {['audi','cadillac'].includes(id) && <span className="px-2 py-0.5 rounded-full text-white fs-11 text-[10px]" style={{ background: det.color}}>2026 NEW</span>}</div>
                  <div className="fs-11 text-sub">{det.base} · {det.engine} · {det.chassis} · Debut {det.debut}</div>
                  <div className="fs-11 text-sub mt-0.5">{drivers.map((d:any)=> `${d.code} — ${d.name}`).join(' · ') || '2 drivers'}</div>
                </div>
                <div className="hidden sm:flex flex-col items-end">
                  <span className="f1-mono font-black">{t.points ?? det.wins*3} pts</span>
                  <span className="fs-11 text-sub">{t.form}</span>
                </div>
                <span className="w-8 h-8 rounded-full border flex items-center justify-center" style={{ borderColor:'var(--border)'}}>{isOpen?'−':'+'}</span>
              </button>

              {/* Expanded breakdown */}
              {isOpen && (
                <div className="px-4 pb-4 space-y-4 border-t" style={{ borderColor:'var(--border)'}}>
                  <div className="grid md:grid-cols-3 gap-3 pt-4">
                    <div className="surface-alt p-3 rounded-lg">
                      <div className="fs-11 font-bold">Heritage</div>
                      <div className="fs-11 text-sub mt-1">Titles: {det.championships} · Wins: {det.wins}<br/>Principal: {det.principal}<br/>Base: {det.base}</div>
                    </div>
                    <div className="surface-alt p-3 rounded-lg">
                      <div className="fs-11 font-bold">2026 Power Unit</div>
                      <div className="fs-11 text-sub mt-1">Engine: {det.engine}<br/>Chassis: {det.chassis}<br/>Weight 768kg · Active aero</div>
                    </div>
                    <div className="surface-alt p-3 rounded-lg">
                      <div className="fs-11 font-bold">Power Ranking</div>
                      <div className="f1-mono text-lg font-black" style={{ color: det.color}}>{t.power ?? 50} / 100</div>
                      <div className="fs-11 text-sub">Form: {t.form}</div>
                      <div className="w-full h-1.5 bg-black/10 rounded-full overflow-hidden mt-1"><span className="h-full block" style={{ width:`${t.power||50}%`, background: det.color}} /></div>
                    </div>
                  </div>

                  {/* Drivers — think outside the box: driver duels inside team */}
                  <div className="grid md:grid-cols-2 gap-3">
                    {drivers.map((d:any)=>{
                      const code = d.code
                      const ratio = (d.strength||50)
                      return (
                        <div key={code} className="card p-3 flex gap-3">
                          <div className="w-14 h-14 rounded-full overflow-hidden border-2" style={{ borderColor: det.color}}>
                            <img src={`/media/${code==='NOR'?'racer1': code==='PIA'?'racer2':'racer3'}.png`} alt={code} className="w-full h-full object-cover" onError={(e)=> (e.currentTarget.style.display='none')} />
                            <div className="w-full h-full flex items-center justify-center font-black" style={{ background: det.color, color:'#fff'}}>{code.slice(0,2)}</div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="f1-display font-black flex items-center gap-1.5"><TeamStripe color={det.color} />{d.name} <span className="f1-mono text-xs">#{d.number}</span></div>
                            <div className="fs-11 text-sub">{code} · Strength {d.strength} · Wet {d.wet_skill} · Reliability {d.reliability}</div>
                            <div className="mt-2 flex items-center gap-2">
                              <span className="fs-11 w-12">Pace</span><div className="flex-1 h-1.5 bg-black/10 rounded-full overflow-hidden"><span className="h-full block" style={{ width:`${ratio}%`, background: det.color}} /></div><span className="fs-11 w-8 text-right">{ratio}</span>
                            </div>
                            <div className="mt-1 flex items-center gap-2">
                              <span className="fs-11 w-12">Wet</span><div className="flex-1 h-1.5 bg-black/10 rounded-full overflow-hidden"><span className="h-full block" style={{ width:`${d.wet_skill||50}%`, background:'#0ea5e9'}} /></div><span className="fs-11 w-8 text-right">{d.wet_skill||50}</span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                    {drivers.length===0 && <div className="fs-11 text-sub col-span-2 p-3 surface-alt rounded-lg">No roster — see <code className="f1-mono">/api/v1/constructors/teams</code></div>}
                  </div>

                  {/* Creative extras: team vs team mini chart + facts */}
                  <div className="grid md:grid-cols-2 gap-3">
                    <div className="surface-alt p-3 rounded-lg">
                      <div className="fs-11 font-bold">Team DNA — 2026</div>
                      <ul className="fs-11 text-sub mt-1 list-disc list-inside space-y-0.5">
                        <li>Active aero: Straight (low drag) vs Corner (high downforce) — every lap</li>
                        <li>Overtake Mode: +0.5MJ within 1s to 337 km/h</li>
                        <li>50/50 PU: 400kW ICE + 350kW electric, sustainable fuel</li>
                      </ul>
                    </div>
                    <div className="surface-alt p-3 rounded-lg">
                      <div className="fs-11 font-bold">What to watch</div>
                      <div className="fs-11 text-sub mt-1">
                        {id==='mercedes'?'Can Antonelli tame the 768kg mule and keep Mercedes on top?':
                         id==='ferrari'?'Hamilton in red — LEC vs HAM internal duel defines Ferrari 2026.':
                         id==='mclaren'?'Defending champs — papaya must handle active aero better than Works.':
                         id==='audi'?'Debut year — Audi Works PU vs customer Mercedes teams.':
                         id==='cadillac'?'American entry — Cadillac C1 with Bose graces the grid.':
                         'Midfield hinges on active aero execution — 0.3s swings per lap.'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
