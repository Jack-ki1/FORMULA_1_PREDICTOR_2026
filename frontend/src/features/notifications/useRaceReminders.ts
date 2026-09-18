import { useEffect, useRef } from 'react'
import { useRaces } from '../../hooks/useRaces'
import { usePreferences } from '../preferences/store'

const FIRED_KEY = 'f1-reminder-fired'

/** Real race-reminder notifications using only the browser Notification API — no
 *  backend involved. Checks once a minute whether the next race's session start
 *  falls within the configured reminder window, and fires (once) if so. */
export function useRaceReminders() {
  const { data: races } = useRaces()
  const enabled = usePreferences((s: any) => s.prefs.notifications.raceReminders)
  const minutesBefore = usePreferences((s: any) => s.prefs.notifications.reminderMinutesBefore)
  const checked = useRef(false)

  useEffect(() => {
    if (!enabled || !races?.length) return
    if (typeof Notification === 'undefined') return

    const check = () => {
      if (Notification.permission !== 'granted') return
      const now = Date.now()
      const next = races
        .filter((r: any) => r.status !== 'cancelled' && new Date(r.date).getTime() >= now)
        .sort((a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime())[0]
      if (!next) return
      const msUntil = new Date(next.date).getTime() - now
      const windowMs = minutesBefore * 60_000
      let fired: Record<string, boolean> = {}
      try { fired = JSON.parse(localStorage.getItem(FIRED_KEY) || '{}') } catch { /* noop */ }
      if (msUntil > 0 && msUntil <= windowMs && !fired[next.id]) {
        new Notification(`${next.flag || ''} ${next.name} starts soon`, {
          body: `Session begins in about ${Math.round(msUntil / 60000)} minutes. Open the Dashboard to run a fresh prediction.`,
          tag: `f1-reminder-${next.id}`,
        })
        fired[next.id] = true
        try { localStorage.setItem(FIRED_KEY, JSON.stringify(fired)) } catch { /* noop */ }
      }
    }

    check()
    const id = setInterval(check, 60_000)
    return () => clearInterval(id)
  }, [enabled, minutesBefore, races])

  return { checked }
}

export async function requestNotificationPermission(): Promise<NotificationPermission | 'unsupported'> {
  if (typeof Notification === 'undefined') return 'unsupported'
  if (Notification.permission === 'granted') return 'granted'
  return Notification.requestPermission()
}
