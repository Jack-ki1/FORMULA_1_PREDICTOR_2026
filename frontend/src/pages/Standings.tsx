import { useSearchParams } from "react-router-dom";
import { Star } from "lucide-react";
import { Card, ErrorNote, Flag, Progress, Skeleton, TeamLogo, cx } from "../components/ui";
import { useApp } from "../lib/store";
import { useStandings } from "../lib/hooks";
import {
  StandingsCumulative, StandingsGapToLeader, StandingsWinsPodiumsDNFs, StandingsAvgGridVsFinish,
  StandingsFinishConsistency, StandingsPointsShare,
} from "../components/SessionPlots";

export default function Standings() {
  const [sp, setSp] = useSearchParams();
  const tab = sp.get("tab") === "constructors" ? "constructors" : "drivers";
  const q = useStandings();
  const { favDriver, favTeam } = useApp((x) => x.s);
  const s = q.data;
  const drivers = s?.drivers ?? [];
  const constructors = s?.constructors ?? [];
  const max = Math.max(1, ...(tab === "drivers" ? drivers.map((d) => d.points) : constructors.map((c) => c.points)) ?? [1]);
  const needsHistory = tab === "drivers" ? drivers.some((d) => !d.history) : constructors.some((c) => !c.history);
  return (
    <div className="space-y-3 p-3.5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><h1 className="text-[20px] font-extrabold">2026 Championship Standings</h1><p className="text-[11px] text-mute">{s ? `After round ${s.as_of_round} · ${s.source === "live" ? "live data" : "offline snapshot"}` : "Loading…"}</p></div>
        <div className="flex gap-1 rounded-lg border border-edge p-1" role="tablist">{(["drivers", "constructors"] as const).map((k) => <button key={k} role="tab" aria-selected={tab === k} onClick={() => setSp({ tab: k })} className={cx("rounded-md px-4 py-1.5 text-[12px] font-medium capitalize", tab === k ? "bg-gradient-to-r from-f1red to-glow text-white on-accent" : "text-slate-300 hover:bg-white/5")}>{k}</button>)}</div>
      </div>
      {s?.note && s.source === "seed" && <div className="card p-3 text-[11px] text-amber-200">{s.note}</div>}
      {q.isError && <ErrorNote error={q.error} retry={() => q.refetch()} />}
      {!s ? <Skeleton className="h-96" /> : (
        <>
          <Card className="overflow-x-auto p-3"><table className="w-full min-w-[520px] text-[12px]">
            <thead><tr className="text-left">{["POS", tab === "drivers" ? "DRIVER" : "TEAM", ...(tab === "drivers" ? ["TEAM"] : []), "WINS", "POINTS", ""].map((h, i) => <th key={i} className="label px-2 py-2 !text-[9px]">{h}</th>)}</tr></thead>
            <tbody>{tab === "drivers" ? drivers.map((d) => (
              <tr key={d.code} className={cx("border-t border-edge", d.team.id === favTeam && "bg-f1red/10")}><td className="px-2 py-2.5 font-bold">{d.pos}</td><td className="px-2"><span className="flex items-center gap-2"><Flag cc={d.cc} className="h-2.5 w-4" />{d.name}{d.code === favDriver && <Star size={12} className="fill-amber-300 text-amber-300" aria-label="Favorite driver" />}</span></td>
                <td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={d.team} size={14} />{d.team.name}</span></td><td className="px-2 tabular-nums">{d.wins ?? "—"}</td><td className="px-2 font-semibold tabular-nums">{d.points}</td><td className="w-40 px-2"><Progress value={d.points / max} /></td></tr>
            )) : constructors.map((c) => (
              <tr key={c.team.id} className={cx("border-t border-edge", c.team.id === favTeam && "bg-f1red/10")}><td className="px-2 py-2.5 font-bold">{c.pos}</td><td className="px-2"><span className="flex items-center gap-2"><TeamLogo team={c.team} size={14} />{c.team.name}</span></td>
                <td className="px-2 tabular-nums">{c.wins ?? "—"}</td><td className="px-2 font-semibold tabular-nums">{c.points}</td><td className="w-40 px-2"><Progress value={c.points / max} tone="violet" /></td></tr>
            ))}</tbody></table></Card>
          {s?.source === "seed" && <div className="card p-3 text-[11px] text-amber-200">Live round-by-round history unavailable in this data source — charts show available totals and fallbacks.</div>}
          <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
            <StandingsCumulative drivers={drivers} constructors={constructors} tab={tab} />
            <StandingsGapToLeader drivers={drivers} constructors={constructors} tab={tab} />
            <StandingsPointsShare drivers={drivers} constructors={constructors} tab={tab} />
            <StandingsWinsPodiumsDNFs drivers={drivers} tab={tab} />
            <StandingsAvgGridVsFinish drivers={drivers} tab={tab} />
            <StandingsFinishConsistency drivers={drivers} tab={tab} />
          </div>
        </>
      )}
    </div>
  );
}
