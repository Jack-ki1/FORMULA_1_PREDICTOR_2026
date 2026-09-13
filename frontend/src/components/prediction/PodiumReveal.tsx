import { useEffect, useMemo, useState } from 'react'

const CONFETTI_COLORS = ['var(--red)', 'var(--amber)', 'var(--green)', 'var(--purple)', '#ffffff']

export function PodiumReveal({ trigger, label }: { trigger?: string; label?: string }) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (!trigger) return
    setShow(true)
    const t = setTimeout(() => setShow(false), 2200)
    return () => clearTimeout(t)
  }, [trigger])

  const pieces = useMemo(
    () =>
      Array.from({ length: 28 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.4,
        duration: 1.4 + Math.random() * 0.8,
        color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
        rotate: Math.round(Math.random() * 360),
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [trigger]
  )

  if (!show) return null

  return (
    <div className="podium-reveal" aria-live="polite">
      {pieces.map((p) => (
        <span
          key={p.id}
          className="podium-confetti"
          style={
            {
              left: `${p.left}%`,
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`,
              background: p.color,
              '--r': `${p.rotate}deg`,
            } as React.CSSProperties
          }
        />
      ))}
      {label && <div className="podium-reveal-label f1-display">🏆 {label} — predicted P1</div>}
    </div>
  )
}
