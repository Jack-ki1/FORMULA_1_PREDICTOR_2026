import { Link } from 'react-router-dom'
import { useRaces } from '../../hooks/useRaces'
import { useCountUp } from '../../hooks/useCountUp'
import { StartLights } from '../../components/home/StartLights'
import { NextRaceCountdown } from '../../components/home/NextRaceCountdown'
import { useState, useEffect } from 'react'
import { api } from '../../api/client'

function Stat({ value, suffix = '', label }: { value: number; suffix?: string; label: string }) {
  const { display, ref } = useCountUp(value)
  return (
    <div className="hp-stat" ref={ref as any}>
      <span className="hp-stat-value f1-display">{display.toLocaleString()}{suffix}</span>
      <span className="hp-stat-label fs-11">{label}</span>
    </div>
  )
}

// Research-backed 2026 regs data (FIA + Formula1.com, June 2024 + March 2026)
const REGS_2026 = [
  { tag:'ACTIVE AERO', title:'Straight vs Corner', desc:'Front wing + rear wing move together. Open on straights (low drag) → closed in corners (high downforce). Every lap, every car.', detail:'Drag -55% · Downforce -30% · Front element + rear top element drop' },
  { tag:'PU 50/50', title:'400kW ICE + 350kW ELEC', desc:'MGU-H deleted. MGU-K nearly 3× to 350kW. Battery recharges 4MJ → 8MJ+ per lap — automated + lift-off regen.', detail:'1.6L V6 turbo · 50% electrical · ~1000hp total · FIA net-zero fuel' },
  { tag:'SUSTAINABLE FUEL', title:'100% Advanced', desc:'Drop-in fuel from carbon capture, municipal waste, non-food biomass — not fossil. Independently certified >90% CO₂ cut.', detail:'No refuelling · Fuel flow limited by energy not mass · FIA assurance scheme' },
  { tag:'SMALLER & LIGHTER', title:'768kg · 3400mm · 1900mm', desc:'-30kg, -200mm wheelbase, -100mm width. Front tyres -25mm, rear -30mm. Nimbler, closer racing.', detail:'Ground-effect flat floor · 6 PU manufacturers · $130m cost cap (was $95m)' },
]

const MINI_PREVIEW_RACES = [
  { id:'au', name:'Melbourne', fav:'ANT 32%', bar:32, color:'#00A19B' },
  { id:'mc', name:'Monaco', fav:'LEC 28%', bar:28, color:'#E8002D' },
  { id:'sg', name:'Singapore', fav:'NOR 31%', bar:31, color:'#FF8000' },
  { id:'jp', name:'Suzuka', fav:'VER 29%', bar:29, color:'#3671C6' },
]

export function HomePage() {
  const { data: races } = useRaces()
  const raceCount = races?.filter((r) => r.status !== 'cancelled').length ?? 23
  const [previewId, setPreviewId] = useState('au')
  const [liveNews, setLiveNews] = useState<any[]>([])
  useEffect(()=>{
    api.get<any>('/api/v1/news').then(r=> setLiveNews(r.news?.slice(0,3)||[])).catch(()=>{})
  },[])

  return (
    <div>
      {/* ---------- HERO — Monaco video ---------- */}
      <section className="hp-hero relative overflow-hidden">
        <video autoPlay muted loop playsInline preload="metadata" poster="/media/night_race.webp" className="hp-hero-video absolute inset-0 w-full h-full object-cover" aria-hidden="true">
          <source src="/media/F1_monaco.mp4" type="video/mp4" />
        </video>
        <img src="/media/night_race.webp" alt="" className="hp-hero-poster-fallback absolute inset-0 w-full h-full object-cover" aria-hidden="true" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black/80" aria-hidden="true" />
        <div className="hp-hero-grid-bg" aria-hidden="true" />
        <div className="hp-hero-glow" aria-hidden="true" />
        <div className="px-4 sm:px-8 py-16 sm:py-24 relative">
          <span className="hp-kicker fs-11" style={{ color: 'rgba(255,255,255,.9)' }}>2026 SEASON · AI RACE INTELLIGENCE — ACTIVE AERO · 50/50 PU</span>
          <h1 className="hp-title f1-display" style={{ color: '#fff' }}>
            F1 PREDICTOR <span style={{ color: 'var(--red)' }}>2026</span>
          </h1>
          <p className="hp-subtitle" style={{ color: 'rgba(255,255,255,.85)' }}>
            Monte-Carlo simulation, Elo duels and optional AI — built on a real engine, not a guess. 30% less downforce, 55% less drag.
          </p>
          <div className="flex flex-wrap items-center gap-3 mt-6">
            <Link to="/dashboard" className="btn-primary">Open Dashboard</Link>
            <Link to="/standings" className="btn-ghost" style={{ borderColor: 'rgba(255,255,255,.3)', color: '#fff' }}>View Standings</Link>
            <StartLights />
          </div>
          <div className="mt-8 max-w-md">
            <NextRaceCountdown />
          </div>
        </div>
      </section>

      <div className="hp-checkered" aria-hidden="true" />

      {/* ---------- STAT TICKER — keep, then everything below is reimagined ---------- */}
      <section className="px-4 sm:px-8 py-8">
        <div className="hp-stat-row">
          <Stat value={raceCount} label="RACES THIS SEASON" />
          <Stat value={23} label="DRIVERS MODELLED" />
          <Stat value={11} label="TEAMS" />
          <Stat value={10000} suffix="+" label="SIMULATIONS PER RACE" />
        </div>
      </section>

      {/* ========== NEW: Cinematic Dusk Break — uses the OTHER video ========== */}
      <section className="relative overflow-hidden" style={{ minHeight:'420px'}}>
        <video autoPlay muted loop playsInline preload="metadata" poster="/media/sunset_race.webp" className="hp-hero-video absolute inset-0 w-full h-full object-cover" aria-hidden="true">
          <source src="/media/Formula_One_race_at_dusk_1.mp4" type="video/mp4" />
        </video>
        <img src="/media/sunset_race.webp" alt="" className="hp-hero-poster-fallback absolute inset-0 w-full h-full object-cover" aria-hidden="true" />
        <div className="absolute inset-0" style={{ background:'linear-gradient(90deg, rgba(10,12,16,0.88) 0%, rgba(10,12,16,0.55) 55%, rgba(10,12,16,0.75) 100%)'}} aria-hidden="true" />
        <div className="relative px-4 sm:px-8 py-12 sm:py-16 grid lg:grid-cols-2 gap-8 items-center">
          <div>
            <span className="fs-11 font-bold tracking-widest" style={{ color:'#FF3B30'}}>DUSK TO DUST — THE OTHER SIDE OF 2026</span>
            <h2 className="f1-display text-3xl font-black mt-2" style={{ color:'#fff'}}>Not just faster. <span style={{ color:'var(--red)'}}>Different.</span></h2>
            <p className="fs-11 mt-3 max-w-xl" style={{ color:'rgba(255,255,255,.82)'}}>
              At dusk the straight-mode wings flatten — less drag, more harvesting. Lift off and you recharge but lose aero. Every straight is now a decision. This is why the simulation matters: 768kg, 50/50 PU, sustainable fuel — the same car behaves differently at 340 km/h with Mode Override armed.
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <span className="px-3 py-1 rounded-full text-white fs-11 font-bold" style={{ background:'var(--red)'}}>Straight Mode = open</span>
              <span className="px-3 py-1 rounded-full text-white fs-11" style={{ background:'rgba(255,255,255,.14)'}}>Corner Mode = closed</span>
              <span className="px-3 py-1 rounded-full text-white fs-11" style={{ background:'rgba(255,255,255,.14)'}}>Overtake +0.5MJ within 1s → 337 km/h</span>
            </div>
            <Link to="/dashboard" className="inline-block mt-5 px-5 py-2 rounded-full font-bold text-sm" style={{ background:'#fff', color:'#0a0a09'}}>Try the 2026 model →</Link>
          </div>
          <div className="relative">
            <div className="card p-0 overflow-hidden" style={{ background:'rgba(255,255,255,0.96)'}}>
              <div className="p-4 flex items-center justify-between">
                <span className="f1-display font-black">Mode Override</span>
                <span className="px-2 py-1 rounded-full text-white fs-11 font-bold" style={{ background:'#16a34a'}}>350kW</span>
              </div>
              <div className="px-4 pb-4 grid grid-cols-2 gap-3 fs-11">
                <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Battery</div><div className="text-sub">4MJ → 8MJ+ per lap. Automated + lift-off regen (disables aero).</div></div>
                <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Fuel</div><div className="text-sub">100% Advanced Sustainable — drop-in, no fossil carbon added.</div></div>
                <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Weight</div><div className="text-sub">768kg (-30kg). Wheelbase 3400mm (-200mm).</div></div>
                <div className="surface-alt p-3 rounded-lg"><div className="font-bold">Cost cap PU</div><div className="text-sub">$130m (was $95m). Six manufacturers.</div></div>
              </div>
              <div className="px-4 pb-4 fs-11 text-sub">Research: FIA 2026 Technical Regs issue 18, Formula1.com 12 changes — verified June 2024 & March 2026.</div>
            </div>
          </div>
        </div>
      </section>

      {/* ========== Regulation Atlas — 4 cards, research-backed ========== */}
      <section className="px-4 sm:px-8 py-10">
        <div className="flex items-center gap-3 mb-2">
          <span className="w-1.5 h-6 rounded-full" style={{ background:'var(--red)'}} />
          <h2 className="f1-display text-xl font-bold">2026 Regulation Atlas — what you’re watching</h2>
        </div>
        <p className="text-sub fs-11 max-w-2xl">Not marketing — FIA document. Tap any card to see why your prediction shifts.</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
          {REGS_2026.map(r=> (
            <div key={r.tag} className="card p-4 group hover:shadow-xl hover:-translate-y-1 transition-all">
              <span className="badge-purple">{r.tag}</span>
              <div className="f1-display font-black mt-3">{r.title}</div>
              <p className="fs-11 text-sub mt-1">{r.desc}</p>
              <div className="mt-3 p-2 rounded-lg surface-alt fs-11 text-sub">{r.detail}</div>
              <Link to="/dashboard" className="inline-block mt-3 fs-11 font-bold" style={{ color:'var(--red)'}}>Simulate this →</Link>
            </div>
          ))}
        </div>
      </section>

      {/* ========== Prediction Playground — live mini predictor ========== */}
      <section className="px-4 sm:px-8 py-8">
        <div className="navy-panel p-6 rounded-xl">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="f1-display text-xl font-bold" style={{ color:'#fff'}}>Prediction Playground — a preview of the format</h2>
            <span className="px-3 py-1 rounded-full bg-white text-black fs-11 font-bold">Illustrative · 4 races</span>
          </div>
          <div className="grid lg:grid-cols-[240px_1fr] gap-4 mt-5">
            <div className="space-y-2">
              {MINI_PREVIEW_RACES.map(r=> (
                <button key={r.id} onClick={()=> setPreviewId(r.id)} className={`w-full text-left p-3 rounded-lg flex items-center gap-3 ${previewId===r.id?'bg-white text-black':'bg-white/10 text-white hover:bg-white/20'}`}>
                  <span className="w-2 h-8 rounded-full" style={{ background: r.color}} />
                  <div><div className="f1-display font-bold text-sm">{r.name}</div><div className="fs-11 opacity-70">{r.fav} favourite</div></div>
                  <span className="ml-auto f1-mono text-xs font-black">{r.bar}%</span>
                </button>
              ))}
              <Link to="/dashboard" className="btn-primary w-full text-center mt-2" style={{ background:'#fff', color:'#0a0a09'}}>Open full Dashboard</Link>
            </div>
            <div className="card p-4" style={{ background:'#fff', color:'#0a0a09'}}>
              <div className="f1-display font-bold">Mini win-prob — {MINI_PREVIEW_RACES.find(r=> r.id===previewId)?.name}</div>
              <div className="space-y-2 mt-3">
                {MINI_PREVIEW_RACES.map(r=> {
                  // deterministic variance based on race id hash, not Math.random
                  const hash = r.id.split('').reduce((a,c)=> a + c.charCodeAt(0),0) % 6
                  const otherBar = Math.max(6, r.bar - 8 + hash)
                  return (
                    <div key={r.id} className="flex items-center gap-2">
                      <span className="fs-11 w-6 font-bold">{r.id.toUpperCase()}</span>
                      <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden"><div className="h-full" style={{ width:`${previewId===r.id? r.bar : otherBar}%`, background: r.color}} /></div>
                      <span className="fs-11 w-10 text-right">{r.bar}%</span>
                    </div>
                  )
                })}
              </div>
              <div className="fs-11 text-sub mt-3">Sample numbers to show the format — open the <Link to="/dashboard" className="underline" style={{ color:'var(--red)'}}>Dashboard</Link> to run the real Monte Carlo engine on live data.</div>
            </div>
          </div>
        </div>
      </section>

      {/* ========== Team Voyage — horizontal car strip ========== */}
      <section className="px-4 sm:px-8 py-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="w-1.5 h-6 rounded-full" style={{ background:'var(--red)'}} />
          <h2 className="f1-display text-xl font-bold">Team Voyage — 11 liveries, one grid</h2>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-2 snap-x" style={{ scrollbarWidth:'thin'}}>
          {[
            { id:'mercedes', name:'Mercedes', color:'#00A19B', note:'Petronas · Antonelli / Russell' },
            { id:'redbull', name:'Red Bull', color:'#3671C6', note:'Honda RBPT + Ford · Verstappen / Hadjar' },
            { id:'ferrari', name:'Ferrari', color:'#E8002D', note:'Hamilton in red · LEC / HAM' },
            { id:'mclaren', name:'McLaren', color:'#FF8000', note:'Defending champs · NOR / PIA' },
            { id:'astonmartin', name:'Aston Martin', color:'#229971', note:'Honda 2026 · ALO / STR' },
            { id:'audi', name:'Audi', color:'#BB0A30', note:'2026 DEBUT · HUL / BOR' },
            { id:'cadillac', name:'Cadillac', color:'#9C7A19', note:'2026 DEBUT · PER / BOT' },
          ].map(t=> (
            <Link key={t.id} to="/teams" className="card p-3 min-w-[180px] snap-start hover:shadow-lg transition-shadow">
              <div className="h-1 rounded-full" style={{ background: t.color}} />
              <img src="/media/car_parts.webp" alt={t.name} className="w-full h-14 object-contain mt-2" loading="lazy" />
              <div className="f1-display font-black text-sm mt-2">{t.name}</div>
              <div className="fs-11 text-sub">{t.note}</div>
            </Link>
          ))}
        </div>
        <Link to="/teams" className="inline-block mt-3 fs-11 font-bold" style={{ color:'var(--red)'}}>Explore all 11 teams →</Link>
      </section>

      {/* ========== Intelligence in Motion — numbers + news teaser ========== */}
      <section className="px-4 sm:px-8 py-8">
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="card p-4">
            <div className="f1-display font-bold">Intelligence in motion</div>
            <div className="grid grid-cols-3 gap-3 mt-3">
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black" style={{ color:'var(--red)'}}>23</div><div className="fs-11">Rounds</div></div>
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black" style={{ color:'var(--red)'}}>50/50</div><div className="fs-11">PU split</div></div>
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black" style={{ color:'var(--red)'}}>768kg</div><div className="fs-11">Min weight</div></div>
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black">30%</div><div className="fs-11">Less downforce</div></div>
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black">55%</div><div className="fs-11">Less drag</div></div>
              <div className="surface-alt p-3 rounded-lg text-center"><div className="f1-mono text-lg font-black">6</div><div className="fs-11">PU makers</div></div>
            </div>
            <Link to="/analytics" className="inline-block mt-3 fs-11 font-bold" style={{ color:'var(--red)'}}>How the engine works →</Link>
          </div>
          <div className="card p-4">
            <div className="f1-display font-bold">Live from the paddock</div>
            <div className="space-y-2 mt-3">
              {liveNews.length? liveNews.map((n:any,i:number)=> (
                <a key={i} href={n.url} target="_blank" rel="noreferrer" className="flex gap-3 p-2 rounded-lg hover:bg-black/5 transition-colors">
                  <img src={n.image||'/media/circuit1.webp'} alt="" className="w-16 h-12 object-cover rounded" loading="lazy" />
                  <div className="min-w-0"><div className="fs-11 font-bold line-clamp-1">{n.title}</div><div className="fs-11 text-sub line-clamp-1">{n.source} · {n.date}</div></div>
                </a>
              )) : <div className="fs-11 text-sub p-4 text-center">Loading news via <code className="f1-mono">/api/v1/news</code>…</div>}
            </div>
            <Link to="/analytics" className="inline-block mt-3 fs-11 font-bold" style={{ color:'var(--red)'}}>More news & analytics →</Link>
          </div>
        </div>
      </section>

      {/* ========== CTA Section ========== */}
      <section className="px-4 sm:px-8 pb-10">
        <div className="card p-6 text-center" style={{ background:'linear-gradient(135deg, #0a0a09, #16233F)', color:'#fff'}}>
          <h2 className="f1-display text-xl font-black">Your grid, your conditions, your call.</h2>
          <p className="fs-11 mt-2" style={{ color:'rgba(255,255,255,.8)'}}>The 2026 regs reward those who read the straight. Run the simulation and see.</p>
          <Link to="/dashboard" className="inline-block mt-4 px-6 py-2 rounded-full font-bold" style={{ background:'var(--red)', color:'#fff'}}>Run a prediction</Link>
        </div>
      </section>
    </div>
  )
}
