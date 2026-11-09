import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

interface LineSeriesProps {
  data: Array<{ name: string } & Record<string, string | number>>;
  series: { key: string; label: string; color?: string }[];
  width?: number | string;
  height?: number | string;
  valueFmt?: (v: number) => string;
}

export function LineSeries({ data, series, height = 240, valueFmt = (v) => v.toFixed(1) }: LineSeriesProps) {
  const vals = data.filter((d) => series.some((s) => d[s.key] != null));
  const aria = vals.length ? series.slice(0, 3).map((s) => `${s.label}: ${valueFmt(Number(vals[vals.length - 1][s.key] ?? 0))}`).join(", ") : "No data";
  if (vals.length === 0) return <div className="h-[240px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const h = typeof height === "number" ? height : 240;
  return (
    <div className="w-full" style={{ height: h }} role="img" aria-label={aria}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={vals} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} />
          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} width={36} />
          <Tooltip content={({ active, payload, label }: any) => {
            if (!active || !payload?.length) return null;
            return (<div className="rounded border p-2 text-[11px]" style={{ background: "rgb(var(--tt-bg) / 0.98)", borderColor: "rgb(var(--tt-bg))", color: "rgb(var(--tt-fg))" }}><b style={{ color: "rgb(var(--tt-fg))" }}>{label}</b>{payload.map((p: any) => <div key={p.dataKey}>{p.name}: {valueFmt(Number(p.value ?? 0))}</div>)}</div>);
          }} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          {series.map((s, i) => (
            <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color ?? `hsl(${(i * 50) % 360}, 70%, 55%)`} strokeWidth={2} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
