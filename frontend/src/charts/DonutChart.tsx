import { PieChart, Pie, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { Team } from "../lib/api";
import { pct } from "../components/ui";

interface DonutChartProps {
  data: { name: string; value: number; team?: Team; color?: string; desc?: string }[];
  total?: string;
  width?: number | string;
  height?: number | string;
  showLegend?: boolean;
  valueFmt?: (v: number, total: number) => string;
}

const FALLBACK = ["#e10600", "#7c4dff", "#22c55e", "#f59e0b", "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#3b82f6", "#a855f7", "#14b8a6", "#ef4444"];

export function DonutChart({ data, total, height = 240, showLegend = false, valueFmt }: DonutChartProps) {
  const vals = data.filter((d) => d.value != null && d.value > 0);
  const top3 = [...vals].sort((a, b) => b.value - a.value).slice(0, 3);
  const totalVal = vals.reduce((s, d) => s + d.value, 0) || 1;
  const fmt = valueFmt ?? ((v: number, t: number) => pct(v / t));
  const aria = top3.length ? `Top 3: ${top3.map((d) => `${d.name} ${fmt(d.value, totalVal)}`).join(", ")}` : "No data";
  if (vals.length === 0) return <div className="h-[240px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const h = typeof height === "number" ? height : 240;
  const chartH = showLegend ? Math.max(160, h - Math.min(vals.length, 8) * 22) : h;
  return (
    <div className="w-full" role="img" aria-label={aria}>
      <div style={{ height: chartH  }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={vals} cx="50%" cy="50%" innerRadius="42%" outerRadius="68%" paddingAngle={2} dataKey="value" nameKey="name">
              <Tooltip content={({ active, payload }: any) => {
                if (!active || !payload?.[0]) return null;
                const d = payload[0].payload as any;
                return (<div className="rounded border p-2 text-[11px]" style={{ background: "rgb(var(--tt-bg) / 0.98)", borderColor: "rgb(var(--tt-bg))", color: "rgb(var(--tt-fg))" }}><b style={{ color: "rgb(var(--tt-fg))" }}>{d.name}</b><div style={{ color: "rgb(var(--tt-fg))" }}>{fmt(d.value, totalVal)}</div>{d.desc && <div className="mt-1 max-w-[220px] text-red-600/90">{d.desc}</div>}</div>);
              }} />
              {vals.map((entry, i) => (
                <Cell key={`cell-${i}`} fill={entry.color ?? entry.team?.color ?? FALLBACK[i % FALLBACK.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      {total && <div className="-mt-5 mb-1 text-center text-[11px] font-bold tabular-nums text-slate-200">{total}</div>}
      {showLegend && (
        <div className="mt-2 grid gap-x-3 gap-y-1 text-[10px] sm:grid-cols-2">
          {vals.map((d, i) => (
            <div key={`${d.name}-${i}`} className="flex items-start gap-2">
              <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: d.color ?? d.team?.color ?? FALLBACK[i % FALLBACK.length]  }} />
              <span className="min-w-0"><b className="text-slate-200">{d.name}</b> <span className="tabular-nums text-slate-300">{fmt(d.value, totalVal)}</span>{d.desc && <span className="block text-slate-400">{d.desc}</span>}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
