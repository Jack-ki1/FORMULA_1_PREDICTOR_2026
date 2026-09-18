import type { SVGProps } from 'react'

// A small, purpose-built icon set (stroke-based, currentColor) so every page
// shares one consistent visual language instead of emoji standing in for icons.
// Adding a new npm icon library wasn't necessary for ~30 glyphs.

export type IconName =
  | 'dashboard' | 'standings' | 'h2h' | 'fantasy' | 'guide' | 'settings'
  | 'sun' | 'moon' | 'monitor' | 'menu' | 'close' | 'chevron-right' | 'chevron-down'
  | 'palette' | 'accessibility' | 'layout' | 'engine' | 'database' | 'bell' | 'sliders'
  | 'user' | 'shield' | 'keyboard' | 'download' | 'upload' | 'trash' | 'check' | 'alert'
  | 'info' | 'lock' | 'unlock' | 'search' | 'refresh' | 'flag' | 'gauge' | 'cloud'

const paths: Record<IconName, string> = {
  dashboard: 'M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6V11h-6v9Zm0-16v5h6V4h-6Z',
  standings: 'M4 20V10M10 20V4M16 20v-7M4 20h16',
  h2h: 'M8 4 4 8l4 4M16 4l4 4-4 4M4 8h16M9 16l-3 4h12l-3-4H9Z',
  fantasy: 'm12 3 2.6 5.6L21 9.3l-4.5 4.2 1.2 6.1L12 16.8 6.3 19.6l1.2-6.1L3 9.3l6.4-.7L12 3Z',
  guide: 'M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15ZM4 5.5v15M20 18H6.5A2.5 2.5 0 0 0 4 20.5',
  settings: 'M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z M19.4 13a7.6 7.6 0 0 0 0-2l2.1-1.6-2-3.5-2.5 1a7.6 7.6 0 0 0-1.7-1L15 3h-4l-.3 2.9a7.6 7.6 0 0 0-1.7 1l-2.5-1-2 3.5L6.6 11a7.6 7.6 0 0 0 0 2l-2.1 1.6 2 3.5 2.5-1a7.6 7.6 0 0 0 1.7 1L11 21h4l.3-2.9a7.6 7.6 0 0 0 1.7-1l2.5 1 2-3.5L19.4 13Z',
  sun: 'M12 3v2m0 14v2M4.2 4.2l1.4 1.4m12.8 12.8 1.4 1.4M3 12h2m14 0h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z',
  moon: 'M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11Z',
  monitor: 'M3 5h18v11H3V5Zm5 15h8m-4-4v4',
  menu: 'M3 6h18M3 12h18M3 18h18',
  close: 'M6 6l12 12M18 6 6 18',
  'chevron-right': 'm9 6 6 6-6 6',
  'chevron-down': 'm6 9 6 6 6-6',
  palette: 'M12 3a9 9 0 1 0 0 18c1.1 0 1.8-.9 1.8-1.8 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.2 0-.9.7-1.6 1.6-1.6h1.9A4.2 4.2 0 0 0 21 11c0-4.4-4-8-9-8Z M7 12a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm3-4a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm5 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm2 4a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z',
  accessibility: 'M12 4a1.6 1.6 0 1 0 0-3.2A1.6 1.6 0 0 0 12 4Zm-7 6 5-1.5V7L5.5 8.3 6 10Zm14 0-5-1.5V7l5.5 1.3-.5 1.7ZM9 8.5v4L6 20h2.2l2-4.5h1.6l2 4.5H16l-3-7.5v-4Z',
  layout: 'M3 4h18v6H3V4Zm0 10h8v6H3v-6Zm10 0h8v6h-8v-6Z',
  engine: 'M10 3h4v3.2a6 6 0 0 1 2.7 1.5l2.8-1.1 2 3.5-2.4 2a6 6 0 0 1 0 3.1l2.4 2-2 3.5-2.8-1.1A6 6 0 0 1 14 21.8V25h-4v-3.2a6 6 0 0 1-2.7-1.5l-2.8 1.1-2-3.5 2.4-2a6 6 0 0 1 0-3.1l-2.4-2 2-3.5 2.8 1.1A6 6 0 0 1 10 6.2V3Z',
  database: 'M12 5c4.4 0 8-1.1 8-2.5S16.4 0 12 0 4 1.1 4 2.5 7.6 5 12 5Zm8 2.5C20 8.9 16.4 10 12 10S4 8.9 4 7.5M20 12.5c0 1.4-3.6 2.5-8 2.5s-8-1.1-8-2.5M20 17.5c0 1.4-3.6 2.5-8 2.5s-8-1.1-8-2.5M4 2.5v15C4 18.9 7.6 20 12 20s8-1.1 8-2.5v-15',
  bell: 'M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9Z M13.7 21a2 2 0 0 1-3.4 0',
  sliders: 'M4 6h9m3 0h4M4 12h4m3 0h9M4 18h13m3 0h.01M9 4v4M15 10v4M18 16v4',
  user: 'M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Zm-7.5 9a7.5 7.5 0 0 1 15 0',
  shield: 'M12 3 4.5 6v6c0 4.5 3.2 7.7 7.5 9 4.3-1.3 7.5-4.5 7.5-9V6L12 3Z',
  keyboard: 'M3 6h18v12H3V6Zm3 3h.01M9 9h.01M12 9h.01M15 9h.01M18 9h.01M6 12h.01M9 12h.01M12 12h.01M15 12h.01M18 12h.01M7 15h10',
  download: 'M12 4v11m0 0-4-4m4 4 4-4M4 19h16',
  upload: 'M12 15V4m0 0 4 4m-4-4-4 4M4 19h16',
  trash: 'M5 7h14M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2m-9 0 1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13',
  check: 'm5 13 4 4L19 7',
  alert: 'M12 9v4m0 4h.01M10.3 3.9 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z',
  info: 'M12 8h.01M11 12h1v5h1M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  lock: 'M6 11V8a6 6 0 1 1 12 0v3M5 11h14v10H5V11Z',
  unlock: 'M6 11V8a6 6 0 0 1 11.3-2.7M5 11h14v10H5V11Z',
  search: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm10 2-4.35-4.35',
  refresh: 'M4 4v5h5M20 20v-5h-5M4.6 15a8 8 0 0 0 14.4 2.8M19.4 9A8 8 0 0 0 5 6.2',
  flag: 'M5 3v18M5 4h13l-3 4 3 4H5',
  gauge: 'M4 15a8 8 0 1 1 16 0M12 15l4-5',
  cloud: 'M7 18a4.5 4.5 0 0 1-1-8.9A5.5 5.5 0 0 1 17 8a4 4 0 0 1-1 7.9M7 18h9',
}

export function Icon({ name, className = 'icon', ...rest }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true" {...rest}>
      <path d={paths[name]} />
    </svg>
  )
}
