import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { Team } from "../lib/api";

interface VBarProps {
  data: { name: string; value: number; team?: Team; color?: string }[];
  width?: number | string;
  height?: number | string;
  valueFmt?: (v: number) => string;
}

export function VBar({ data, width = "100%", height = 240, valueFmt = (v) => v.toFixed(1) }: VBarProps) {
  const vals = data.filter((d) => d.value != null);
  const aria = vals.length ? `Top 3: ${[...vals].sort((a, b) => b.value - a.value).slice(0, 3).map((d) => `${d.name} ${valueFmt(d.value)}`).join(", ")}` : "No data";
  if (vals.length === 0) return <div className="h-[240px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const h = typeof height === "number" ? height : 240;
  return (
    <div className="w-full" style={{ height: h }} role="img" aria-label={aria}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={vals} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <Tooltip content={({ active, payload }: any) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload as any;
            return (<div className="rounded border p-2 text-[11px]" style={{ background: "rgb(var(--tt-bg) / 0.98)", borderColor: "rgb(var(--tt-bg))", color: "rgb(var(--tt-fg))" }}><b style={{ color: "rgb(var(--tt-fg))" }}>{d.name}</b><div style={{ color: "rgb(var(--tt-fg))" }}>{valueFmt(d.value)}</div></div>);
          }} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={0} angle={-20} textAnchor="end" height={48} />
          <YAxis hide />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {vals.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={entry.color ?? entry.team?.color ?? `hsl(${(i * 47) % 360}, 70%, 55%)`} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
