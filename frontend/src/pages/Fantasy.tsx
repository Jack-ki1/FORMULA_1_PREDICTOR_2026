import { Sparkles, X } from "lucide-react";
import { Avatar, Card, ErrorNote, Flag, Progress, Skeleton, TeamLogo, cx } from "../components/ui";
import { useFantasy } from "../lib/hooks";
import { useApp } from "../lib/store";

export default function Fantasy() {
  const race = useApp((s) => s.applied.race_id);
  const { fantasy, setFantasy } = useApp();
  const q = useFantasy(race);
  const f = q.data;
  const chosen = (f?.pool ?? []).filter((d) => fantasy.includes(d.code));
  const spent = chosen.reduce((s, d) => s + d.price, 0), exp = chosen.reduce((s, d) => s + d.exp_points, 0);
  const toggle = (c: string, price: number) => {
    if (fantasy.includes(c)) return setFantasy(fantasy.filter((x) => x !== c));
    if (fantasy.length >= (f?.picks ?? 5) || spent + price > (f?.budget ?? 100)) return;
    setFantasy([...fantasy, c]);
  };
  return (
    <div className="space-y-3 p-3.5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><h1 className="text-[20px] font-extrabold">Fantasy League{f ? ` · ${f.race.name}` : ""}</h1><p className="text-[11px] text-mute">Pick {f?.picks ?? 5} drivers within a ${f?.budget ?? 100}M budget. Scored by simulated expected points. Your team is saved in this browser.</p></div>
        <div className="flex gap-2"><button className="btn-red" disabled={!f} onClick={() => f && setFantasy(f.optimal)}><Sparkles size={13} />Auto-pick best team</button><button className="btn-ghost" onClick={() => setFantasy([])}>Clear</button></div>
      </div>
      {q.isError && <ErrorNote error={q.error} retry={() => q.refetch()} />}
      <div className="grid gap-3 lg:grid-cols-[1.6fr_1fr]">
        <Card className="overflow-x-auto p-3"><table className="w-full min-w-[420px] text-[12px]">
          <thead><tr className="text-left">{["DRIVER", "TEAM", "PRICE", "EXP. PTS", ""].map((h) => <th key={h} className="label px-2 py-2 !text-[9px]">{h}</th>)}</tr></thead>
          <tbody>{!f ? <tr><td colSpan={5}><Skeleton className="h-72" /></td></tr> : f.pool.map((d) => {
            const on = fantasy.includes(d.code), blocked = !on && (fantasy.length >= f.picks || spent + d.price > f.budget);
            return (<tr key={d.code} className={cx("border-t border-edge", on && "bg-f1red/10")}><td className="px-2 py-2"><span className="flex items-center gap-2"><Flag cc={d.cc} className="h-2.5 w-4" />{d.name}</span></td>
              <td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={d.team} size={13} />{d.team.name}</span></td><td className="px-2 tabular-nums">${d.price.toFixed(1)}M</td><td className="px-2 tabular-nums">{d.exp_points.toFixed(1)}</td>
              <td className="px-2 text-right"><button disabled={blocked} onClick={() => toggle(d.code, d.price)} className={cx("rounded-md px-3 py-1 text-[11px] font-semibold", on ? "bg-white/10" : "bg-gradient-to-r from-f1red to-glow text-white on-accent", blocked && "opacity-30")}>{on ? "Remove" : "Add"}</button></td></tr>);
          })}</tbody></table></Card>
        <Card className="h-fit p-4"><h3 className="text-[13px] font-bold">Your team</h3>
          <div className="mt-3 space-y-2">{chosen.length ? chosen.map((d) => (<div key={d.code} className="flex items-center gap-3 rounded-lg border border-edge bg-black/20 p-2 text-[12px]"><Avatar code={d.code} team={d.team} size={32} /><span className="flex-1 font-medium">{d.name}</span><span className="tabular-nums text-mute">${d.price}M</span><button aria-label={`Remove ${d.name}`} onClick={() => toggle(d.code, d.price)}><X size={13} /></button></div>)) : <p className="text-[11px] text-mute">No drivers picked yet.</p>}</div>
          <div className="mt-4 space-y-2 text-[11px]"><div className="flex justify-between"><span className="text-mute">Budget used</span><b>${spent.toFixed(1)}M / ${f?.budget ?? 100}M</b></div><Progress value={spent / (f?.budget ?? 100)} />
            <div className="flex justify-between pt-2"><span className="text-mute">Expected points</span><b className="text-glow">{exp.toFixed(1)}</b></div>
            {f && <div className="flex justify-between"><span className="text-mute">Model’s best possible</span><b>{f.optimal_points}</b></div>}</div></Card>
      </div>
    </div>
  );
}
