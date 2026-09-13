import { useEffect, useState } from 'react'

/**
 * The five red F1 start lights: illuminate one at a time, hold, then cut out
 * together ("lights out and away we go") before looping. Purely decorative,
 * zero dependencies — sits in the hero next to the CTA buttons.
 */
export function StartLights() {
  const [lit, setLit] = useState(0) // 0..5 lights lit; 6 = "lights out" frame

  useEffect(() => {
    let step = 0
    let timer: ReturnType<typeof setTimeout>
    const sequence = () => {
      if (step <= 5) {
        setLit(step)
        step++
        timer = setTimeout(sequence, step === 6 ? 900 : 420)
      } else {
        setLit(6) // lights out
        step = 0
        timer = setTimeout(sequence, 1600)
      }
    }
    timer = setTimeout(sequence, 500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="hp-start-lights" role="img" aria-label="Formula 1 start lights sequence">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={`hp-start-light ${lit >= n && lit < 6 ? 'is-lit' : ''}`} />
      ))}
    </div>
  )
}
