import type { Team } from "../lib/api";

interface RangeBarProps {
  data: { name: string; p10: number; p50: number; p90: number; mean: number; team?: Team; color?: string }[];
  width?: number | string;
  height?: number | string;
}

export function RangeBar({ data, height = 300 }: RangeBarProps) {
  const vals = data.filter((d) => d.p10 != null && d.p50 != null && d.p90 != null);
  const aria = vals.length ? vals.slice(0, 3).map((d) => `${d.name}: p10 ${d.p10.toFixed(1)}, p50 ${d.p50.toFixed(1)}, p90 ${d.p90.toFixed(1)}`).join("; ") : "No data";
  if (vals.length === 0) return <div className="h-[300px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const lo = Math.min(...vals.map((d) => d.p10));
  const hi = Math.max(...vals.map((d) => d.p90));
  const span = hi - lo || 1;
  const scale = (v: number) => ((v - lo) / span) * 100;
  const h = typeof height === "number" ? height : 300;
  return (
    <div className="w-full overflow-auto pr-1" style={{ maxHeight: h }} role="img" aria-label={aria}>
      <div className="space-y-1.5">
        {vals.map((d, i) => {
          const color = d.color ?? d.team?.color ?? `hsl(${(i * 47) % 360}, 70%, 55%)`;
          return (
            <div key={`${d.name}-${i}`} className="flex items-center gap-2 text-[11px]">
              <span className="w-24 shrink-0 truncate text-right text-slate-300" title={d.name}>{d.name}</span>
              <div className="relative h-3.5 min-w-0 flex-1 rounded bg-white/[0.06]">
                <div className="absolute top-1/2 h-1 -translate-y-1/2 rounded bg-slate-500/50" style={{ left: `${scale(d.p10)}%`, width: `${Math.max(scale(d.p90) - scale(d.p10), 1)}%` }} />
                <div className="absolute top-1/2 h-2.5 w-1 -translate-y-1/2 rounded bg-white" style={{ left: `calc(${scale(d.p50)}% - 2px)` }} title={`p50 ${d.p50.toFixed(1)}`} />
                <div className="absolute top-1/2 h-2 w-2 -translate-y-1/2 rounded-full border border-white" style={{ left: `calc(${scale(d.mean)}% - 4px)`, background: color }} title={`mean ${d.mean.toFixed(1)}`} />
              </div>
              <span className="w-16 shrink-0 text-right tabular-nums text-slate-200">{d.mean.toFixed(1)}</span>
            </div>
          );
        })}
      </div>
      <div className="mt-2 text-[10px] text-mute">bar = p10–p90 · white tick = p50 · dot = mean</div>
    </div>
  );
}
