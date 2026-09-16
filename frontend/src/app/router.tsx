import { createBrowserRouter } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import type { ReactNode } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { HomePage } from '../pages/Home'

// Route-level code splitting. The build emitted a single large chunk with a
// repeated "chunks are larger than 500 kB" warning, and every page — including
// the Chart.js-heavy Dashboard/Standings/H2H — was loaded on first paint even
// when the user only wanted the Home page. Heavy pages load on navigation now.
const DashboardPage = lazy(() => import('../pages/Dashboard').then(m => ({ default: m.DashboardPage })))
const StandingsPage = lazy(() => import('../pages/Standings').then(m => ({ default: m.StandingsPage })))
const H2HPage = lazy(() => import('../pages/H2H').then(m => ({ default: m.H2HPage })))
const ConstructorsPage = lazy(() => import('../pages/Constructors').then(m => ({ default: m.ConstructorsPage })))
const FantasyPage = lazy(() => import('../pages/Fantasy').then(m => ({ default: m.FantasyPage })))
const AnalyticsPage = lazy(() => import('../pages/Analytics').then(m => ({ default: m.AnalyticsPage })))
const SettingsPage = lazy(() => import('../pages/Settings').then(m => ({ default: m.SettingsPage })))

function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<div className="px-4 sm:px-8 py-10 text-sub fs-11">Loading…</div>}>{children}</Suspense>
}

export const router = createBrowserRouter([
  { path:'/', element: <AppShell />, children:[
    { index:true, element:<HomePage />},
    { path:'dashboard', element:<Lazy><DashboardPage /></Lazy>},
    { path:'predictions', element:<Lazy><DashboardPage /></Lazy>},
    { path:'standings', element:<Lazy><StandingsPage /></Lazy>},
    { path:'h2h', element:<Lazy><H2HPage /></Lazy>},
    { path:'fantasy', element:<Lazy><FantasyPage /></Lazy>},
    { path:'teams', element:<Lazy><ConstructorsPage /></Lazy>},
    { path:'constructors', element:<Lazy><ConstructorsPage /></Lazy>},
    { path:'analytics', element:<Lazy><AnalyticsPage /></Lazy>},
    { path:'analytics-news', element:<Lazy><AnalyticsPage /></Lazy>},
    { path:'settings', element:<Lazy><SettingsPage /></Lazy>},
  ]}
])
