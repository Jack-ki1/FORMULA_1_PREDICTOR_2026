import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

// Real, working keyboard navigation — "g" then a letter jumps to a section,
// matching the reference table shown in Settings > Keyboard Shortcuts.
// Ignored while focus is in a text input/select/textarea/contentEditable so it
// never interferes with typing.
const ROUTES: Record<string, string> = {
  h: '/', d: '/dashboard', s: '/standings', v: '/h2h', f: '/fantasy', g: '/guide', t: '/settings',
}

export function useGlobalShortcuts(enabled: boolean) {
  const navigate = useNavigate()
  useEffect(() => {
    if (!enabled) return
    let waitingForSecond = false
    let timer: ReturnType<typeof setTimeout> | null = null

    const isTyping = (el: EventTarget | null) => {
      const t = el as HTMLElement | null
      if (!t) return false
      const tag = t.tagName?.toLowerCase()
      return tag === 'input' || tag === 'textarea' || tag === 'select' || t.isContentEditable
    }

    const onKeyDown = (e: KeyboardEvent) => {
      if (isTyping(e.target) || e.metaKey || e.ctrlKey || e.altKey) return
      const key = e.key.toLowerCase()
      if (waitingForSecond) {
        waitingForSecond = false
        if (timer) clearTimeout(timer)
        const path = ROUTES[key]
        if (path) { e.preventDefault(); navigate(path) }
        return
      }
      if (key === 'g') {
        waitingForSecond = true
        timer = setTimeout(() => { waitingForSecond = false }, 900)
      } else if (key === '?') {
        navigate('/settings#shortcuts')
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => { window.removeEventListener('keydown', onKeyDown); if (timer) clearTimeout(timer) }
  }, [enabled, navigate])
}
