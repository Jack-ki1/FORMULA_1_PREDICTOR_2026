import { useSearchParams } from "react-router-dom";
import { Avatar, Card, ErrorNote, Flag, Skeleton, cx, pct } from "../components/ui";
import { useDrivers, useH2H } from "../lib/hooks";
import { useApp } from "../lib/store";

export default function Head2Head() {
  const [sp, setSp] = useSearchParams();
  const a = (sp.get("a") ?? "VER").toUpperCase(), b = (sp.get("b") ?? (a === "NOR" ? "VER" : "NOR")).toUpperCase();
  const race = useApp((s) => s.applied.race_id);
  const { data: drivers } = useDrivers();
  const q = useH2H(a, b, race);
  const d = q.data;
  const set = (k: "a" | "b", v: string) => setSp({ a, b, [k]: v });
  const rows: { l: string; x: number | null; y: number | null; f?: (n: number) => string; low?: boolean }[] = d ? [
    { l: "Season points", x: d.a.points, y: d.b.points }, { l: "Wins", x: d.a.wins, y: d.b.wins }, { l: "Podiums", x: d.a.podiums, y: d.b.podiums },
    { l: "Avg. qualifying", x: d.a.avg_quali, y: d.b.avg_quali, f: (n) => n.toFixed(1), low: true },
    { l: "Win probability", x: d.a.win_prob, y: d.b.win_prob, f: (n) => pct(n) }, { l: "Podium probability", x: d.a.podium_prob, y: d.b.podium_prob, f: (n) => pct(n) },
    { l: "Pole probability", x: d.a.pole_prob, y: d.b.pole_prob, f: (n) => pct(n) }, { l: "Expected finish", x: d.a.exp_pos, y: d.b.exp_pos, f: (n) => n.toFixed(1), low: true }] : [];
  return (
    <div className="space-y-3 p-3.5">
      <h1 className="text-[20px] font-extrabold">Driver Head-to-Head{d ? ` · ${d.race.name}` : ""}</h1>
      <div className="grid gap-3 sm:grid-cols-2">{(["a", "b"] as const).map((k) => (
        <label key={k} className="text-[11px]"><span className="mb-1 block text-mute">Driver {k.toUpperCase()}</span>
          <select className="field" value={k === "a" ? a : b} onChange={(e) => set(k, e.target.value)}>{(drivers ?? []).map((x) => <option key={x.code} value={x.code} disabled={x.code === (k === "a" ? b : a)}>{x.name} — {x.team.name}</option>)}</select></label>))}</div>
      {q.isError && <ErrorNote error={q.error} retry={() => q.refetch()} />}
      {!d ? <Skeleton className="h-96" /> : (<Card className="p-4">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">{[d.a, d.b].map((s, i) => (
          <div key={s.code} className={cx("flex items-center gap-3", i === 1 && "order-3 flex-row-reverse text-right")}><Avatar code={s.code} team={s.team} size={56} />
            <div><div className="text-[16px] font-bold">{s.name}</div><div className="flex items-center gap-2 text-[11px] text-mute" style={i === 1 ? { justifyContent: "flex-end" } : undefined}><Flag cc={s.cc} className="h-2.5 w-4" />{s.team.name}</div></div></div>))}
          <span className="order-2 text-[20px] font-black text-slate-300">VS</span></div>
        <div className="mt-4">{rows.map((r) => {
          const f = r.f ?? String; const lead = r.x != null && r.y != null && r.x !== r.y ? ((r.x > r.y) !== !!r.low ? 0 : 1) : -1;
          return (<div key={r.l} className="grid grid-cols-[1fr_1.4fr_1fr] items-center border-t border-edge py-2.5 text-center"><b className={cx("text-[14px]", lead === 0 && "text-glow")}>{r.x == null ? "—" : f(r.x)}</b><span className="text-[11px] text-mute">{r.l}</span><b className={cx("text-[14px]", lead === 1 && "text-glow")}>{r.y == null ? "—" : f(r.y)}</b></div>);
        })}
          <div className="grid grid-cols-[1fr_1.4fr_1fr] items-center border-t border-edge py-2.5 text-center"><b className="text-[14px]">{d.record?.[0] ?? "—"}</b><span className="text-[11px] text-mute">Race head-to-head</span><b className="text-[14px]">{d.record?.[1] ?? "—"}</b></div></div>
        <p className="mt-2 text-[10px] text-mute">Wins, podiums, qualifying and race head-to-head need live season results; they show “—” in offline snapshot mode.</p></Card>)}
    </div>
  );
}
