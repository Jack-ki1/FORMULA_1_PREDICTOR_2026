import { NavLink, Link, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { ThemeToggle } from '../../features/theme/ThemeToggle'
import { Icon } from '../icons/Icon'
import type { IconName } from '../icons/Icon'

const LINKS: { to: string; label: string; icon: IconName }[] = [
  { to: '/dashboard', label: 'Predictions', icon: 'dashboard' },
  { to: '/standings', label: 'Standings', icon: 'standings' },
  { to: '/h2h', label: 'H2H', icon: 'h2h' },
  { to: '/fantasy', label: 'Fantasy', icon: 'fantasy' },
  { to: '/guide', label: 'Guide', icon: 'guide' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]

export function TopNavigation() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  useEffect(() => { setOpen(false) }, [location.pathname])
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  return (
    <header className="f1-nav">
      <div className="flex items-center justify-between gap-3 px-4 sm:px-8 h-full">
        <Link to="/" className="flex items-center gap-2.5 shrink-0" title="Back to home">
          <span className="f1-nav-logo">F1</span>
          <span className="f1-display text-base font-bold hidden xs:inline" style={{ color: 'var(--text)' }}>
            Predictor <span style={{ color: 'var(--red)' }}>2026</span>
          </span>
        </Link>

        <nav className="nav-desktop-links items-center gap-5" aria-label="Primary">
          {LINKS.map(l => (
            <NavLink key={l.to} to={l.to} className={({ isActive }) => `f1-nav-link ${isActive ? 'is-active' : ''}`}>
              <Icon name={l.icon} className="icon-sm" />
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button className="btn-icon nav-hamburger" aria-label="Open menu" aria-expanded={open} onClick={() => setOpen(true)}>
            <Icon name="menu" />
          </button>
        </div>
      </div>

      {open && (
        <>
          <div className="nav-drawer-backdrop" onClick={() => setOpen(false)} />
          <div className="nav-drawer" role="dialog" aria-modal="true" aria-label="Navigation menu">
            <div className="flex items-center justify-between mb-2">
              <span className="f1-display font-bold">Menu</span>
              <button className="btn-icon" aria-label="Close menu" onClick={() => setOpen(false)}><Icon name="close" /></button>
            </div>
            {LINKS.map(l => (
              <NavLink key={l.to} to={l.to} className={({ isActive }) => `nav-drawer-link ${isActive ? 'is-active' : ''}`}>
                <Icon name={l.icon} />
                {l.label}
              </NavLink>
            ))}
          </div>
        </>
      )}
    </header>
  )
}
