interface GaugeProps {
  value: number | null;
  min?: number;
  max?: number;
  label?: string;
  width?: number | string;
  height?: number | string;
}

export function Gauge({ value, min = 0, max = 100, label, height = 160 }: GaugeProps) {
  const v = value == null ? null : Math.min(max, Math.max(min, value));
  const pct = v == null ? 0 : (v - min) / (max - min || 1);
  const aria = v == null ? "No data" : `${label ?? "Value"} ${v.toFixed(0)} of ${max}`;
  const color = pct < 0.33 ? "rgb(var(--bad))" : pct < 0.66 ? "rgb(var(--warn))" : "rgb(var(--ok))";
  const r = 54, c = 2 * Math.PI * r;
  const h = typeof height === "number" ? height : 160;
  return (
    <div className="flex w-full flex-col items-center justify-center" style={{ minHeight: h }} role="img" aria-label={aria}>
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="rgb(var(--edge) / 0.35)" strokeWidth="10" />
        {v != null && <circle cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="10" strokeDasharray={c} strokeDashoffset={c * (1 - pct)} strokeLinecap="round" transform="rotate(-90 70 70)" />}
        <text x="70" y="76" textAnchor="middle" fill="rgb(var(--fg))" fontSize="22" fontWeight="700">{v == null ? "—" : `${v.toFixed(0)}%`}</text>
      </svg>
      {label && <div className="mt-1 max-w-full px-2 text-center text-[11px] text-slate-300">{label}</div>}
    </div>
  );
}
