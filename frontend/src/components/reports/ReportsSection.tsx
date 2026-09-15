import { useEffect, useState } from 'react'
import { ShareCardPreview } from './ShareCardPreview'

const FORMATS: Array<{ id: string; title: string; blurb: string; icon: string }> = [
  { id: 'csv', title: 'CSV', blurb: 'Raw probabilities per driver — opens straight into Sheets/Excel.', icon: '📊' },
  { id: 'json', title: 'JSON', blurb: 'Full prediction payload — targets, confidence intervals, drift score.', icon: '🧩' },
  { id: 'pdf', title: 'PDF race sheet', blurb: 'Formatted printable 2026 race sheet (WeasyPrint, Stone 2026 livery).', icon: '📄' },
  { id: 'share', title: 'Share card', blurb: '1080×1080 shareable image with headline prediction, for socials.', icon: '🎴' },
]

export function ReportsSection({ currentRaceId, currentPredictions }: { currentRaceId?: string; currentPredictions?: any }) {
  const [last, setLast] = useState<{ raceId?: string; predictions?: any } | null>(null)
  useEffect(() => {
    const load = () => {
      try {
        const raw = localStorage.getItem('f1-last-prediction')
        if (raw) setLast(JSON.parse(raw))
      } catch {}
    }
    load()
    const handler = () => load()
    window.addEventListener('storage', handler)
    window.addEventListener('f1-prediction', handler as any)
    return () => {
      window.removeEventListener('storage', handler)
      window.removeEventListener('f1-prediction', handler as any)
    }
  }, [])

  // Prefer live Dashboard result over localStorage
  const activeRaceId = currentRaceId || last?.raceId
  const activePredictions = currentPredictions || last?.predictions
  const winner = activePredictions?.winner?.predictions?.[0] || activePredictions?.[Object.keys(activePredictions||{})[0]]?.predictions?.[0]

  return (
    <div className="space-y-6 mt-8 pt-8 border-t" style={{ borderColor: 'var(--border)'}}>
      {/* Anchor header */}
      <div className="flex items-center gap-3">
        <div className="w-1 h-8 rounded-full" style={{ background: 'var(--red)'}} />
        <div>
          <h2 className="f1-display text-xl font-black">Reports — Export Everything</h2>
          <p className="text-sub fs-11">Every format below is served from <code className="f1-mono fs-11">POST /api/v1/reports/export</code>. Your latest Dashboard prediction appears here automatically.</p>
        </div>
      </div>

      {/* Hero - compact variant */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/pit_stop.jpg" alt="Pit stop" loading="lazy" className="w-full h-48 object-cover" />
          <div className="p-5">
            <h3 className="f1-display font-bold">Export from Dashboard</h3>
            <p className="text-sub fs-11 mt-1">Run Monte Carlo above, then export below without leaving the page. Also saved to <code className="f1-mono">localStorage f1-last-prediction</code>.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge">CSV</span><span className="badge">JSON</span><span className="badge">PDF</span><span className="badge">Share Card</span>
            </div>
            {winner && (
              <div className="mt-4 p-3 surface-alt rounded-lg">
                <div className="fs-11 font-bold">Last prediction — {activeRaceId?.toUpperCase() || 'AU'}</div>
                <div className="f1-mono text-sm">Winner: {winner.driver_code} · {(winner.percentage ?? winner.probability*100).toFixed(1)}%</div>
              </div>
            )}
            {!winner && <div className="mt-4 p-3 surface-alt rounded-lg fs-11 text-sub">No prediction yet — hit <strong>Run</strong> above.</div>}
          </div>
        </div>
      </div>

      {/* Formats */}
      <div className="grid sm:grid-cols-2 gap-4">
        {FORMATS.map((f) => (
          <div key={f.id} className="card p-4 group hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl flex items-center justify-center text-xl" style={{ background: 'var(--red)', color:'#fff'}}>{f.icon}</span>
              <div className="f1-display font-bold">{f.title}</div>
              <span className="ml-auto fs-11 px-2 py-1 rounded-full bg-black text-white">{f.id.toUpperCase()}</span>
            </div>
            <p className="text-sub fs-11 mt-2">{f.blurb}</p>
            <div className="mt-3 p-3 rounded-lg bg-black/5 fs-11 font-mono text-xs">
              {f.id==='csv' && 'driver_code,probability,percentage\nVER,0.245,24.5\n...'}
              {f.id==='json' && '{"race_id":"au","predictions":{"winner":[...]}}'}
              {f.id==='pdf' && '<html> F1 race sheet — print me </html>'}
              {f.id==='share' && '1080×1080 PNG — winner + podium + confidence'}
            </div>
          </div>
        ))}
      </div>

      {/* 2026 template mini */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-3 gap-0">
          <img src="/media/podium_all.png" alt="Podium" loading="lazy" className="w-full h-36 object-cover" />
          <div className="p-5 md:col-span-2">
            <div className="f1-display font-bold">2026 Race Sheet — New Template</div>
            <p className="fs-11 text-sub mt-1">Sustainable fuel era, active aero, 30kg lighter. PDF now includes <strong>Straight/Corner mode splits</strong>, <strong>Overtake Mode eligibility</strong>, and <strong>PU deploy map</strong>.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge">Straight Mode</span><span className="badge">Corner Mode</span><span className="badge">Overtake +0.5MJ</span><span className="badge">Boost</span>
            </div>
          </div>
        </div>
      </div>

      {/* Share card preview */}
      <ShareCardPreview raceId={activeRaceId} predictions={activePredictions} />

      {/* How to */}
      <div className="card p-4">
        <div className="f1-display font-bold">How it works</div>
        <ol className="fs-11 text-sub mt-2 list-decimal list-inside space-y-1">
          <li>Pick a Grand Prix above (23 rounds) → Run Monte Carlo</li>
          <li>Prediction auto-saves to <code className="f1-mono">localStorage f1-last-prediction</code> and appears here</li>
          <li>Choose format — <code className="f1-mono">POST /api/v1/reports/export</code> returns <code>csv</code>/<code>pdf</code> as download or <code>json</code>/<code>share</code> as JSON</li>
          <li>PDF uses <code>WeasyPrint</code> (lazy import) — fallback is raw HTML if not installed</li>
        </ol>
        <img src="/media/circuit1.png" alt="Circuit" loading="lazy" className="w-full h-24 object-cover rounded-lg mt-4 opacity-60" />
      </div>
    </div>
  )
}
