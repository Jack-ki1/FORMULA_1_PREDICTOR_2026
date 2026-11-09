import { RadarChart as RC, Radar, PolarAngleAxis, PolarRadiusAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface RadarChartProps {
  data: ({ name: string } & Record<string, number | string>)[];
  axes: { key: string; label: string }[];
  width?: number | string;
  height?: number | string;
}

export function RadarChart({ data, axes, height = 260 }: RadarChartProps) {
  const vals = data.filter((d) => axes.some((a) => d[a.key] != null));
  const aria = vals.length ? vals.slice(0, 2).map((d) => `${d.name}: ${axes.map((a) => `${a.label} ${Number(d[a.key] ?? 0).toFixed(1)}`).join(", ")}`).join("; ") : "No data";
  if (vals.length === 0) return <div className="h-[260px] flex items-center justify-center rounded-lg border border-dashed border-edge text-[11px] text-slate-400">No data available</div>;
  const flat = vals.map((d) => {
    const row: any = { name: d.name };
    axes.forEach((a) => { row[a.label] = Number(d[a.key] ?? 0); });
    return row;
  });
  const maxVal = Math.max(...flat.flatMap((d) => axes.map((a) => Number(d[a.label] ?? 0))), 1);
  return (
    <div className="w-full" style={{ height: typeof height === "number" ? height : 260 }} role="img" aria-label={aria}>
      <ResponsiveContainer width="100%" height="100%">
        <RC data={flat} outerRadius="70%">
          <PolarAngleAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} />
          <PolarRadiusAxis domain={[0, Math.ceil(maxVal)]} tick={{ fontSize: 9, fill: "#94a3b8" }} />
          <Tooltip content={({ active, payload, label }: any) => {
            if (!active || !payload?.length) return null;
            return (<div className="rounded border p-2 text-[11px]" style={{ background: "rgb(var(--tt-bg) / 0.98)", borderColor: "rgb(var(--tt-bg))", color: "rgb(var(--tt-fg))" }}><b style={{ color: "rgb(var(--tt-fg))" }}>{label}</b>{payload.map((p: any) => <div key={p.dataKey} style={{ color: "rgb(var(--tt-fg))" }}>{p.dataKey}: {Number(p.value).toFixed(1)}</div>)}</div>);
          }} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          {axes.map((a, i) => (
            <Radar key={a.label} dataKey={a.label} stroke={`hsl(${(i * 60) % 360}, 70%, 55%)`} fill={`hsl(${(i * 60) % 360}, 70%, 55%)`} fillOpacity={0.15} />
          ))}
        </RC>
      </ResponsiveContainer>
    </div>
  );
}
