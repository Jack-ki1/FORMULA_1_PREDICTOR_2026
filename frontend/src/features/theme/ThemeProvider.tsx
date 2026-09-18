import { useEffect } from 'react'
import { usePreferences, applyPreferencesToDocument } from '../preferences/store'

// Thin wrapper now — the preferences store is the single source of truth for
// theme + colors + accessibility flags (see features/preferences/store.ts).
// This component's only job is to re-apply document attributes whenever
// preferences change (it already applies once at import time for first paint).
export function ThemeProvider({ children }: { children: any }) {
  const prefs = usePreferences((s: any) => s.prefs)
  useEffect(() => { applyPreferencesToDocument(prefs) }, [prefs])
  return children
}
