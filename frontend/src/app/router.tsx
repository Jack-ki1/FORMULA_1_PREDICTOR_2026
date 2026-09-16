import { createBrowserRouter } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import type { ReactNode } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { HomePage } from '../pages/Home'
import { ErrorBoundary } from '../components/common/ErrorBoundary'

// Route-level code splitting. The build emitted a single large chunk with a
// repeated "chunks are larger than 500 kB" warning, and every page — including
// the Chart.js-heavy Dashboard/Standings/H2H — was loaded on first paint even
// when the user only wanted the Home page. Heavy pages load on navigation now.
const DashboardPage = lazy(() => import('../pages/Dashboard').then(m => ({ default: m.DashboardPage })))
const StandingsPage = lazy(() => import('../pages/Standings').then(m => ({ default: m.StandingsPage })))
const H2HPage = lazy(() => import('../pages/H2H').then(m => ({ default: m.H2HPage })))
const FantasyPage = lazy(() => import('../pages/Fantasy').then(m => ({ default: m.FantasyPage })))
const GuidePage = lazy(() => import('../pages/Guide').then(m => ({ default: m.GuidePage })))
const SettingsPage = lazy(() => import('../pages/Settings').then(m => ({ default: m.SettingsPage })))

function Lazy({ children, label }: { children: ReactNode; label: string }) {
  return (
    <ErrorBoundary label={label}>
      <Suspense fallback={<div className="px-4 sm:px-8 py-10 text-sub fs-11">Loading…</div>}>{children}</Suspense>
    </ErrorBoundary>
  )
}

export const router = createBrowserRouter([
  { 
    path:'/', 
    element: <ErrorBoundary label="App"><AppShell /></ErrorBoundary>, 
    children:[
      // All routes are public - no authentication required
      { index:true, element:<ErrorBoundary label="Home"><HomePage /></ErrorBoundary>},
      { path:'dashboard', element:<Lazy label="Predictions"><DashboardPage /></Lazy>},
      { path:'predictions', element:<Lazy label="Predictions"><DashboardPage /></Lazy>},
      { path:'standings', element:<Lazy label="Standings"><StandingsPage /></Lazy>},
      { path:'h2h', element:<Lazy label="H2H"><H2HPage /></Lazy>},
      { path:'fantasy', element:<Lazy label="Fantasy"><FantasyPage /></Lazy>},
      { path:'guide', element:<Lazy label="User Guide"><GuidePage /></Lazy>},
      { path:'settings', element:<Lazy label="Settings"><SettingsPage /></Lazy>},
    ]
  }
])
