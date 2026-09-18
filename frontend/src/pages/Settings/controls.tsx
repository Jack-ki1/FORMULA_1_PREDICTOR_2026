import type { ReactNode } from 'react'
import { Icon } from '../../components/icons/Icon'

export type Tier = 'live' | 'admin' | 'planned' | 'none'

const TIER_BADGE: Record<Tier, { label: string; cls: string } | null> = {
  live: { label: 'Live', cls: 'badge-live' },
  admin: { label: 'Needs admin access', cls: 'badge-admin' },
  planned: { label: 'Not yet applied', cls: 'badge-planned' },
  none: null,
}

export function SectionHeader({ icon, title, description }: { icon: any; title: string; description: string }) {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="btn-icon !cursor-default" style={{ width: 40, height: 40 }}><Icon name={icon} /></div>
      <div>
        <h2 className="f1-display text-lg font-bold">{title}</h2>
        <p className="fs-11 text-sub mt-0.5 max-w-xl">{description}</p>
      </div>
    </div>
  )
}

export function SettingRow({ label, help, tier = 'none', children, dirty }: { label: string; help?: string; tier?: Tier; children: ReactNode; dirty?: boolean }) {
  const badge = TIER_BADGE[tier]
  return (
    <div className={`setting-row ${dirty ? 'is-dirty' : ''}`}>
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-bold text-sm">{label}</span>
          {badge && <span className={`badge ${badge.cls}`}>{badge.label}</span>}
        </div>
        {help && <p className="fs-11 text-sub mt-1 max-w-md">{help}</p>}
      </div>
      <div className="setting-control">{children}</div>
    </div>
  )
}

export function Switch({ checked, onChange, disabled, label }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean; label?: string }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} disabled={disabled}
      onClick={() => onChange(!checked)} className={`f1-switch ${checked ? 'is-on' : ''}`}>
      <span className="knob" />
    </button>
  )
}

export function RangeControl({ value, onChange, min, max, step = 1, unit = '', disabled }: { value: number; onChange: (v: number) => void; min: number; max: number; step?: number; unit?: string; disabled?: boolean }) {
  return (
    <div className="flex items-center gap-2 w-full">
      <input type="range" min={min} max={max} step={step} value={value} disabled={disabled}
        onChange={e => onChange(parseFloat(e.target.value))} className="f1-range flex-1 accent-red" />
      <span className="f1-mono text-sm font-black w-16 text-right" style={{ color: 'var(--red)' }}>{value}{unit}</span>
    </div>
  )
}

export function ColorControl({ value, onChange, disabled }: { value: string; onChange: (v: string) => void; disabled?: boolean }) {
  return (
    <div className="flex items-center gap-2 w-full">
      <input type="color" value={value} disabled={disabled} onChange={e => onChange(e.target.value)}
        className="w-9 h-9 rounded-lg border cursor-pointer" style={{ borderColor: 'var(--border)' }} />
      <input type="text" value={value} disabled={disabled} onChange={e => onChange(e.target.value)} className="f1-input f1-mono flex-1" />
    </div>
  )
}
