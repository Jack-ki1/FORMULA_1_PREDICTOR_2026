const FORMATS: Array<{ id: string; title: string; blurb: string; icon: string }> = [
  { id: 'csv', title: 'CSV', blurb: 'Raw probabilities per driver — opens straight into Sheets/Excel for your own analysis.', icon: '📊' },
  { id: 'json', title: 'JSON', blurb: 'The full prediction payload — targets, confidence intervals, drift score, metadata.', icon: '🧩' },
  { id: 'pdf', title: 'PDF race sheet', blurb: 'A formatted, printable 2026 race sheet (WeasyPrint, Stone 2026 livery).', icon: '📄' },
  { id: 'share', title: 'Share card', blurb: 'A 1080×1080 shareable image with headline prediction, for socials.', icon: '🎴' },
]

import { useEffect, useState } from 'react'
import { ShareCardPreview } from '../../components/reports/ShareCardPreview'

export function ReportsPage() {
  const [last, setLast] = useState<{ raceId?: string; predictions?: any } | null>(null)
  useEffect(() => {
    try {
      const raw = localStorage.getItem('f1-last-prediction')
      if (raw) setLast(JSON.parse(raw))
    } catch {}
    const handler = () => {
      try {
        const r = localStorage.getItem('f1-last-prediction')
        if (r) setLast(JSON.parse(r))
      } catch {}
    }
    window.addEventListener('storage', handler)
    window.addEventListener('f1-prediction', handler as any)
    return () => {
      window.removeEventListener('storage', handler)
      window.removeEventListener('f1-prediction', handler as any)
    }
  }, [])
  const winner = last?.predictions?.winner?.predictions?.[0] || last?.predictions?.[Object.keys(last?.predictions||{})[0]]?.predictions?.[0]
  return (
    <div className="px-4 sm:px-8 py-6 space-y-6">
      {/* Hero */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/pit_stop.jpg" alt="Pit stop" loading="lazy" className="w-full h-56 object-cover" />
          <div className="p-6">
            <h2 className="f1-display text-2xl font-black">Reports — Export Everything</h2>
            <p className="text-sub fs-11 mt-1">Every format below is served from the same endpoint <code className="f1-mono fs-11">POST /api/v1/reports/export</code>. Run a prediction on the <a href="/dashboard" className="underline" style={{ color: 'var(--red)'}}>Dashboard</a> first — then it appears here automatically via <code className="f1-mono">localStorage f1-last-prediction</code>.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge">CSV</span><span className="badge">JSON</span><span className="badge">PDF</span><span className="badge">Share Card</span><span className="badge">2026 Template</span>
            </div>
            {winner && (
              <div className="mt-4 p-3 surface-alt rounded-lg">
                <div className="fs-11 font-bold">Last prediction — {last?.raceId?.toUpperCase() || 'AU'}</div>
                <div className="f1-mono text-sm">Winner: {winner.driver_code} · {(winner.percentage ?? winner.probability*100).toFixed(1)}%</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Formats — well organized grid with icons and previews */}
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

      {/* 2026 template */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-3 gap-0">
          <img src="/media/podium_all.png" alt="Podium" loading="lazy" className="w-full h-48 object-cover" />
          <div className="p-6 md:col-span-2">
            <div className="f1-display font-bold">2026 Race Sheet — New Template</div>
            <p className="fs-11 text-sub mt-1">Sustainable fuel era, active aero, 30kg lighter. PDF now includes <strong>Straight/Corner mode splits</strong>, <strong>Overtake Mode eligibility</strong>, and <strong>PU deploy map</strong> (400kW ICE + 350kW elec). Print it, take it to the grandstand.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="badge">Straight Mode</span><span className="badge">Corner Mode</span><span className="badge">Overtake +0.5MJ</span><span className="badge">Boost</span>
            </div>
          </div>
        </div>
      </div>

      {/* Share card preview */}
      <div className="card p-4">
        <div className="f1-display font-bold mb-2">Share Card Preview — 1080×1080</div>
        <p className="fs-11 text-sub">Powered by <code className="f1-mono">reports/share_card_generator.py</code> → <code className="f1-mono">html2canvas</code> on the client. Uses your last prediction from <code className="f1-mono">localStorage</code>.</p>
        <div className="mt-4">
          <ShareCardPreview raceId={last?.raceId} predictions={last?.predictions} />
        </div>
      </div>

      {/* How to */}
      <div className="card p-4">
        <div className="f1-display font-bold">How it works</div>
        <ol className="fs-11 text-sub mt-2 list-decimal list-inside space-y-1">
          <li>Go to <a href="/dashboard" className="underline">Dashboard</a> → pick a Grand Prix (23 rounds, 6 sprint) → Run Monte Carlo</li>
          <li>Prediction auto-saves to <code className="f1-mono">localStorage f1-last-prediction</code> and appears here</li>
          <li>Choose format above — `POST /api/v1/reports/export` returns `csv`/`pdf` as StreamingResponse (download) or `json`/`share` as JSON</li>
          <li>PDF uses `WeasyPrint` (lazy import, needs `libpango` in Docker) — fallback is raw HTML `text/html` if not installed</li>
        </ol>
        <img src="/media/circuit1.png" alt="Circuit" loading="lazy" className="w-full h-32 object-cover rounded-lg mt-4 opacity-60" />
      </div>
    </div>
  )
}
