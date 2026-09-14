export function DuelSection() {
  return (
    <section className="px-4 sm:px-8 py-10">
      <div className="navy-panel rounded-xl p-6 sm:p-8 text-white relative overflow-hidden">
        <div className="grid md:grid-cols-3 gap-6 items-center relative">
          <div className="text-center">
            <img src="/media/racer1.png" alt="Racer A" loading="lazy" className="w-32 h-32 mx-auto rounded-full object-cover border-4 border-white/20 shadow-xl" />
            <div className="f1-display font-bold mt-3">Driver A</div>
            <div className="fs-11" style={{ color: 'rgba(255,255,255,.7)' }}>Pick any two — Elo win probability</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-black" style={{ color: 'var(--red)' }}>VS</div>
            <p className="fs-11 mt-2" style={{ color: 'rgba(255,255,255,.75)' }}>Head-to-head compares strength, wet-skill, consistency — powered by <code className="f1-mono">elo_calculator</code>.</p>
            <a href="/h2h" className="inline-block mt-3 px-4 py-2 bg-white text-black rounded-full fs-11 font-bold">Compare →</a>
          </div>
          <div className="text-center">
            <img src="/media/racer2.png" alt="Racer B" loading="lazy" className="w-32 h-32 mx-auto rounded-full object-cover border-4 border-white/20 shadow-xl" />
            <div className="f1-display font-bold mt-3">Driver B</div>
            <div className="fs-11" style={{ color: 'rgba(255,255,255,.7)' }}>Win probability bar + radar chart</div>
          </div>
        </div>
      </div>
    </section>
  )
}
