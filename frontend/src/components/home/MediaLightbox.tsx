import { useState } from 'react'

const GALLERY = [
  { src: '/media/p1.png', label: 'P1' },
  { src: '/media/p2.png', label: 'P2' },
  { src: '/media/p3.png', label: 'P3' },
  { src: '/media/podium_all.png', label: 'Podium' },
  { src: '/media/racer1.png', label: 'Racer 1' },
  { src: '/media/racer2.png', label: 'Racer 2' },
  { src: '/media/racer3.png', label: 'Racer 3' },
  { src: '/media/circuit1.png', label: 'Circuit 1' },
  { src: '/media/circuit2.png', label: 'Circuit 2' },
]

export function MediaLightbox() {
  const [active, setActive] = useState<string | null>(null)
  return (
    <section className="px-4 sm:px-8 py-10">
      <h2 className="f1-display text-xl font-bold">Media — Lightbox Gallery</h2>
      <p className="text-sub fs-11 mt-1">Click any image — 2026 liveries, podiums and circuits. Creative use of <code className="f1-mono">frontend/public/media/*</code> (never proxied from backend).</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mt-6">
        {GALLERY.map((g) => (
          <button key={g.src} onClick={() => setActive(g.src)} className="card overflow-hidden p-0 group text-left">
            <img src={g.src} alt={g.label} loading="lazy" className="w-full h-28 object-cover group-hover:scale-105 transition-transform duration-500" />
            <div className="px-3 py-2 fs-11 font-semibold">{g.label}</div>
          </button>
        ))}
      </div>
      {active && (
        <div onClick={() => setActive(null)} className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 cursor-zoom-out">
          <img src={active} alt="lightbox" className="max-w-full max-h-[85vh] rounded-xl shadow-2xl object-contain" />
        </div>
      )}
    </section>
  )
}
