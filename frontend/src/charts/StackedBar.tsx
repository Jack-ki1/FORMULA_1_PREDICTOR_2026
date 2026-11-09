import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface StackedBarProps {
  data: { name: string; a: number; b: number; aLabel: string; bLabel: string; color?: string }[];
  width?: number | string;
  height?: number | string;
}

export function StackedBar({ data, height = 240 }: StackedBarProps) {
  const vals = data.filter((d) => d.a != null && d.b != null);
  const aria = vals.length ? vals.slice(0, 3).map((d) => `${d.name}: ${d.aLabel} ${d.a.toFixed(0)}, ${d.bLabel} ${d.b.toFixed(0)}`).join("; ") : "No data";
  if (vals.length === 0) return <div className="h-[240px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const h = typeof height === "number" ? height : 240;
  const aLabel = vals[0]?.aLabel ?? "A";
  const bLabel = vals[0]?.bLabel ?? "B";
  return (
    <div className="w-full" style={{ height: h }} role="img" aria-label={aria}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={vals} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <Tooltip content={({ active, payload }: any) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload as any;
            return (<div className="rounded border p-2 text-[11px]" style={{ background: "rgb(var(--tt-bg) / 0.98)", borderColor: "rgb(var(--tt-bg))", color: "rgb(var(--tt-fg))" }}><b style={{ color: "rgb(var(--tt-fg))" }}>{d.name}</b><div style={{ color: "rgb(var(--tt-fg))" }}>{d.aLabel}: {d.a.toFixed(2)}</div><div style={{ color: "rgb(var(--tt-fg))" }}>{d.bLabel}: {d.b.toFixed(2)}</div></div>);
          }} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={0} angle={-20} textAnchor="end" height={48} />
          <YAxis hide />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          <Bar dataKey="a" name={aLabel} stackId="a" fill="rgb(var(--chart1))" />
          <Bar dataKey="b" name={bLabel} stackId="a" fill="rgb(var(--chart2))" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
