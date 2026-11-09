import { useSearchParams } from "react-router-dom";
import { Avatar, Card, ErrorNote, Flag, Skeleton, TeamLogo, cx, pct } from "../components/ui";
import { useDrivers, useH2H } from "../lib/hooks";
import { useApp } from "../lib/store";
import {
  H2HCompareBars, H2HOutcomeDiverging, H2HFinishProfile, H2HRadarCompare, H2HPointsHistogram, H2HSeasonCompare,
} from "../components/SessionPlots";

function stat(v: number | null | undefined, digits = 0, suffix = "") {
  if (v == null || Number.isNaN(v)) return "—";
  return `${digits ? v.toFixed(digits) : Math.round(v)}${suffix}`;
}

export default function Head2Head() {
  const [sp, setSp] = useSearchParams();
  const a = (sp.get("a") ?? "VER").toUpperCase(), b = (sp.get("b") ?? (a === "NOR" ? "VER" : "NOR")).toUpperCase();
  const { data: drivers } = useDrivers();
  const applied = useApp((s) => s.applied);
  const race = applied?.race_id ?? null;
  const body = applied ? { sims: applied.sims, session: applied.session, sub: applied.sub, weather: applied.weather, grid_mode: applied.grid_mode, grid: applied.grid } : undefined;
  const q = useH2H(a, b, race, body);
  const d = q.data;
  const set = (k: "a" | "b", v: string) => setSp({ a, b, [k]: v });
  const rows = d ? [
    { label: "Season points", a: stat(d.a.season_points ?? d.a.points), b: stat(d.b.season_points ?? d.b.points) },
    { label: "Wins", a: stat(d.a.wins), b: stat(d.b.wins) },
    { label: "Podiums", a: stat(d.a.podiums), b: stat(d.b.podiums) },
    { label: "Avg. qualifying", a: stat(d.a.avg_quali_season ?? d.a.avg_quali, 1), b: stat(d.b.avg_quali_season ?? d.b.avg_quali, 1) },
    { label: "Win probability", a: pct(d.a.win_prob), b: pct(d.b.win_prob) },
    { label: "Podium probability", a: pct(d.a.podium_prob), b: pct(d.b.podium_prob) },
    { label: "Pole probability", a: pct(d.a.pole_prob), b: pct(d.b.pole_prob) },
    { label: "Expected finish", a: stat(d.a.exp_pos, 1), b: stat(d.b.exp_pos, 1) },
    { label: "Race head-to-head", a: stat(d.record?.[0]), b: stat(d.record?.[1]) },
  ] : [];

  return (
    <div className="space-y-3 p-3.5">
      <h1 className="text-[20px] font-extrabold">Driver Head-to-Head{d ? ` · ${d.race.name}` : ""}</h1>
      <div className="card p-3 text-[11px] text-mute">{applied ? "Using Dashboard run params" : "Using default settings"} · POST /api/v1/h2h</div>
      <div className="grid gap-3 sm:grid-cols-2">{(["a", "b"] as const).map((k) => (
        <label key={k} className="text-[11px]"><span className="mb-1 block text-mute">Driver {k.toUpperCase()}</span>
          <select className="field" value={k === "a" ? a : b} onChange={(e) => set(k, e.target.value)}>{(drivers ?? []).map((x) => <option key={x.code} value={x.code} disabled={x.code === (k === "a" ? b : a)}>{x.name} — {x.team.name}</option>)}</select></label>))}</div>
      {q.isError && <ErrorNote error={q.error} retry={() => q.refetch()} />}
      {!d ? <Skeleton className="h-[400px]" /> : (
        <>
          <Card className="p-4">
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
              {[d.a, d.b].map((s: any, i: number) => (
                <div key={s.code} className={cx("flex items-center gap-3", i === 1 && "order-3 flex-row-reverse text-right")}>
                  <Avatar code={s.code} team={s.team} size={56} />
                  <div><div className="text-[16px] font-bold">{s.name}</div><div className="flex items-center gap-2 text-[11px] text-mute" style={i === 1 ? { justifyContent: "flex-end" } : undefined}><TeamLogo team={s.team} size={12} /><Flag cc={s.cc} className="h-2.5 w-4" />{s.team.name}</div></div>
                </div>
              ))}
              <span className="order-2 text-[20px] font-black text-slate-300">VS</span>
            </div>
            <div className="mt-4 overflow-hidden rounded-lg border border-edge">
              <div className="grid grid-cols-[1fr_1.3fr_1fr] bg-white/[0.03] px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-mute"><span className="text-left">{d.a.code}</span><span className="text-center">Metric</span><span className="text-right">{d.b.code}</span></div>
              {rows.map((r) => (
                <div key={r.label} className="grid grid-cols-[1fr_1.3fr_1fr] border-t border-edge px-3 py-2 text-[11px]">
                  <b className="tabular-nums text-glow">{r.a}</b><span className="text-center text-mute">{r.label}</span><b className="text-right tabular-nums text-glow">{r.b}</b>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-center text-[10px] sm:grid-cols-4">
              <div className="rounded-lg border border-edge bg-black/20 p-2"><div className="text-mute">P({d.a.code} ahead)</div><b className="text-[12px]">{d.pair ? pct(d.pair.p_a_ahead) : "—"}</b></div>
              <div className="rounded-lg border border-edge bg-black/20 p-2"><div className="text-mute">P({d.b.code} ahead)</div><b className="text-[12px]">{d.pair ? pct(d.pair.p_b_ahead) : "—"}</b></div>
              <div className="rounded-lg border border-edge bg-black/20 p-2"><div className="text-mute">Both DNF</div><b className="text-[12px]">{d.pair ? pct(d.pair.p_both_dnf) : "—"}</b></div>
              <div className="rounded-lg border border-edge bg-black/20 p-2"><div className="text-mute">Both Podium</div><b className="text-[12px]">{d.pair ? pct(d.pair.p_both_podium) : "—"}</b></div>
            </div>
          </Card>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <H2HCompareBars a={d.a} b={d.b} />
            <H2HOutcomeDiverging a={d.a} b={d.b} />
            <H2HFinishProfile a={d.a} b={d.b} />
            <H2HRadarCompare a={d.a} b={d.b} />
            <H2HPointsHistogram a={d.a} b={d.b} />
            <H2HSeasonCompare a={d.a} b={d.b} />
          </div>
        </>
      )}
    </div>
  );
}
