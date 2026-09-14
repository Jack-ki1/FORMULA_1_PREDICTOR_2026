export function GarageSection() {
  return (
    <section className="px-4 sm:px-8 py-10">
      <div className="grid md:grid-cols-2 gap-6 items-center">
        <div>
          <h2 className="f1-display text-xl font-bold">Inside the Garage</h2>
          <p className="text-sub fs-11 mt-2">11 teams, 22 drivers, 23 circuits. Every car rendered with team-accurate colours from <code className="f1-mono">backend/app/config/constants.py:TEAM_COLORS</code>. The garage is where strength, wet-skill and reliability live.</p>
          <div className="grid grid-cols-2 gap-3 mt-4">
            <div className="card p-3">
              <div className="fs-11 font-bold">Strength</div>
              <div className="fs-11 text-sub">Pace + driver form, 0-100. Powers Monte Carlo.</div>
            </div>
            <div className="card p-3">
              <div className="fs-11 font-bold">Wet Skill</div>
              <div className="fs-11 text-sub">Rain modifier, 0-100. Wet weather reshuffles the grid.</div>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <img src="/media/f1_cartoon.png" alt="F1 cartoon" loading="lazy" className="rounded-xl object-cover h-48 w-full shadow-lg" />
          <img src="/media/sunset_race.png" alt="Sunset race" loading="lazy" className="rounded-xl object-cover h-48 w-full shadow-lg" />
          <img src="/media/night_race.png" alt="Night race" loading="lazy" className="rounded-xl object-cover h-40 w-full shadow-lg col-span-2" />
        </div>
      </div>
    </section>
  )
}
