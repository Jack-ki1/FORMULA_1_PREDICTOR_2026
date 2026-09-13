import { useState } from 'react'
import { api } from '../../api/client'

export function ShareCardPreview({ raceId, predictions }: { raceId?: string; predictions?: any }) {
  const [url, setUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    if (!predictions || !raceId) return
    setLoading(true)
    try {
      // POST /api/v1/reports/export with format share returns an image blob
      const res = await fetch(`/api/v1/reports/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ race_id: raceId, session: 'race', format: 'share', predictions }),
      })
      if (!res.ok) throw new Error('Failed')
      const blob = await res.blob()
      setUrl(URL.createObjectURL(blob))
    } catch (e) {
      // fallback: try via api client (may return blob)
      try {
        const blob = await api.post<Blob>(`/api/v1/reports/export`, { race_id: raceId, session: 'race', format: 'share', predictions })
        // api client may have parsed as json, so try object URL from response if possible
        if (blob instanceof Blob) setUrl(URL.createObjectURL(blob))
      } catch {}
    } finally {
      setLoading(false)
    }
  }

  const copy = async () => {
    if (!url) return
    try {
      const res = await fetch(url)
      const blob = await res.blob()
      await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })])
      alert('Image copied')
    } catch {
      // fallback share
      if (navigator.share && url) {
        // fetch as file
        const r = await fetch(url)
        const b = await r.blob()
        const file = new File([b], 'f1-share.png', { type: b.type })
        // @ts-ignore
        await navigator.share({ files: [file], title: 'F1 Prediction' }).catch(()=>{})
      }
    }
  }

  if (!predictions) {
    return (
      <div className="card p-4">
        <div className="f1-display font-bold">Share Card</div>
        <p className="fs-11 text-sub mt-1">Run a prediction on the Dashboard first — then generate a shareable image here.</p>
        <div className="empty-state mt-3 p-6 text-muted">No prediction yet</div>
      </div>
    )
  }

  return (
    <div className="card p-4">
      <div className="f1-display font-bold">Share Card</div>
      <p className="fs-11 text-sub">Preview the WeasyPrint/Pillow share image (from reports/share_card_generator.py) + copy or native share.</p>
      <div className="flex gap-2 mt-3">
        <button onClick={generate} disabled={loading} className="btn-primary">{loading ? 'Generating…' : 'Generate Preview'}</button>
        {url && <button onClick={copy} className="btn-ghost">Copy image</button>}
        {url && <a href={url} download={`f1-${raceId}-share.png`} className="btn-ghost">Download</a>}
      </div>
      {url && <img src={url} alt="Share card" className="mt-4 rounded-lg border" style={{ borderColor: 'var(--border)', maxWidth: '100%' }} />}
    </div>
  )
}
