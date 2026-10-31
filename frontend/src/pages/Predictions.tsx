import { useSearchParams } from "react-router-dom";
import { Confidence, Strategy } from "../components/Panels";
import { Card, ErrorNote, Flag, Skeleton, TeamLogo, cx, pct } from "../components/ui";
import { usePrediction } from "../lib/hooks";
import { useApp } from "../lib/store";

const TABS = [["results", "Results"], ["qualifying", "Qualifying"], ["strategy", "Strategy"]] as const;

export default function Predictions() {
  const [sp, setSp] = useSearchParams();
  const tab = sp.get("tab") ?? "results";
  const applied = useApp((s) => s.applied);
  const q = usePrediction(applied);
  const p = q.data;
  const name = (c: string) => p?.drivers.find((d) => d.code === c);
  return (
    <div className="space-y-3 p-3.5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><h1 className="flex items-center gap-2 text-[20px] font-extrabold">{p && <Flag cc={p.race.cc} className="h-4 w-6" />}Full Predictions{p ? ` · ${p.race.name}` : ""}</h1>
          <p className="text-[11px] text-mute">{p ? `${p.params.sims.toLocaleString()} simulations · ${p.params.session} · ${p.params.weather} · seed ${p.seed}` : "Loading…"} — change settings on the Dashboard or in Settings.</p></div>
        <div className="flex gap-1 rounded-lg border border-edge p-1" role="tablist">{TABS.map(([k, l]) => <button key={k} role="tab" aria-selected={tab === k} onClick={() => setSp({ tab: k })} className={cx("rounded-md px-4 py-1.5 text-[12px] font-medium", tab === k ? "bg-gradient-to-r from-f1red to-glow text-white on-accent" : "text-slate-300 hover:bg-white/5")}>{l}</button>)}</div>
      </div>
      {q.isError && !p && <ErrorNote error={q.error} retry={() => q.refetch()} />}
      {tab === "results" && (
        <Card className="overflow-x-auto p-3"><table className="w-full min-w-[820px] text-[11px]">
          <thead><tr className="text-left">{["POS", "DRIVER", "TEAM", "WIN (95% CI)", "PODIUM", "POINTS", "DNF", "AVG PTS", "EXP. FINISH", "FASTEST LAP", "FINISH DISTRIBUTION P1→P10"].map((h) => <th key={h} className="label px-2 py-2 !text-[9px]">{h}</th>)}</tr></thead>
          <tbody>{!p ? <tr><td colSpan={11}><Skeleton className="h-64" /></td></tr> : p.drivers.map((d) => (
            <tr key={d.code} className="border-t border-edge">
              <td className="px-2 py-2 font-bold">{d.pos}</td><td className="px-2"><span className="flex items-center gap-2"><Flag cc={d.cc} className="h-2.5 w-4" />{d.name}</span></td>
              <td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={d.team} size={13} />{d.team.name}</span></td>
              <td className="px-2 tabular-nums">{pct(d.win)} <span className="text-mute">±{pct(d.win_ci)}</span></td><td className="px-2 tabular-nums">{pct(d.podium)}</td>
              <td className="px-2 tabular-nums">{pct(d.points_prob, 0)}</td><td className="px-2 tabular-nums">{pct(d.dnf)}</td><td className="px-2 tabular-nums">{d.avg_points.toFixed(2)}</td>
              <td className="px-2 tabular-nums">{d.exp_pos.toFixed(1)}</td><td className="px-2 tabular-nums">{pct(d.fastest_lap)}</td>
              <td className="px-2"><div className="flex gap-0.5">{d.dist.map((v, i) => <span key={i} title={`P${i + 1}: ${pct(v)}`} className="h-4 w-4 rounded-[2px]" style={{ background: d.team.color, opacity: 0.1 + Math.min(0.9, v * 3.5) }} />)}</div></td>
            </tr>))}</tbody></table></Card>
      )}
      {tab === "qualifying" && (
        <Card className="overflow-x-auto p-3"><table className="w-full min-w-[480px] text-[12px]">
          <thead><tr className="text-left">{["POS", "DRIVER", "EST. TIME", "GAP", "POLE PROB"].map((h) => <th key={h} className="label px-2 py-2 !text-[9px]">{h}</th>)}</tr></thead>
          <tbody>{!p ? <tr><td colSpan={5}><Skeleton className="h-64" /></td></tr> : p.qualifying.map((r) => { const d = name(r.code)!; return (
            <tr key={r.code} className="border-t border-edge"><td className="px-2 py-2 font-bold">{r.pos}</td><td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={d.team} size={14} />{d.name}</span></td>
              <td className="px-2 tabular-nums">{r.time}</td><td className="px-2 tabular-nums">{r.pos === 1 ? "—" : `+${r.gap.toFixed(3)}`}</td><td className="px-2 tabular-nums">{pct(r.pole)}</td></tr>); })}</tbody></table>
          <p className="p-2 text-[10px] text-mute">Times are estimates anchored to each circuit’s lap record; gaps come from the simulated rating spread.</p></Card>
      )}
      {tab === "strategy" && (
        <div className="grid gap-3 lg:grid-cols-2"><Strategy p={p} /><Confidence p={p} />
          <Card className="p-4 text-[12px] text-slate-300 lg:col-span-2"><h3 className="mb-2 font-bold text-white">How strategies are scored</h3>
            <p>Likelihoods come from circuit tyre wear, overtaking difficulty, weather and the safety-car rate ({p ? pct(p.safety_car_rate, 0) : "—"} of simulated races had a safety car). High-wear tracks favour two stops; easy-overtaking tracks reward aggressive starts on softs.</p></Card></div>
      )}
    </div>
  );
}
