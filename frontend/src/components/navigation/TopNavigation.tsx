import { NavLink, Link } from 'react-router-dom'
import { ThemeToggle } from '../../features/theme/ThemeToggle'
export function TopNavigation(){
  const link = (to:string,label:string)=> (
    <NavLink to={to} className={({isActive})=> `f1-nav-link ${isActive?'is-active':''}`}>{label}</NavLink>
  )
  return (
    <header className="f1-nav">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 sm:px-8 py-3">
        <Link to="/" className="flex items-center gap-2.5" title="Back to home">
          <span className="f1-nav-logo">F1</span>
          <span className="f1-display text-base font-bold" style={{color:'var(--text)'}}>Predictor <span style={{color:'var(--red)'}}>2026</span></span>
        </Link>
        <nav className="flex flex-wrap items-center gap-2" aria-label="Primary">
          {link('/dashboard','Predictions')}
          {link('/live-win-prob','Live Prob')}
          {link('/timeline','Timeline')}
          {link('/replay','Replay')}
          {link('/championship','Champ')}
          {link('/transfer','Transfer')}
          {link('/personas','AI Teams')}
          {link('/preview','Preview')}
          {link('/fingerprint','Styles')}
          {link('/meta-crowd','Meta/Crowd')}
          {link('/community','Community')}
          {link('/sensory','Sensory')}
          {link('/scenario-lab','Lab')}
          {link('/live','Live')}
          {link('/analytics','Analytics')}
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <span className="f1-live-pill"><span className="f1-live-dot" style={{background:'#fff'}}></span>LIVE</span>
        </div>
      </div>
    </header>
  )
}
