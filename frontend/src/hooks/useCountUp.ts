import { useEffect, useRef, useState } from 'react'

/**
 * Animates a number from 0 -> value once it scrolls into view (or immediately
 * if used without a ref). Pure CSS/JS, no dependency — mirrors the
 * `animateNumber()` IntersectionObserver pattern from the legacy
 * homepage.html ticker so the React version keeps the same feel.
 */
export function useCountUp(value: number, durationMs = 1200) {
  const [display, setDisplay] = useState(0)
  const ref = useRef<HTMLElement | null>(null)
  const started = useRef(false)

  useEffect(() => {
    const node = ref.current
    if (!node) {
      animate()
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !started.current) {
          started.current = true
          animate()
        }
      },
      { threshold: 0.4 }
    )
    observer.observe(node)
    return () => observer.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  function animate() {
    const start = performance.now()
    function frame(now: number) {
      const progress = Math.min(1, (now - start) / durationMs)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.floor(value * eased))
      if (progress < 1) requestAnimationFrame(frame)
      else setDisplay(value)
    }
    requestAnimationFrame(frame)
  }

  return { display, ref }
}
