import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { HomePage } from '../pages/Home'
import { DashboardPage } from '../pages/Dashboard'
import { StandingsPage } from '../pages/Standings'
import { H2HPage } from '../pages/H2H'
import { ConstructorsPage } from '../pages/Constructors'
import { AnalyticsPage } from '../pages/Analytics'
import { ReportsPage } from '../pages/Reports'
export const router = createBrowserRouter([
  { path:'/', element: <AppShell />, children:[
    { index:true, element:<HomePage />},
    { path:'dashboard', element:<DashboardPage />},
    { path:'standings', element:<StandingsPage />},
    { path:'h2h', element:<H2HPage />},
    { path:'constructors', element:<ConstructorsPage />},
    { path:'analytics', element:<AnalyticsPage />},
    { path:'reports', element:<ReportsPage />},
  ]}
], { basename: '/app' })
