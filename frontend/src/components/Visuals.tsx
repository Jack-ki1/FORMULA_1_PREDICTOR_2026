import { BarChart3, Download, FileJson, Grid3x3, Printer, Route, Users } from "lucide-react";
import { motion } from "framer-motion";
import type { DriverPred, Prediction } from "../lib/api";
import { download, overtakingLabel, predictionCsv } from "../lib/util";
import { Card, CardTitle, Skeleton, TeamLogo, cx, pct, surname } from "./ui";

export function PositionHeatmap({ p }: { p?: Prediction }) {
  const rows = p ? [...p.drivers].sort((a, b) => a.exp_pos - b.exp_pos).slice(0, 14) : [];
  return (
    <Card className="p-4">
      <CardTitle icon={<Grid3x3 size={13} />} title="Finishing Position Probability" sub="Chance of each classified position (darker = more likely)" />
      {!p ? <Skeleton className="h-72" /> : (
        <div className="overflow-x-auto"><table className="w-full min-w-[520px] border-separate border-spacing-[3px] text-[10px]">
          <thead><tr><th className="w-24" />{Array.from({ length: 10 }, (_, i) => <th key={i} className="label !text-[9px]">P{i + 1}</th>)}<th className="label !text-[9px]">DNF</th></tr></thead>
          <tbody>{rows.map((d) => (
            <tr key={d.code}><td className="whitespace-nowrap pr-2 text-[11px] font-medium"><span className="flex items-center gap-1.5"><TeamLogo team={d.team} size={12} />{surname(d.name)}</span></td>
              {d.dist.map((v, i) => <td key={i} title={`${d.name} P${i + 1}: ${pct(v)}`} className="h-6 rounded-[4px] text-center tabular-nums" style={{ background: `${d.team.color}${Math.round(Math.min(1, 0.07 + v * 2.6) * 255).toString(16).padStart(2, "0")}`, color: v > 0.18 ? "#fff" : undefined }}>{v >= 0.04 ? Math.round(v * 100) : ""}</td>)}
              <td className="rounded-[4px] bg-white/[0.04] text-center tabular-nums text-amber-300" title={`DNF ${pct(d.dnf)}`}>{Math.round(d.dnf * 100)}</td></tr>))}</tbody></table></div>
      )}
    </Card>
  );
}

export function TeamBattle({ p }: { p?: Prediction }) {
  const max = Math.max(...(p?.team_points.map((t) => t.points) ?? [1]), 1);
  return (
    <Card className="p-4">
      <CardTitle icon={<Users size={13} />} title="Constructor Battle" sub="Expected team points this session" />
      <div className="space-y-2">{!p ? <Skeleton className="h-64" /> : p.team_points.map((t, i) => (
        <div key={t.team.id} className="flex items-center gap-2 text-[11px]"><TeamLogo team={t.team} size={13} /><span className="w-24 truncate">{t.team.name}</span>
          <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/[0.07]"><motion.div initial={{ width: 0 }} animate={{ width: `${(t.points / max) * 100}%` }} transition={{ duration: 0.7, delay: i * 0.04 }} className="h-full rounded-full" style={{ background: t.team.color }} /></div>
          <b className="w-9 text-right tabular-nums">{t.points.toFixed(1)}</b></div>))}</div>
    </Card>
  );
}

export function GridVsFinish({ p }: { p?: Prediction }) {
  const rows = p ? [...p.drivers].sort((a, b) => a.avg_grid - b.avg_grid) : [];
  const n = rows.length || 22, W = 520, X = (v: number) => 92 + ((v - 1) / Math.max(n - 1, 1)) * (W - 112), H = 24 + n * 17;
  return (
    <Card className="p-4">
      <CardTitle icon={<Route size={13} />} title="Grid → Predicted Finish" sub="Average starting slot (hollow) to average finishing position (solid)" />
      {!p ? <Skeleton className="h-80" /> : (
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Grid versus predicted finish by driver">
          {[1, 5, 10, 15, n].map((t) => <g key={t}><line x1={X(t)} x2={X(t)} y1={14} y2={H - 4} stroke="currentColor" strokeOpacity=".12" /><text x={X(t)} y={10} fontSize="8" textAnchor="middle" fill="currentColor" opacity=".5">P{t}</text></g>)}
          {rows.map((d: DriverPred, i) => {
            const y = 24 + i * 17, a = X(d.avg_grid), b = X(Math.min(d.exp_pos, n)), gain = d.exp_pos < d.avg_grid - 0.3, loss = d.exp_pos > d.avg_grid + 0.3;
            return (<g key={d.code}><text x={0} y={y + 3} fontSize="9" fill="currentColor">{d.code}</text>
              <line x1={a} x2={b} y1={y} y2={y} stroke={gain ? "#2EE6A6" : loss ? "#ff5a6b" : "currentColor"} strokeOpacity={gain || loss ? 0.9 : 0.3} strokeWidth="2" />
              <circle cx={a} cy={y} r="3.4" fill="none" stroke={d.team.color} strokeWidth="1.6" /><circle cx={b} cy={y} r="3.6" fill={d.team.color} /></g>);
          })}
        </svg>
      )}
      <div className="mt-1 flex gap-4 text-[10px] text-mute"><span><span className="text-emerald-300">━</span> gains places</span><span><span className="text-red-400">━</span> loses places</span></div>
    </Card>
  );
}

export function SessionVisual({ p }: { p?: Prediction }) {
  if (!p) return <Card className="p-4"><Skeleton className="h-72" /></Card>;
  const s = p.params.session;
  if (s === "practice") {
    const rows = p.drivers, max = Math.max(...rows.map((d) => d.pace_hi ?? 0), 0.1);
    return (
      <Card className="p-4"><CardTitle icon={<BarChart3 size={13} />} title="Projected Pace Distribution" sub="Gap to the session-best lap: bar = 10th–90th percentile, tick = average" />
        <div className="space-y-1.5">{rows.map((d) => (
          <div key={d.code} className="flex items-center gap-2 text-[10px]"><span className="w-8 font-semibold">{d.code}</span>
            <div className="relative h-2.5 flex-1 rounded-full bg-white/[0.06]"><div className="absolute h-full rounded-full opacity-70" style={{ left: `${((d.pace_lo ?? 0) / max) * 100}%`, width: `${Math.max(1.5, (((d.pace_hi ?? 0) - (d.pace_lo ?? 0)) / max) * 100)}%`, background: d.team.color }} />
              <div className="absolute top-[-2px] h-4 w-0.5 bg-white" style={{ left: `${((d.pace_gap ?? 0) / max) * 100}%` }} /></div>
            <span className="w-14 text-right tabular-nums text-mute">+{(d.pace_gap ?? 0).toFixed(2)}s</span></div>))}</div></Card>
    );
  }
  const rows = p.qualifying;
  const by = Object.fromEntries(p.drivers.map((d) => [d.code, d]));
  return (
    <Card className="p-4"><CardTitle icon={<BarChart3 size={13} />} title="Q1 → Q2 → Q3 Advancement" sub="Probability of surviving each qualifying segment, and taking pole" />
      <div className="max-h-[420px] space-y-1 overflow-auto pr-1">{rows.map((r) => { const d = by[r.code]; return (
        <div key={r.code} className="grid grid-cols-[34px_1fr_1fr_1fr] items-center gap-2 text-[10px]"><span className="flex items-center gap-1 font-semibold"><TeamLogo team={d.team} size={11} />{r.code}</span>
          {([[r.q2, "Q2"], [r.q3, "Q3"], [r.pole, "Pole"]] as const).map(([v, l]) => <div key={l} className="relative h-4 overflow-hidden rounded bg-white/[0.06]"><div className="h-full" style={{ width: `${v * 100}%`, background: d.team.color, opacity: l === "Pole" ? 1 : 0.65 }} /><span className="absolute inset-0 flex items-center justify-between px-1.5"><span className="text-mute">{l}</span><b className="tabular-nums">{Math.round(v * 100)}%</b></span></div>)}</div>); })}</div></Card>
  );
}

function Meter({ label, value, hint }: { label: string; value: number; hint: string }) {
  return <div><div className="mb-1 flex justify-between text-[11px]"><span>{label}</span><b>{hint}</b></div><div className="h-2 overflow-hidden rounded-full bg-white/[0.07]"><motion.div initial={{ width: 0 }} animate={{ width: `${Math.round(value * 100)}%` }} className="h-full rounded-full bg-gradient-to-r from-f1red to-glow" /></div></div>;
}

export function TrackTraits({ p }: { p?: Prediction }) {
  const c = p?.race.circuit;
  return (
    <Card className="p-4"><CardTitle icon={<Route size={13} />} title="Race-Day Profile" sub={c ? `${c.name} — what shapes this result` : undefined} />
      {!p || !c ? <Skeleton className="h-32" /> : (<div className="space-y-3">
        <Meter label="Overtaking ease" value={c.overtaking} hint={overtakingLabel(c.overtaking)} />
        <Meter label="Tyre wear" value={c.tyre_wear} hint={c.tyre_wear >= 0.65 ? "High" : c.tyre_wear >= 0.4 ? "Medium" : "Low"} />
        <Meter label="Safety-car likelihood" value={p.safety_car_prob} hint={`${Math.round(p.safety_car_prob * 100)}%`} />
        <Meter label="Wet-weather impact" value={p.weather_used === "wet" ? 1 : p.weather_used === "mixed" ? 0.5 : 0.05} hint={p.weather_used} />
        <p className="text-[10px] leading-snug text-mute">Hard-to-pass tracks make the grid matter more; high tyre wear shifts strategy toward two stops.</p></div>)}
    </Card>
  );
}

export function ExportPanel({ p }: { p?: Prediction }) {
  const name = p ? `f1-${p.race.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${p.params.session}` : "f1-prediction";
  return (
    <Card className="no-print flex flex-wrap items-center justify-between gap-3 p-4">
      <div><h3 className="text-[13px] font-bold">Export this prediction</h3><p className="text-[10px] text-mute">CSV for spreadsheets, JSON for the full model output, or print/save as PDF.</p></div>
      <div className="flex flex-wrap gap-2">
        <button className="btn-ghost" disabled={!p} onClick={() => p && download(`${name}.csv`, predictionCsv(p), "text/csv")}><Download size={13} />CSV</button>
        <button className="btn-ghost" disabled={!p} onClick={() => p && download(`${name}.json`, JSON.stringify(p, null, 2), "application/json")}><FileJson size={13} />JSON</button>
        <button className={cx("btn-ghost")} onClick={() => window.print()}><Printer size={13} />Print / PDF</button>
      </div>
    </Card>
  );
}
