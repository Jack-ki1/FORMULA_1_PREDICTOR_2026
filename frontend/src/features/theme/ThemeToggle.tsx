import { usePreferences } from '../preferences/store'
import { Icon } from '../../components/icons/Icon'
import type { ThemeMode } from '../preferences/types'

const MODES: { id: ThemeMode; label: string; icon: any }[] = [
  { id: 'light', label: 'Light', icon: 'sun' },
  { id: 'dark', label: 'Dark', icon: 'moon' },
  { id: 'system', label: 'System', icon: 'monitor' },
]

export function ThemeToggle() {
  const mode = usePreferences((s: any) => s.prefs.appearance.themeMode)
  const setAppearance = usePreferences((s: any) => s.setAppearance)
  const next = () => {
    const idx = MODES.findIndex(m => m.id === mode)
    setAppearance({ themeMode: MODES[(idx + 1) % MODES.length].id })
  }
  const current = MODES.find(m => m.id === mode) || MODES[0]
  return (
    <button onClick={next} className="btn-icon" aria-label={`Theme: ${current.label}. Click to change.`} title={`Theme: ${current.label}`}>
      <Icon name={current.icon} />
    </button>
  )
}
