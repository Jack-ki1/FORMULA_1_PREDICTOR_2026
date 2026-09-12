import { useContext } from 'react'
import { ThemeCtx } from './ThemeProvider'
export function ThemeToggle(){
  const {theme,toggle}=useContext(ThemeCtx)
  return <button onClick={toggle} className="theme-toggle" aria-label="Toggle dark mode">{theme==='dark'?'☀️':'🌙'}</button>
}
