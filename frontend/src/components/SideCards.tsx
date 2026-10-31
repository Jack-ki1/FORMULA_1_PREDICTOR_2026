import { ArrowRight, Cloud, CloudFog, CloudLightning, CloudRain, CloudSun, Droplets, Loader2, Map, Play, RotateCw, Ruler, Snowflake, Sun, Swords, Trophy, Users, Settings as Cog, Wind, Zap, Route as RouteIcon, Flag as FlagIcon } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { Prediction } from "../lib/api";
import { useH2H, useRaces, useRecent } from "../lib/hooks";
import { useApp } from "../lib/store";
import { Avatar, Card, CardTitle, Flag, Skeleton, Toggle, cx, pct, surname } from "./ui";

export function WeatherIcon({ kind, size = 18 }: { kind: string; size?: number }) {
  const m: Record<string, [typeof Sun, string]> = { sun: [Sun, "text-amber-300"], partly: [CloudSun, "text-amber-200"], cloud: [Cloud, "text-slate-300"], rain: [CloudRain, "text-sky-300"], storm: [CloudLightning, "text-violet"], fog: [CloudFog, "text-slate-400"], snow: [Snowflake, "text-cyan-200"] };
  const [I, c] = m[kind] ?? m.cloud;
  return <I size={size} className={c} />;
}

export function TrackWeather({ p }: { p?: Prediction }) {
  const [bad, setBad] = useState<string | null>(null);
  const c = p?.race.circuit, fc = p?.forecast;
  return (
    <Card className="p-4">
      <CardTitle icon={<Map size={13} />} title="Track & Weather" />
      {!p || !c ? <Skeleton className="h-[330px]" /> : (<>
        <div className="relative h-[84px] overflow-hidden rounded-lg border border-edge bg-gradient-to-br from-[#10204a] to-[#050a17]">
          {bad !== c.id && <img src={`/img/tracks/${c.id}.jpg`} alt={c.name} onError={() => setBad(c.id)} className="heavy-img h-full w-full object-cover" />}
          {bad === c.id && <div className="grid h-full place-items-center text-[10px] text-mute"><RouteIcon size={22} className="mb-1" />Add /img/tracks/{c.id}.jpg</div>}
        </div>
        <div className="mt-2 text-[12px] font-semibold">{c.name} – {c.locality}</div>
        <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-300"><Flag cc={p.race.cc} />{p.race.country}</div>
        <div className="mt-3 grid grid-cols-3 gap-2 text-[10px] text-mute">
          {[[<Ruler size={15} key="a" />, "Length", c.length_km ? `${c.length_km} km` : "—"], [<RotateCw size={15} key="b" />, "Turns", c.turns ?? "—"], [<Zap size={15} key="c" />, "DRS Zones", c.drs ?? "—"]].map(([i, l, v]) => (
            <div key={String(l)} className="flex items-center gap-2"><span className="grid h-8 w-8 place-items-center rounded-full border border-edge text-slate-300">{i}</span><div><div>{l}</div><b className="text-[12px] text-white">{v}</b></div></div>))}
        </div>
        <div className="mt-3 rounded-lg border border-edge bg-black/25 p-3">
          {fc ? (<>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3"><WeatherIcon kind={fc.race_day.kind} size={30} />
                <div><div className="text-[11px] font-semibold">Weather Forecast</div><div className="text-[10px] text-mute">{fc.race_day.label}</div>
                  <div className="mt-1 flex gap-3 text-[10px] text-slate-300"><span className="flex items-center gap-1"><Droplets size={10} />{fc.race_day.humidity ?? "—"}%</span><span className="flex items-center gap-1"><Wind size={10} />{fc.race_day.wind ?? "—"} km/h</span></div></div></div>
              <b className="text-[24px]">{fc.race_day.temp != null ? `${Math.round(fc.race_day.temp)}°C` : "—"}</b>
            </div>
            <div className="mt-3 grid grid-cols-3 divide-x divide-edge border-t border-edge pt-2 text-center text-[10px]">
              {fc.days.map((d) => (<div key={d.date} className="flex flex-col items-center gap-1"><span className="text-mute">{new Date(d.date + "T12:00:00Z").toLocaleDateString("en-US", { weekday: "short", timeZone: "UTC" })}</span><WeatherIcon kind={d.kind} /><b>{d.temp != null ? `${Math.round(d.temp)}°C` : "—"}</b></div>))}
            </div></>) : <p className="py-3 text-center text-[11px] text-mute">Forecast unavailable. Weekend forecasts appear about 16 days before the race.</p>}
        </div>
      </>)}
    </Card>
  );
}

export function H2HCard({ p }: { p?: Prediction }) {
  const [a, b] = p ? [...p.drivers].sort((x, y) => y.win - x.win).slice(0, 2).map((d) => d.code) : [undefined, undefined];
  const { data } = useH2H(a, b, p?.race.id);
  const row = (label: string, x: number | null, y: number | null, f: (n: number) => string = (n) => String(n), lowerBetter = false, big = false) => {
    const xa = x == null ? "—" : f(x), ya = y == null ? "—" : f(y);
    const lead = x != null && y != null && x !== y ? ((x > y) !== lowerBetter ? 0 : 1) : -1;
    return (<div key={label} className="grid grid-cols-[1fr_1.2fr_1fr] items-center border-t border-edge py-2 text-center first:border-0">
      <b className={cx(big ? "text-[18px]" : "text-[12px]", lead === 0 && "text-glow")}>{xa}</b><span className="text-[10px] text-mute">{label}</span><b className={cx(big ? "text-[18px]" : "text-[12px]", lead === 1 && "text-glow")}>{ya}</b></div>);
  };
  return (
    <Card className="p-4">
      <CardTitle icon={<Swords size={13} />} title="Driver Head-to-Head" sub="Compare drivers and see detailed head-to-head stats" />
      {!data ? <Skeleton className="h-[270px]" /> : (<>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
          {[data.a, data.b].map((s, i) => (<div key={s.code} className={cx("flex items-center gap-2 rounded-lg border border-edge bg-black/20 p-2", i === 1 && "order-3")}>
            <Avatar code={s.code} team={s.team} size={36} /><div className="min-w-0"><div className="truncate text-[11px] font-bold">{s.name}</div><div className="truncate text-[9px] text-mute">{s.team.name}</div><Flag cc={s.cc} className="mt-0.5 h-2.5 w-4" /></div></div>))}
          <span className="order-2 text-[13px] font-black text-slate-300">VS</span>
        </div>
        <div className="mt-3 rounded-lg border border-edge px-2">
          {row("Points", data.a.points, data.b.points, String, false, true)}
          {row("Wins", data.a.wins, data.b.wins)}{row("Podiums", data.a.podiums, data.b.podiums)}
          {row("Avg. Quali", data.a.avg_quali, data.b.avg_quali, (n) => n.toFixed(1), true)}
          <div className="grid grid-cols-[1fr_1.2fr_1fr] items-center border-t border-edge py-2 text-center"><b className="text-[12px]">{data.record ? data.record[0] : "—"}</b><span className="text-[10px] text-mute">Head-to-Head</span><b className="text-[12px]">{data.record ? data.record[1] : "—"}</b></div>
        </div>
        <Link to={`/head2head?a=${data.a.code}&b=${data.b.code}`} className="btn-ghost mt-3 w-full">View Full Comparison <ArrowRight size={13} /></Link>
      </>)}
    </Card>
  );
}

export function SimPanel({ p, loading }: { p?: Prediction; loading: boolean }) {
  const { draft, setDraft, run } = useApp();
  const { data: races } = useRaces();
  const next = races?.find((r) => r.status !== "completed");
  return (
    <Card className="p-4">
      <CardTitle icon={<Play size={12} />} title="Race Simulation" sub="Run multiple simulations with custom settings" />
      <div className="grid grid-cols-2 gap-3 text-[11px]">
        <label><span className="mb-1 block">Simulations</span><input type="number" min={100} max={25000} step={500} className="field" value={draft.sims} onChange={(e) => setDraft({ sims: Math.min(25000, Math.max(100, Number(e.target.value) || 100)) })} /></label>
        <label><span className="mb-1 block">Session Type</span><select className="field" value={draft.session} onChange={(e) => setDraft({ session: e.target.value as typeof draft.session })}><option value="practice">Practice</option><option value="qualifying">Qualifying</option><option value="race">Race</option><option value="sprint">Sprint</option></select></label>
        <label><span className="mb-1 block">Grand Prix</span><select className="field" value={draft.race_id ?? next?.id ?? ""} onChange={(e) => setDraft({ race_id: e.target.value })}>{(races ?? []).map((r) => <option key={r.id} value={r.id}>{r.name.replace(" Grand Prix", " GP")}{r.status === "completed" ? " (done)" : ""}</option>)}</select></label>
        <label><span className="mb-1 block">Weather</span><select className="field" value={draft.weather} onChange={(e) => setDraft({ weather: e.target.value as typeof draft.weather })}><option value="auto">Auto (forecast)</option><option value="dry">Dry</option><option value="mixed">Mixed</option><option value="wet">Wet</option></select></label>
      </div>
      <div className="mt-4 space-y-3 text-[11px]">
        {([["Include Mechanical Failures", "mechanical_failures"], ["Include Safety Car", "safety_car"], ["Use AI Model (Enhanced)", "enhanced"]] as const).map(([l, k]) => (
          <div key={k} className="flex items-center justify-between"><span title={k === "enhanced" ? "Blends current-season form into the base driver and car ratings" : undefined}>{l}</span><Toggle checked={draft[k]} onChange={(v) => setDraft({ [k]: v })} label={l} /></div>))}
        <label className="block"><span className="mb-1 flex justify-between"><span>Chaos</span><b>{Math.round(draft.chaos * 100)}%</b></span><input type="range" min={0} max={1} step={0.05} value={draft.chaos} onChange={(e) => setDraft({ chaos: Number(e.target.value) })} className="w-full" /></label>
      </div>
      <button className="btn-red mt-4 w-full !py-2.5" onClick={() => run()} disabled={loading}>{loading ? <Loader2 size={14} className="animate-spin" /> : null}{loading ? "Simulating…" : "Run Simulation"}</button>
      {p && <p className="mt-2 text-center text-[10px] text-mute">{p.params.sims.toLocaleString()} simulations in {p.elapsed_ms} ms · weather: {p.params.weather}</p>}
    </Card>
  );
}

export function RecentRaces() {
  const { data } = useRecent();
  return (
    <Card className="p-4">
      <CardTitle icon={<FlagIcon size={12} />} title="Recent Races" right={<Link to="/predictions" className="text-[10px] text-mute hover:text-white">View All</Link>} />
      <div className="space-y-2">{!data ? [0, 1, 2].map((i) => <Skeleton key={i} className="h-10" />) : data.map((r) => (
        <div key={r.id} className="flex items-center gap-3 rounded-lg border border-edge bg-black/20 px-3 py-2 text-[11px]">
          <Flag cc={r.cc} className="h-4 w-6" /><span className="min-w-0 flex-1 truncate font-medium">{r.name.replace(" Grand Prix", " GP")}{r.next && <span className="text-mute"> (Next)</span>}</span>
          <span className="text-slate-300">{r.winner_name ? `1. ${surname(r.winner_name)}` : "1. ?"}</span><span className="w-10 text-right text-mute">{r.points ? `${r.points} pts` : "-"}</span></div>))}
        {data && !data.length && <p className="text-[11px] text-mute">No results yet.</p>}</div>
    </Card>
  );
}

export function QuickActions() {
  const items = [{ to: "/standings", icon: <Trophy size={16} className="text-glow" />, t: "View Standings", s: "Current driver & constructor standings" }, { to: "/head2head", icon: <b className="text-[13px] text-glow">VS</b>, t: "Head2Head", s: "Compare drivers & analyze stats" }, { to: "/fantasy", icon: <Users size={16} className="text-glow" />, t: "Fantasy League", s: "Build your team & join the league" }];
  return (
    <Card className="p-4">
      <CardTitle icon={<Zap size={12} />} title="Quick Actions" />
      <div className="grid gap-2 sm:grid-cols-3">{items.map((i) => (
        <Link key={i.to} to={i.to} className="rounded-lg border border-edge bg-black/20 p-3 transition hover:border-glow/60"><div className="mb-2">{i.icon}</div><div className="text-[11px] font-semibold">{i.t}</div><div className="text-[9px] leading-tight text-mute">{i.s}</div></Link>))}</div>
      <Link to="/settings" className="mt-2 flex items-center gap-3 rounded-lg border border-edge bg-black/20 p-3 text-[11px] transition hover:border-glow/60"><Cog size={15} className="text-glow" /><b>Settings</b><span className="ml-2 text-mute">Customize predictions & preferences</span></Link>
    </Card>
  );
}

export function Promo() {
  return (
    <Card className="keep-dark relative flex min-h-[170px] overflow-hidden">
      <img src="/img/promo-helmet.jpg" alt="" className="heavy-img h-full w-[42%] object-cover object-top" style={{ maskImage: "linear-gradient(to right, #000 60%, transparent)", WebkitMaskImage: "linear-gradient(to right, #000 60%, transparent)" }} />
      <div className="absolute inset-y-0 right-0 flex w-[62%] flex-col justify-center gap-3 p-4">
        <div className="flex items-center gap-2"><img src="/img/logo-f1.png" alt="" className="h-4 w-auto" /><span className="text-[10px] font-bold tracking-wider">F1 PREDICTOR 2026</span></div>
        <h3 className="text-[16px] font-extrabold uppercase leading-tight">Better data.<br />Smarter predictions.<br />Bigger races.</h3>
        <Link to="/predictions" className="btn-red self-start">Explore All Features <ArrowRight size={13} /></Link>
      </div>
    </Card>
  );
}
