const FORMATS: Array<{ id: string; title: string; blurb: string }> = [
  { id: 'csv', title: 'CSV', blurb: 'Raw probabilities per driver — opens straight into Sheets/Excel for your own analysis.' },
  { id: 'json', title: 'JSON', blurb: 'The full prediction payload — targets, confidence intervals, drift score, metadata.' },
  { id: 'pdf', title: 'PDF race sheet', blurb: 'A formatted, printable summary of the prediction (WeasyPrint-rendered).' },
  { id: 'share', title: 'Share card', blurb: 'A shareable image card with the headline prediction, for socials.' },
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
  return (
    <div className="px-4 sm:px-8 py-6">
      <h2 className="f1-display text-xl font-bold">Reports</h2>
      <p className="text-sub fs-11 mt-2 max-w-2xl">
        Exports are generated from a live prediction, so start on the{' '}
        <a href="/app/dashboard" className="text-red" style={{ color: 'var(--red)' }}>Dashboard</a>{' '}
        — run a prediction, then use the Export control at the bottom of the results.
        Every format below is served from the same endpoint:{' '}
        <code className="f1-mono fs-11">POST /api/v1/reports/export</code>.
      </p>
      <div className="grid sm:grid-cols-2 gap-4 mt-6">
        {FORMATS.map((f) => (
          <div key={f.id} className="card p-4">
            <div className="f1-display font-bold">{f.title}</div>
            <p className="text-sub fs-11 mt-1">{f.blurb}</p>
          </div>
        ))}
      </div>
      <div className="mt-6">
        <ShareCardPreview raceId={last?.raceId} predictions={last?.predictions} />
      </div>
    </div>
  )
}
