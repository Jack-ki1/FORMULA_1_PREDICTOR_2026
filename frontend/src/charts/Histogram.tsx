import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface HistogramProps {
  data: { bin: string; count: number }[];
  width?: number | string;
  height?: number | string;
}

export function Histogram({ data, height = 240 }: HistogramProps) {
  const vals = data.filter((d) => d.count != null && d.count > 0);
  const aria = vals.length ? vals.slice(0, 3).map((d) => `${d.bin}: ${d.count}`).join(", ") : "No data";
  if (vals.length === 0) return <div className="h-[240px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const h = typeof height === "number" ? height : 240;
  return (
    <div className="w-full" style={{ height: h }} role="img" aria-label={aria}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={vals} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <XAxis dataKey="bin" tick={{ fontSize: 10, fill: "#94a3b8" }} />
          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} width={36} />
          <Tooltip content={({ active, payload }: any) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload as any;
            return (<div className="rounded border p-2 text-[11px]" style={{ background: "rgb(var(--tt-bg) / 0.98)", borderColor: "rgb(var(--tt-bg))", color: "rgb(var(--tt-fg))" }}><b style={{ color: "rgb(var(--tt-fg))" }}>{d.bin}</b><div style={{ color: "rgb(var(--tt-fg))" }}>{Number(d.count).toFixed(3)}</div></div>);
          }} />
          <Bar dataKey="count" fill="rgb(var(--chart1))" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
