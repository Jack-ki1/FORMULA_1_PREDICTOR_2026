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
import { LiveWinProbPage } from '../pages/LiveWinProb'
import { TimelinePage } from '../pages/Timeline'
import { ReplayPage } from '../pages/Replay'
import { ChampionshipPage } from '../pages/Championship'
import { TransferPage } from '../pages/Transfer'
import { PersonasPage } from '../pages/Personas'
import { PreviewPage } from '../pages/Preview'
import { FingerprintPage } from '../pages/Fingerprint'
import { MetaCrowdPage } from '../pages/MetaCrowd'
import { CommunityPage } from '../pages/Community'
import { SensoryPage } from '../pages/Sensory'
export const router = createBrowserRouter([
  { path:'/', element: <AppShell />, children:[
    { index:true, element:<HomePage />},
    { path:'dashboard', element:<DashboardPage />},
    { path:'predictions', element:<DashboardPage />},
    { path:'live-win-prob', element:<LiveWinProbPage />},
    { path:'timeline', element:<TimelinePage />},
    { path:'replay', element:<ReplayPage />},
    { path:'championship', element:<ChampionshipPage />},
    { path:'transfer', element:<TransferPage />},
    { path:'personas', element:<PersonasPage />},
    { path:'preview', element:<PreviewPage />},
    { path:'fingerprint', element:<FingerprintPage />},
    { path:'meta-crowd', element:<MetaCrowdPage />},
    { path:'community', element:<CommunityPage />},
    { path:'sensory', element:<SensoryPage />},
    { path:'scenario-lab', element:<ScenarioLabPage />},
    { path:'live', element:<LiveRacePage />},
    { path:'standings', element:<StandingsPage />},
    { path:'h2h', element:<H2HPage />},
    { path:'constructors', element:<ConstructorsPage />},
    { path:'analytics', element:<AnalyticsPage />},
    { path:'reports', element:<ReportsPage />},
  ]}
])
