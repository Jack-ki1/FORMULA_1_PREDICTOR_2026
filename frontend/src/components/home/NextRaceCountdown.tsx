import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRaces } from '../../hooks/useRaces'
import type { Race } from '../../types'

function timeParts(msRemaining: number) {
  const clamped = Math.max(0, msRemaining)
  const totalSeconds = Math.floor(clamped / 1000)
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
  }
}

/** Live countdown to the next non-cancelled race, driven by real /api/v1/races data. */
export function NextRaceCountdown() {
  const { data: races, isLoading } = useRaces()
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const nextRace: Race | undefined = useMemo(() => {
    if (!races) return undefined
    return races
      .filter((r) => r.status !== 'cancelled' && new Date(r.date).getTime() >= Date.now())
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())[0]
  }, [races])

  if (isLoading) {
    return <div className="hp-countdown card p-4"><span className="text-sub fs-11">Loading race calendar…</span></div>
  }
  if (!nextRace) {
    return null
  }

  const { days, hours, minutes, seconds } = timeParts(new Date(nextRace.date).getTime() - now)
  const cell = (value: number, label: string) => (
    <div className="hp-countdown-cell">
      <span className="hp-countdown-value f1-mono">{String(value).padStart(2, '0')}</span>
      <span className="hp-countdown-label">{label}</span>
    </div>
  )

  return (
    <Link to="/dashboard" className="hp-countdown card p-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <span className="fs-11 text-sub">Up next · Round {nextRace.round}</span>
          <div className="f1-display font-bold text-base mt-1">
            {nextRace.flag} {nextRace.name}
          </div>
          <span className="fs-11 text-muted">{nextRace.circuit}, {nextRace.location}</span>
        </div>
        <div className="hp-countdown-grid">
          {cell(days, 'DAYS')}
          {cell(hours, 'HRS')}
          {cell(minutes, 'MIN')}
          {cell(seconds, 'SEC')}
        </div>
      </div>
    </Link>
  )
}
