import { Outlet, Link } from 'react-router-dom'
import { TopNavigation } from '../navigation/TopNavigation'
import { ThemeProvider } from '../../features/theme/ThemeProvider'
import { RaceLoadingBar } from '../shared/RaceLoadingBar'
import { useGlobalShortcuts } from '../../features/shortcuts/useGlobalShortcuts'
import { useRaceReminders } from '../../features/notifications/useRaceReminders'
import { usePreferences } from '../../features/preferences/store'

function Shell() {
  const shortcutsEnabled = usePreferences((s: any) => s.prefs.advanced.keyboardShortcuts)
  useGlobalShortcuts(shortcutsEnabled)
  useRaceReminders()
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopNavigation />
      <RaceLoadingBar />
      <main style={{ flex: 1 }}><Outlet /></main>
      <footer className="f1-footer px-4 sm:px-8 py-6 mt-8 border-t" style={{ borderColor: 'var(--border)' }}>
        <div className="flex flex-wrap items-center justify-between gap-2 fs-11 text-sub">
          <span>&copy; 2026 F1 Predictor. Predictions are modelled estimates, not betting advice.</span>
          <div className="flex items-center gap-3">
            <Link to="/guide" className="hover:underline">Guide</Link>
            <Link to="/settings" className="hover:underline">Settings</Link>
            <span className="f1-mono">Season 2026 · Model v1.0</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export function AppShell() {
  return (
    <ThemeProvider>
      <Shell />
    </ThemeProvider>
  )
}
