import { Outlet } from 'react-router-dom'
import { TopNavigation } from '../navigation/TopNavigation'
import { ThemeProvider } from '../../features/theme/ThemeProvider'
export function AppShell(){
  return (
    <ThemeProvider>
      <div style={{minHeight:'100vh', display:'flex', flexDirection:'column'}}>
        <TopNavigation />
        <main style={{flex:1}}><Outlet /></main>
        <footer className="f1-footer px-4 sm:px-8 py-6 mt-8">
          <div className="flex flex-wrap items-center justify-between gap-2 fs-11">
            <span>&copy; 2026 F1 Predictor. Predictions are modelled estimates, not betting advice.</span>
            <span className="f1-mono">Season 2026 · Model v1.0</span>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  )
}
