export function RaceWeekendSection() {
  return (
    <section className="px-4 sm:px-8 py-10">
      <div className="flex items-center gap-3 mb-4">
        <span className="w-1.5 h-6 bg-red rounded-full" style={{ background: 'var(--red)' }} />
        <h2 className="f1-display text-xl font-bold">Race Weekend — Every Session Matters</h2>
      </div>
      <p className="text-sub fs-11 max-w-2xl">Friday practice → Saturday qualifying → Sunday race. The engine models each session differently: practice pace (FP1 0.95×), qualifying pressure (Q1 0.9×, Q3 1.1×), race chaos & safety-car.</p>
      <div className="grid md:grid-cols-3 gap-4 mt-6">
        <div className="card overflow-hidden group">
          <img src="/media/car_parts.png" alt="Car parts" loading="lazy" className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-500" />
          <div className="p-4">
            <div className="f1-display font-bold text-sm">Friday — Practice</div>
            <p className="fs-11 text-sub mt-1">FP1/FP2/FP3 pace models. Tyre deg, fuel-corrected lap times. Use it to spot who’s hiding pace.</p>
            <span className="inline-block mt-2 fs-11 font-semibold" style={{ color: 'var(--red)' }}>FP1 0.95× · FP2 1.00× · FP3 1.05× →</span>
          </div>
        </div>
        <div className="card overflow-hidden group">
          <img src="/media/f1_simulation.png" alt="Simulation" loading="lazy" className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-500" />
          <div className="p-4">
            <div className="f1-display font-bold text-sm">Saturday — Qualifying</div>
            <p className="fs-11 text-sub mt-1">GridModel with Q1/Q2/Q3 pressure. Manual P1-22 overrides auto grid — the grid is the race.</p>
            <span className="inline-block mt-2 fs-11 font-semibold" style={{ color: 'var(--red)' }}>Q1 0.9× · Q2 1.0× · Q3 1.1× →</span>
          </div>
        </div>
        <div className="card overflow-hidden group">
          <img src="/media/pit_stop.jpg" alt="Pit stop" loading="lazy" className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-500" />
          <div className="p-4">
            <div className="f1-display font-bold text-sm">Sunday — Race</div>
            <p className="fs-11 text-sub mt-1">Monte Carlo 100-100k laps, safety-car (base_sc +10 wet), chaos smoothing to uniform, AI blend optional.</p>
            <span className="inline-block mt-2 fs-11 font-semibold" style={{ color: 'var(--red)' }}>Winner sums to 1.00 →</span>
          </div>
        </div>
      </div>
    </section>
  )
}
