import { ArrowRight, Flame, Target, Timer } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { DriverPred, Prediction } from "../lib/api";
import { headlineWord, sessionWord } from "../lib/util";
import { Avatar, AwaitRun, Card, CardTitle, Progress, Segmented, Skeleton, TeamLogo, cx, pct, surname } from "./ui";

const top = (d: DriverPred[], k: keyof DriverPred) => [...d].sort((a, b) => (b[k] as number) - (a[k] as number))[0];

const awaiting = (loading: boolean) => (loading ? <Skeleton className="h-[92px]" /> : <AwaitRun />);

export function StatCards({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-[92px]" />)}</div>;
  const winner = top(p.drivers, "win"), pole = top(p.drivers, "pole"), pod = top(p.drivers, "podium"), fl = top(p.drivers, "fastest_lap");
  const quali = p.params.session === "qualifying";
  const small = (label: string, d: DriverPred, v: number, tone: "red" | "violet") => (
    <Card className="p-4"><div className="label">{label}</div>
      <div className="mt-3 flex items-center justify-between"><b className="text-[15px]">{surname(d.name)}</b><b className="text-[15px] tabular-nums">{pct(v)}</b></div>
      <div className="mt-3"><Progress value={v} tone={tone} /></div></Card>
  );
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <Card className="flex items-center gap-3 p-4">
        <Avatar code={winner.code} team={winner.team} size={50} />
        <div className="min-w-0 flex-1"><div className="label !text-violet">{quali ? "Pole prediction" : p.params.session === "practice" ? "Fastest in practice" : "Winner prediction"}</div><div className="mt-1 truncate text-[14px] font-bold">{winner.name}</div><div className="truncate text-[10px] text-red-300">{winner.team.name}</div></div>
        <b className="text-[22px] tabular-nums">{pct(winner.win)}</b>
      </Card>
      {small("Pole position probability", pole, pole.pole, "red")}
      {small("Podium probability", pod, pod.podium, "violet")}
      {small("Fastest lap probability", fl, fl.fastest_lap, "red")}
    </div>
  );
}

export function WinProbability({ p, loading }: { p?: Prediction; loading?: boolean }) {
  const [mode, setMode] = useState<"prob" | "pts">("prob");
  const rows = p ? [...p.drivers].sort((a, b) => (mode === "prob" ? b.win - a.win : b.avg_points - a.avg_points)).slice(0, 7) : [];
  const val = (d: DriverPred) => (mode === "prob" ? d.win : d.avg_points);
  const max = Math.max(...rows.map(val), 0.0001);
  return (
    <Card className="p-4">
      <div className="mb-2 flex items-center justify-between"><h3 className="label !text-[11px] !text-slate-200">{p ? `${headlineWord(p.params.session)} probability` : "Race win probability"}</h3>
        <Segmented value={mode} onChange={setMode} options={[{ v: "prob", label: "Probability" }, { v: "pts", label: "Points" }]} /></div>
        {!p ? (loading ? <Skeleton className="h-[220px]" /> : <AwaitRun />) : (
        <div className="flex h-[230px] items-end justify-between gap-2 px-1 pt-6" role="img" aria-label="Win probability by driver">
          {rows.map((d, i) => (
            <div key={d.code} className="flex h-full flex-1 flex-col items-center justify-end" title={mode === "prob" ? `${pct(d.win)} ± ${pct(d.win_ci)} (95% CI)` : undefined}>
              <span className="mb-1 text-[10px] font-semibold tabular-nums">{mode === "prob" ? pct(val(d)) : val(d).toFixed(1)}</span>
              <motion.div initial={{ height: 0 }} animate={{ height: `${Math.max(3, (val(d) / max) * 78)}%` }} transition={{ duration: 0.7, delay: i * 0.05 }}
                className="w-full max-w-[44px] rounded-t-[5px]" style={{ background: `linear-gradient(180deg, ${d.team.color}, ${d.team.color}55)`, boxShadow: `0 0 18px -6px ${d.team.color}` }} />
              <div className="mt-2 flex flex-col items-center gap-1"><TeamLogo team={d.team} size={16} /><span className="text-[10px] text-slate-300">{surname(d.name)}</span></div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export function ResultsPanel({ p, loading }: { p?: Prediction; loading?: boolean }) {
  const [tab, setTab] = useState<"results" | "qualifying" | "strategy">("results");
  const byCode = Object.fromEntries((p?.drivers ?? []).map((d) => [d.code, d]));
  const qualiMode = p?.params.session === "qualifying" || p?.params.session === "sprint_qualifying";
  return (
    <Card className="p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="label !text-[11px] !text-slate-200">Results</h3>
        <div className="flex gap-1 rounded-lg border border-edge p-1" role="tablist">
          {([["results", "Results"], ["qualifying", "Qualifying"], ["strategy", "Strategy"]] as const).map(([k, label]) => (
            <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={cx("rounded-md px-3 py-1 text-[11px] font-medium", tab === k ? "bg-gradient-to-r from-f1red to-glow text-white on-accent" : "text-slate-300 hover:bg-white/5")}>{label}</button>
          ))}
        </div>
      </div>
      {!p ? (loading ? <Skeleton className="h-64" /> : <AwaitRun />) : tab === "strategy" ? (
        <div className="space-y-2">{p.strategies.map((s, i) => (
          <div key={s.name} className={cx("flex items-center gap-3 rounded-lg border px-3 py-2.5", i === 0 ? "border-f1red/70 bg-f1red/10" : "border-edge")}>
            <div className="min-w-0 flex-1"><div className="text-[12px] font-semibold">{s.name}</div><div className="text-[10px] text-mute">{s.stops} ({s.tyres})</div></div>
            <div className="text-right"><div className="text-[11px] tabular-nums">{s.prob}%</div>{s.optimal && <span className="mt-0.5 inline-block rounded-full bg-emerald-500/20 px-2 py-0.5 text-[9px] font-semibold text-emerald-300">Optimal</span>}</div>
          </div>
        ))}</div>
      ) : tab === "qualifying" ? (
        <div className="max-h-[420px] overflow-auto"><table className="w-full min-w-[420px] text-[11px]"><thead className="sticky top-0 bg-[#111827]"><tr className="text-left">{["POS", "DRIVER", "TEAM", "EST. TIME / GAP", "Q2", "Q3", "POLE"].map((h) => <th key={h} className="label px-2 py-2 !text-[9px]">{h}</th>)}</tr></thead><tbody>
          {p.qualifying.map((q, i) => { const d = byCode[q.code]; return d ? (<tr key={q.code} className="border-t border-edge"><td className="px-2 py-2 font-bold">{q.pos}</td><td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={d.team} size={13} />{d.name}</span></td><td className="px-2 text-slate-300">{d.team.name}</td><td className="px-2 tabular-nums">{i === 0 ? q.time : `+${q.gap.toFixed(3)}`}</td><td className="px-2 tabular-nums">{pct(q.q2, 0)}</td><td className="px-2 tabular-nums">{pct(q.q3, 0)}</td><td className="px-2 tabular-nums text-glow">{pct(q.pole)}</td></tr>) : null; })}
        </tbody></table></div>
      ) : (
        <div className="max-h-[420px] overflow-auto"><table className="w-full min-w-[480px] text-[11px]"><thead className="sticky top-0 bg-[#111827]"><tr className="text-left">{["POS", "DRIVER", "TEAM", qualiMode ? "POLE PROB" : "WIN PROB", "PODIUM", "POINTS %", "AVG PTS"].map((h) => <th key={h} className="label px-2 py-2 !text-[9px]">{h}</th>)}</tr></thead><tbody>
          {p.drivers.map((d, i) => (<tr key={d.code} className="border-t border-edge"><td className="px-2 py-2 font-bold">{d.pos}</td><td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={d.team} size={13} />{d.name}</span></td><td className="px-2 text-slate-300">{d.team.name}</td><td className={cx("px-2 font-semibold tabular-nums", i === 0 && "text-glow")}>{pct(d.win)}</td><td className="px-2 tabular-nums">{pct(d.podium)}</td><td className="px-2 tabular-nums">{pct(d.points_prob)}</td><td className="px-2 tabular-nums">{d.avg_points.toFixed(1)}</td></tr>))}
        </tbody></table></div>
      )}
    </Card>
  );
}

export function Strategy({ p, loading }: { p?: Prediction; loading?: boolean }) {
  const [sel, setSel] = useState(0);
  return (
    <Card className="p-4">
      <CardTitle icon={<Flame size={13} />} title="RACE STRATEGY INSIGHTS" sub="Best strategy based on current conditions" />
      <div className="space-y-2">
        {!p ? (loading ? [0, 1, 2].map((i) => <Skeleton key={i} className="h-14" />) : <AwaitRun />) : p.strategies.map((s, i) => (
          <button key={s.name} onClick={() => setSel(i)} aria-pressed={sel === i} className={cx("flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition", sel === i ? "border-f1red/70 bg-f1red/10" : "border-edge hover:bg-white/[0.03]")}>
            <span className={cx("grid h-3.5 w-3.5 place-items-center rounded-full border", sel === i ? "border-glow" : "border-mute")}>{sel === i && <span className="h-1.5 w-1.5 rounded-full bg-glow" />}</span>
            <div className="min-w-0 flex-1"><div className="text-[12px] font-semibold">{s.name}</div><div className="truncate text-[10px] text-mute">{s.stops} ({s.tyres})</div></div>
            <div className="text-right"><div className="text-[11px] tabular-nums">{s.prob}%</div>{s.optimal && <span className="mt-0.5 inline-block rounded-full bg-emerald-500/20 px-2 py-0.5 text-[9px] font-semibold text-emerald-300">Optimal</span>}</div>
          </button>
        ))}
      </div>
      <Link to="/predictions?tab=strategy" className="btn-ghost mt-3 w-full">View Full Strategy Analysis <ArrowRight size={13} /></Link>
    </Card>
  );
}

export function ResultsTable({ p, limit = 5, loading }: { p?: Prediction; limit?: number; loading?: boolean }) {
  return (
    <Card className="p-4">
      <CardTitle icon={<Target size={13} />} title={`Predicted ${p ? sessionWord(p.params.session) : "Race"} Results`} />
      <div className="overflow-x-auto"><table className="w-full min-w-[460px] text-[11px]">
        <thead><tr className="bg-white/[0.03] text-left">{["POS", "DRIVER", "TEAM", p?.params.session === "qualifying" ? "POLE PROB" : "WIN PROB", "PODIUM PROB", "PTS (AVG)"].map((h) => <th key={h} className="label px-2 py-2 !text-[9px]">{h}</th>)}</tr></thead>
        <tbody>{!p ? (loading ? [0, 1, 2, 3, 4].map((i) => <tr key={i}><td colSpan={6}><Skeleton className="my-1 h-7" /></td></tr>) : <tr><td colSpan={6}><AwaitRun /></td></tr>) : p.drivers.slice(0, limit).map((d, i) => (
          <tr key={d.code} className="border-t border-edge">
            <td className="px-2 py-2.5 font-bold">{d.pos}</td>
            <td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={d.team} size={14} />{d.name}</span></td>
            <td className="px-2 text-slate-300">{d.team.name}</td>
            <td className={cx("px-2 font-semibold tabular-nums", i === 0 && "text-glow")}>{pct(d.win)}</td>
            <td className="px-2 tabular-nums">{pct(d.podium)}</td><td className="px-2 tabular-nums">{d.avg_points.toFixed(1)}</td>
          </tr>))}</tbody>
      </table></div>
      <Link to="/predictions" className="mt-3 inline-flex items-center gap-1 text-[11px] text-slate-300 hover:text-white">View Full Predictions <ArrowRight size={12} /></Link>
    </Card>
  );
}

const LEVEL: Record<string, string> = { High: "text-emerald-300", Medium: "text-amber-300", Low: "text-slate-400" };

export function Confidence({ p, loading }: { p?: Prediction; loading?: boolean }) {
  const c = p?.confidence ?? 0, R = 52, L = 2 * Math.PI * R;
  const label = c >= 0.75 ? "High" : c >= 0.55 ? "Medium" : "Low";
  if (!p && !loading) return <Card className="p-4"><CardTitle icon={<Timer size={13} />} title="Prediction Confidence" /><AwaitRun /></Card>;
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Prediction Confidence" sub="Model certainty for this run" />
      {!p ? <Skeleton className="h-[220px]" /> : (
        <div className="grid gap-4 lg:grid-cols-[180px_1fr]">
          <div className="rounded-lg border border-edge bg-black/20 p-4 text-center">
            <svg viewBox="0 0 130 130" className="mx-auto h-[130px] w-[130px] -rotate-90" role="img" aria-label={`Confidence ${Math.round(c * 100)} percent`}>
              <circle cx="65" cy="65" r={R} fill="none" stroke="#334155" strokeWidth="9" />
              <motion.circle cx="65" cy="65" r={R} fill="none" stroke="url(#g)" strokeWidth="9" strokeLinecap="round" strokeDasharray={L} initial={{ strokeDashoffset: L }} animate={{ strokeDashoffset: L * (1 - c) }} transition={{ duration: 0.9 }} />
              <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#e10600" /><stop offset="1" stopColor="#ff4d6d" /></linearGradient></defs>
            </svg>
            <div className="-mt-[88px] mb-9 text-[26px] font-extrabold tabular-nums">{`${Math.round(c * 100)}%`}</div>
            <div className={cx("text-[12px] font-semibold", LEVEL[label])}>{label} Confidence</div>
            <p className="mt-1 text-[10px] leading-snug text-mute">{p.params.sims.toLocaleString()} sims · {p.params.session}{p.params.sub ? ` ${p.params.sub}` : ""} · {p.weather_used}</p>
          </div>
          <div className="space-y-3">
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="rounded-lg border border-edge bg-black/20 p-2.5"><div className="label !text-[9px]">Sharpness</div><b className="text-[14px] tabular-nums">{Math.round((p.sharpness ?? 0) * 100)}%</b></div>
              <div className="rounded-lg border border-edge bg-black/20 p-2.5"><div className="label !text-[9px]">Safety Car</div><b className="text-[14px] tabular-nums">{Math.round((p.safety_car_prob ?? 0) * 100)}%</b></div>
              <div className="rounded-lg border border-edge bg-black/20 p-2.5"><div className="label !text-[9px]">Grid Source</div><b className="text-[14px] capitalize">{p.grid_source}</b></div>
            </div>
            <div><div className="mb-2 text-[12px] font-bold">Key Factors</div>
              <div className="space-y-1.5">{(p.factors ?? []).map((f) => (
                <div key={f.name} className="rounded-md border border-edge bg-white/[0.02] px-3 py-2">
                  <div className="flex items-center justify-between text-[11px]"><span>{f.name}</span><b className={LEVEL[f.level]}>{f.level}</b></div>
                  <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-white/[0.06]"><div className="h-full rounded-full bg-gradient-to-r from-f1red to-glow" style={{ width: `${Math.round((f.share ?? 0) * 100)}%` }} /></div>
                  <div className="mt-1 text-[10px] text-mute">~{Math.round((f.share ?? 0) * 100)}% influence</div>
                </div>))}
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
