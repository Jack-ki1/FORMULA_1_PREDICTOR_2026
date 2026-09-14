export function CircuitSection() {
  return (
    <section className="px-4 sm:px-8 py-10">
      <h2 className="f1-display text-xl font-bold">Circuit Intelligence</h2>
      <p className="text-sub fs-11 mt-1">23 circuits, each with length, DRS zones, overtaking difficulty and base safety-car rain/temp. Data from <code className="f1-mono">backend/app/data/calendar_2026.py</code>.</p>
      <div className="grid md:grid-cols-2 gap-4 mt-6">
        <div className="card overflow-hidden">
          <img src="/media/circuit1.png" alt="Circuit 1" loading="lazy" className="w-full h-56 object-cover" />
          <div className="p-4">
            <div className="f1-display font-bold">Albert Park — Medium Overtaking</div>
            <p className="fs-11 text-sub mt-1">5.278 km · 4 DRS zones · base_sc 55. High-consequence street circuit, safety-car prone.</p>
          </div>
        </div>
        <div className="card overflow-hidden">
          <img src="/media/circuit2.png" alt="Circuit 2" loading="lazy" className="w-full h-56 object-cover" />
          <div className="p-4">
            <div className="f1-display font-bold">Monza — High Overtaking</div>
            <p className="fs-11 text-sub mt-1">5.793 km · 2 DRS zones · Temple of Speed. Slipstream + tyre deg decides.</p>
          </div>
        </div>
      </div>
    </section>
  )
}
