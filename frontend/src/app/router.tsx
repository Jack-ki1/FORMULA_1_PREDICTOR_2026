import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { HomePage } from '../pages/Home'
import { DashboardPage } from '../pages/Dashboard'
import { StandingsPage } from '../pages/Standings'
import { H2HPage } from '../pages/H2H'
import { ConstructorsPage } from '../pages/Constructors'
import { FantasyPage } from '../pages/Fantasy'
import { AnalyticsPage } from '../pages/Analytics'
import { SettingsPage } from '../pages/Settings'
export const router = createBrowserRouter([
  { path:'/', element: <AppShell />, children:[
    { index:true, element:<HomePage />},
    { path:'dashboard', element:<DashboardPage />},
    { path:'predictions', element:<DashboardPage />},
    { path:'standings', element:<StandingsPage />},
    { path:'h2h', element:<H2HPage />},
    { path:'fantasy', element:<FantasyPage />},
    { path:'teams', element:<ConstructorsPage />},
    { path:'constructors', element:<ConstructorsPage />},
    { path:'analytics', element:<AnalyticsPage />},
    { path:'analytics-news', element:<AnalyticsPage />},
    { path:'settings', element:<SettingsPage />},
  ]}
])
