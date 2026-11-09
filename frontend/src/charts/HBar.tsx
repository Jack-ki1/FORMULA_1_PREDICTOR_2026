import type { Team } from "../lib/api";

interface HBarProps {
  data: { name: string; value: number; team?: Team; color?: string }[];
  width?: number | string;
  height?: number | string;
  valueFmt?: (v: number) => string;
}

export function HBar({ data, height = 240, valueFmt = (v) => v.toFixed(1) }: HBarProps) {
  const vals = data.filter((d) => d.value != null);
  const aria = vals.length ? `Top 3: ${[...vals].sort((a, b) => b.value - a.value).slice(0, 3).map((d) => `${d.name} ${valueFmt(d.value)}`).join(", ")}` : "No data";
  if (vals.length === 0) return <div className="h-[240px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const max = Math.max(...vals.map((d) => Math.abs(d.value)), 1);
  const h = typeof height === "number" ? height : 240;
  return (
    <div className="w-full overflow-auto pr-1" style={{ maxHeight: h }} role="img" aria-label={aria}>
      <div className="space-y-1.5">
        {vals.map((d, i) => {
          const pct = (Math.abs(d.value) / max) * 100;
          return (
            <div key={`${d.name}-${i}`} className="flex items-center gap-2 text-[11px]">
              <span className="w-24 shrink-0 truncate text-right text-slate-300" title={d.name}>{d.name}</span>
              <div className="h-3.5 min-w-0 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                <div className="h-full rounded-full" style={{ width: `${Math.max(pct, d.value ? 2 : 0)}%`, background: d.color ?? d.team?.color ?? `hsl(${(i * 47) % 360}, 70%, 55%)` }} />
              </div>
              <span className="w-14 shrink-0 text-right tabular-nums text-slate-200">{valueFmt(d.value)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
