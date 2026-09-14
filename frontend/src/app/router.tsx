import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { HomePage } from '../pages/Home'
import { DashboardPage } from '../pages/Dashboard'
import { StandingsPage } from '../pages/Standings'
import { H2HPage } from '../pages/H2H'
import { ConstructorsPage } from '../pages/Constructors'
import { AnalyticsPage } from '../pages/Analytics'
import { ReportsPage } from '../pages/Reports'
import { ScenarioLabPage } from '../pages/ScenarioLab'
import { LiveRacePage } from '../pages/LiveRace'
export const router = createBrowserRouter([
  { path:'/', element: <AppShell />, children:[
    { index:true, element:<HomePage />},
    { path:'dashboard', element:<DashboardPage />},
    { path:'predictions', element:<DashboardPage />},
    { path:'scenario-lab', element:<ScenarioLabPage />},
    { path:'live', element:<LiveRacePage />},
    { path:'standings', element:<StandingsPage />},
    { path:'h2h', element:<H2HPage />},
    { path:'constructors', element:<ConstructorsPage />},
    { path:'analytics', element:<AnalyticsPage />},
    { path:'reports', element:<ReportsPage />},
  ]}
])
