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
        <nav className="flex flex-wrap items-center gap-4" aria-label="Primary">
          {link('/dashboard','Predictions')}
          {link('/standings','Standings')}
          {link('/h2h','H2H')}
          {link('/fantasy','Fantasy')}
          {link('/analytics','Analytics & News')}
          {link('/settings','Settings')}
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <span className="f1-live-pill"><span className="f1-live-dot" style={{background:'#fff'}}></span>LIVE</span>
        </div>
      </div>
    </header>
  )
}
