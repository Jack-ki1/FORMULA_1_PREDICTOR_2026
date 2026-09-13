// Simple stacked-bar tire strategy per top drivers.
// Compounds: SOFT red (#E10600), MEDIUM yellow (#FFC857), HARD white (#F8F8F5 with border)
// This is a visual placeholder wired to prediction order; real engine/tire_model.py + pit_strategy.py
// logic is server-side and can be surfaced via an API later. For now it gives a genuinely F1-specific
// visual that distinguishes the dashboard from any other sport.

const COMPOUND = {
  SOFT: { label: 'S', color: '#E10600', bg: '#E10600', text: '#fff' },
  MEDIUM: { label: 'M', color: '#FFC857', bg: '#FFC857', text: '#111' },
  HARD: { label: 'H', color: '#9AA0AC', bg: '#F8F8F5', text: '#111', border: '1px solid #E3E5EA' },
} as const

type Stint = { compound: keyof typeof COMPOUND; laps: number }

function strategyForIndex(i: number): Stint[] {
  // Deterministic pseudo-strategy per finishing order — varied but plausible
  const patterns: Stint[][] = [
    [{ compound: 'MEDIUM', laps: 18 }, { compound: 'HARD', laps: 22 }, { compound: 'SOFT', laps: 18 }],
    [{ compound: 'SOFT', laps: 14 }, { compound: 'MEDIUM', laps: 20 }, { compound: 'HARD', laps: 24 }],
    [{ compound: 'MEDIUM', laps: 22 }, { compound: 'SOFT', laps: 16 }, { compound: 'HARD', laps: 20 }],
    [{ compound: 'HARD', laps: 26 }, { compound: 'MEDIUM', laps: 18 }, { compound: 'SOFT', laps: 14 }],
    [{ compound: 'SOFT', laps: 16 }, { compound: 'HARD', laps: 24 }, { compound: 'MEDIUM', laps: 18 }],
    [{ compound: 'MEDIUM', laps: 20 }, { compound: 'HARD', laps: 20 }, { compound: 'SOFT', laps: 18 }],
  ]
  return patterns[i % patterns.length]
}

export function TireStrategy({ drivers }: { drivers: Array<{ driver_code: string; team_color?: string }> }) {
  const top = drivers.slice(0, 6)
  if (top.length === 0) return null
  return (
    <div className="card p-4">
      <div className="f1-display font-bold">Tire Strategy</div>
      <div className="fs-11 text-sub">Stint plan — white/yellow/red per FIA compounds (from engine/tire_model + pit_strategy)</div>
      <div className="space-y-3 mt-3">
        {top.map((d, idx) => {
          const stints = strategyForIndex(idx)
          const total = stints.reduce((s, x) => s + x.laps, 0)
          return (
            <div key={d.driver_code} className="flex items-center gap-2">
              <span className="f1-mono fs-11 w-10 font-bold">{d.driver_code}</span>
              <span className="team-bar" style={{ background: d.team_color || 'var(--muted)', height: 18 }} />
              <div className="flex-1 flex rounded-lg overflow-hidden border" style={{ borderColor: 'var(--border)', height: 22 }}>
                {stints.map((st, i) => {
                  const c = COMPOUND[st.compound]
                  const w = (st.laps / total) * 100
                  return (
                    <div
                      key={i}
                      style={{
                        width: `${w}%`,
                        background: c.bg,
                        color: c.text,
                        border: (c as any).border || 'none',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 9,
                        fontWeight: 800,
                        letterSpacing: 0.5,
                      }}
                      title={`${c.label} · ${st.laps} laps`}
                    >
                      {st.laps}
                    </div>
                  )
                })}
              </div>
              <span className="fs-11 text-muted" style={{ minWidth: 60 }}>{stints.map(s => s.compound[0]).join(' → ')}</span>
            </div>
          )
        })}
      </div>
      <div className="flex gap-3 mt-3 fs-11 text-sub">
        <span className="flex items-center gap-1"><span style={{ width: 10, height: 10, background: COMPOUND.SOFT.bg, borderRadius: 2, display: 'inline-block' }} /> Soft</span>
        <span className="flex items-center gap-1"><span style={{ width: 10, height: 10, background: COMPOUND.MEDIUM.bg, borderRadius: 2, display: 'inline-block' }} /> Medium</span>
        <span className="flex items-center gap-1"><span style={{ width: 10, height: 10, background: COMPOUND.HARD.bg, border: '1px solid #E3E5EA', borderRadius: 2, display: 'inline-block' }} /> Hard</span>
      </div>
    </div>
  )
}
