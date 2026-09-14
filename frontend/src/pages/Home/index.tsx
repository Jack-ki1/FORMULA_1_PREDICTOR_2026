import { Link } from 'react-router-dom'
import { useRaces } from '../../hooks/useRaces'
import { useCountUp } from '../../hooks/useCountUp'
import { StartLights } from '../../components/home/StartLights'
import { NextRaceCountdown } from '../../components/home/NextRaceCountdown'
import { RaceWeekendSection } from '../../components/home/RaceWeekendSection'
import { GarageSection } from '../../components/home/GarageSection'
import { MediaLightbox } from '../../components/home/MediaLightbox'
import { DuelSection } from '../../components/home/DuelSection'
import { CircuitSection } from '../../components/home/CircuitSection'

function Stat({ value, suffix = '', label }: { value: number; suffix?: string; label: string }) {
  const { display, ref } = useCountUp(value)
  return (
    <div className="hp-stat" ref={ref as any}>
      <span className="hp-stat-value f1-display">{display.toLocaleString()}{suffix}</span>
      <span className="hp-stat-label fs-11">{label}</span>
    </div>
  )
}

const ICONS = {
  dashboard: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="M7 15l3-4 3 3 5-7" /></svg>
  ),
  standings: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 21V9M14 21V3M20 21v-6M4 21v-3" /></svg>
  ),
  h2h: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="7" cy="8" r="3" /><circle cx="17" cy="8" r="3" /><path d="M2 21c0-3 2.5-5 5-5s5 2 5 5M12 21c0-3 2.5-5 5-5s5 2 5 5" /></svg>
  ),
  constructors: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 17h18M5 17l1.5-6h11L19 17M9 11V7h6v4" /><circle cx="7.5" cy="19" r="1.5" /><circle cx="16.5" cy="19" r="1.5" /></svg>
  ),
  analytics: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z" /><path d="M21.2 8.4A10 10 0 0 0 15.6 2.8v5.6h5.6z" /></svg>
  ),
  reports: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M9 13h6M9 17h6" /></svg>
  ),
}

const FEATURES: Array<{ to: string; icon: keyof typeof ICONS; title: string; blurb: string }> = [
  { to: '/dashboard', icon: 'dashboard', title: 'Prediction Dashboard', blurb: 'Pick a Grand Prix and session, tune the grid, and run the Monte Carlo engine live.' },
  { to: '/standings', icon: 'standings', title: 'Standings', blurb: "Live driver and constructor standings for the 2026 season, with fallback to season data." },
  { to: '/h2h', icon: 'h2h', title: 'Head-to-Head', blurb: 'Compare any two drivers — Elo-derived win probability, reversed and ranked.' },
  { to: '/constructors', icon: 'constructors', title: 'Constructors', blurb: 'Team power rankings and full 2026 lineups, car by car.' },
  { to: '/analytics', icon: 'analytics', title: 'Analytics & Settings', blurb: 'Model accuracy tracking, feature-weight tuning, and target calibration.' },
  { to: '/reports', icon: 'reports', title: 'Reports', blurb: 'Export any prediction as CSV, JSON, a PDF race sheet, or a shareable card.' },
]

export function HomePage() {
  const { data: races } = useRaces()
  const raceCount = races?.filter((r) => r.status !== 'cancelled').length ?? 24

  return (
    <div>
      {/* ---------- HERO — video background creatively using public/media ---------- */}
      <section className="hp-hero relative overflow-hidden">
        <video
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          poster="/media/night_race.png"
          className="absolute inset-0 w-full h-full object-cover"
          aria-hidden="true"
        >
          <source src="/media/F1_monaco.mp4" type="video/mp4" />
          <source src="/media/Formula_One_race_at_dusk_1.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black/80" aria-hidden="true" />
        <div className="hp-hero-grid-bg" aria-hidden="true" />
        <div className="hp-hero-glow" aria-hidden="true" />
        <div className="px-4 sm:px-8 py-16 sm:py-24 relative">
          <span className="hp-kicker fs-11" style={{ color: 'rgba(255,255,255,.9)' }}>2026 SEASON · AI RACE INTELLIGENCE — ACTIVE AERO · 50/50 PU</span>
          <h1 className="hp-title f1-display" style={{ color: '#fff' }}>
            F1 PREDICTOR <span style={{ color: 'var(--red)' }}>2026</span>
          </h1>
          <p className="hp-subtitle" style={{ color: 'rgba(255,255,255,.85)' }}>
            Monte-Carlo race simulation, Elo-based head-to-heads and an optional AI layer —
            built on a real prediction engine, not a guess. 30% less downforce, 55% less drag.
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

      {/* ---------- CHECKERED DIVIDER ---------- */}
      <div className="hp-checkered" aria-hidden="true" />

      {/* ---------- STAT TICKER ---------- */}
      <section className="px-4 sm:px-8 py-8">
        <div className="hp-stat-row">
          <Stat value={raceCount} label="RACES THIS SEASON" />
          <Stat value={20} label="DRIVERS MODELLED" />
          <Stat value={10} label="CONSTRUCTORS" />
          <Stat value={10000} suffix="+" label="SIMULATIONS PER RACE" />
        </div>
      </section>

      {/* ---------- FEATURE GRID ---------- */}
      <section className="px-4 sm:px-8 py-6">
        <h2 className="f1-display text-xl font-bold">Everything the engine can tell you</h2>
        <p className="text-sub fs-11 mt-1">Six views onto the same prediction engine — pick where you want to start.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
          {FEATURES.map((f) => (
            <Link key={f.to} to={f.to} className="card p-4 hp-feature-card">
              <span className="hp-feature-icon">{ICONS[f.icon]}</span>
              <div className="f1-display font-bold mt-3">{f.title}</div>
              <p className="text-sub fs-11 mt-1">{f.blurb}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* ---------- HOW IT WORKS ---------- */}
      <section className="px-4 sm:px-8 py-10">
        <div className="navy-panel p-6 sm:p-8 rounded-xl text-white">
          <h2 className="f1-display text-xl font-bold">How a prediction gets made</h2>
          <div className="grid sm:grid-cols-3 gap-6 mt-6">
            <div className="hp-step">
              <span className="hp-step-number f1-mono">01</span>
              <div className="f1-display font-bold mt-2">Build the grid</div>
              <p className="fs-11 mt-1" style={{ color: 'rgba(255,255,255,.75)' }}>
                Race, qualifying or practice — pull the real 2026 calendar, weather and starting grid, or set it manually.
              </p>
            </div>
            <div className="hp-step">
              <span className="hp-step-number f1-mono">02</span>
              <div className="f1-display font-bold mt-2">Run the simulation</div>
              <p className="fs-11 mt-1" style={{ color: 'rgba(255,255,255,.75)' }}>
                Thousands of Monte Carlo laps factor in safety-car odds, chaos level and driver/team strength — with an optional AI adjustment layered on top.
              </p>
            </div>
            <div className="hp-step">
              <span className="hp-step-number f1-mono">03</span>
              <div className="f1-display font-bold mt-2">Read the odds</div>
              <p className="fs-11 mt-1" style={{ color: 'rgba(255,255,255,.75)' }}>
                Calibrated win, podium and points probabilities, with confidence intervals and drift detection — export it or take it to the grid editor.
              </p>
            </div>
          </div>
        </div>
      </section>

      <RaceWeekendSection />
      <GarageSection />
      <MediaLightbox />
      <DuelSection />
      <CircuitSection />
    </div>
  )
}
