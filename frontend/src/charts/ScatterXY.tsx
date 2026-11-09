import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from "recharts";
import type { Team } from "../lib/api";

interface ScatterXYProps {
  data: { name: string; x: number; y: number; team?: Team; color?: string }[];
  highlight?: string[];
  frontier?: { x: number; y: number }[];
  width?: number | string;
  height?: number | string;
  xLabel?: string;
  yLabel?: string;
}

export function ScatterXY({ data, height = 260, xLabel = "X", yLabel = "Y" }: ScatterXYProps) {
  const vals = data.filter((d) => d.x != null && d.y != null);
  const aria = vals.length ? vals.slice(0, 3).map((d) => `${d.name} (${d.x.toFixed(1)}, ${d.y.toFixed(1)})`).join(", ") : "No data";
  if (vals.length === 0) return <div className="h-[260px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const h = typeof height === "number" ? height : 260;
  return (
    <div className="w-full" style={{ height: h }} role="img" aria-label={aria}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 8, left: 0, bottom: 8  }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
          <XAxis dataKey="x" type="number" name={xLabel} tick={{ fontSize: 10, fill: "#94a3b8" }} label={{ value: xLabel, position: "insideBottom", offset: -2, fontSize: 10, fill: "#64748b" }} />
          <YAxis dataKey="y" type="number" name={yLabel} tick={{ fontSize: 10, fill: "#94a3b8" }} width={36} label={{ value: yLabel, angle: -90, position: "insideLeft", fontSize: 10, fill: "#64748b" }} />
          <Tooltip content={({ active, payload }: any) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload as any;
            return (<div className="rounded border p-2 text-[11px]" style={{ background: "rgb(var(--tt-bg) / 0.98)", borderColor: "rgb(var(--tt-bg))", color: "rgb(var(--tt-fg))" }}><b style={{ color: "rgb(var(--tt-fg))" }}>{d.name}</b><div style={{ color: "rgb(var(--tt-fg))" }}>{xLabel}: {Number(d.x).toFixed(2)}</div><div style={{ color: "rgb(var(--tt-fg))" }}>{yLabel}: {Number(d.y).toFixed(2)}</div></div>);
          }} />
          <Scatter data={vals}>
            {vals.map((entry, i) => (
              <Cell key={entry.name} fill={entry.color ?? entry.team?.color ?? `hsl(${(i * 47) % 360}, 70%, 55%)`} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
