import { Flame, Rocket, Timer } from "lucide-react";
import type { DriverPred, Prediction, Team } from "../lib/api";
import { headlineWord, sessionWord, short } from "../lib/util";
import { Avatar, Card, CardTitle, Flag, Skeleton, TeamLogo, cx, pct, surname } from "../components/ui";
import { DonutChart, HBar, VBar, ScatterXY, RangeBar, RadarChart, DivergingBar, Histogram, Gauge, StackedBar, LineSeries, ChartCard } from "../charts";

function emptyCard(title: string, sub: string, icon: React.ReactNode) {
  return (
    <Card className="p-4">
      <CardTitle icon={icon} title={title} sub={sub} />
      <div className="h-64 flex flex-col items-center justify-center rounded-lg border border-dashed border-edge p-4 text-center">
        <div className="mb-2 text-[11px] text-slate-400">No data available yet</div>
        <div className="text-[10px] text-slate-500">Set simulations and press Run Prediction.</div>
      </div>
    </Card>
  );
}

function withData<T extends { p?: Prediction; loading?: boolean }>(Component: React.FC<T>, title: string, sub: string, icon: React.ReactNode) {
  return (props: T) => {
    const { p, loading } = props as any;
    if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard(title, sub, icon);
    return <Component {...(props as any)} />;
  };
}

// ================= PRACTICE PLOTS =================

export function PracticePaceGap({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Pace Gap (p10–p90)", "Projected lap-time spread vs session best", <Timer size={13} />);
  const rows = p.drivers;
  const max = Math.max(...rows.map((d) => d.pace_hi ?? 0), 0.1);
  const data = rows.map((d) => ({
    name: d.code, value: d.pace_gap ?? 0, p10: d.pace_lo ?? 0, p50: d.pace_gap ?? 0, p90: d.pace_hi ?? 0, mean: d.pace_gap ?? 0, team: d.team, color: d.team.color,
  }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Pace Gap — p10 to p90 Whiskers" sub="Projected lap-time gap to session-best; bar = average" />
      <RangeBar data={data} height={320} />
    </Card>
  );
}

export function PracticeFastestDonut({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Fastest Driver by Team", "Share of projected fastest laps by constructor", <Flame size={13} />);
  const byTeam: Record<string, number> = {};
  p.drivers.forEach((d) => { byTeam[d.team.id] = (byTeam[d.team.id] || 0) + (d.win ?? 0); });
  const data = Object.entries(byTeam).map(([id, v]) => {
    const t = p.drivers.find((d) => d.team.id === id)!.team;
    return { name: t.name, value: v, team: t, color: t.color };
  }).sort((a, b) => b.value - a.value);
  const total = data.reduce((s, d) => s + d.value, 0).toFixed(2);
  return (
    <Card className="p-4">
      <CardTitle icon={<Flame size={13} />} title="Fastest-Driver Share by Team" sub="Model probability of setting the fastest lap, grouped by constructor" />
      <DonutChart data={data} total={total} height={300} />
    </Card>
  );
}

export function PracticeOneLapVsLongRun({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("One-Lap vs Long-Run", "Single-lap pace (x) vs race-pace consistency (y)", <Timer size={13} />);
  const rows = p.drivers;
  const data = rows.map((d) => ({
    name: d.code, x: d.pace_gap ?? 0, y: d.long_gap ?? 0, team: d.team, color: d.team.color,
  }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="One-Lap vs Long-Run Pace" sub="X = single-lap gap to best · Y = long-run gap. FP1: low confidence — new track" />
      <ScatterXY data={data} xLabel="One-lap gap (s)" yLabel="Long-run gap (s)" height={300} />
    </Card>
  );
}

export function PracticeTeamPaceLadder({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Team Pace Ladder", "Best projected pace gap per team, with teammate gap", <Flame size={13} />);
  const byTeam: Record<string, { min: number; a: string; b: string; ga: number; gb: number }> = {};
  p.drivers.forEach((d) => {
    const t = byTeam[d.team.id] || { min: Infinity, a: d.code, b: d.code, ga: 0, gb: 0 };
    if ((d.pace_gap ?? 0) < t.min) { t.min = d.pace_gap ?? 0; t.a = d.code; t.ga = d.pace_gap ?? 0; }
    else { t.b = d.code; t.gb = d.pace_gap ?? 0; }
    byTeam[d.team.id] = t;
  });
  const data = Object.entries(byTeam).map(([id, v]) => {
    const t = p.drivers.find((d) => d.team.id === id)!.team;
    return { name: t.name, a: v.min, b: Math.abs(v.ga - v.gb), aLabel: "Pace gap", bLabel: "Teammate gap", team: t, color: t.color };
  }).sort((a, b) => a.a - b.a);
  return (
    <Card className="p-4">
      <CardTitle icon={<Flame size={13} />} title="Team Pace Ladder + Teammate Gap" sub="Bar = best pace gap per team · stacked segment = gap between teammates" />
      <StackedBar data={data} height={300} />
    </Card>
  );
}

export function PracticeTop3Top10({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Top-3 / Top-10 Probability", "Chance of finishing in the top 3 or top 10", <Timer size={13} />);
  const rows = p.drivers;
  const data = rows.map((d) => ({
    name: d.code, value: d.top3 ?? 0, team: d.team, color: d.team.color,
  })).sort((a, b) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Top-3 Probability by Driver" sub="Model chance of finishing in the top 3 in this practice session" />
      <VBar data={data} height={300} valueFmt={(v) => pct(v)} />
    </Card>
  );
}

// ================= QUALIFYING PLOTS =================

export function QualiSurvivalFunnel({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Q1 → Q2 → Q3 Survival", "Probability of surviving each qualifying segment", <Rocket size={13} />);
  const rows = p.drivers;
  const data = rows.map((d) => ({
    name: d.code, a: d.reach_q2 ?? 0, b: d.reach_q3 ?? 0, aLabel: "Reach Q2", bLabel: "Reach Q3", team: d.team, color: d.team.color,
  })).sort((a, b) => b.b - b.a);
  return (
    <Card className="p-4">
      <CardTitle icon={<Rocket size={13} />} title="Qualifying Survival Funnel" sub="Probability of reaching Q2 and Q3" />
      <StackedBar data={data} height={320} />
    </Card>
  );
}

export function QualiGapToPole({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Gap to Pole", "Projected gap to pole position", <Timer size={13} />);
  const rows = p.drivers;
  const data = rows.map((d) => ({ name: d.code, value: d.gap ?? 0, team: d.team, color: d.team.color })).sort((a, b) => a.value - b.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Gap to Pole" sub="Estimated seconds off pole time (placeholder anchors)" />
      <HBar data={data} height={320} valueFmt={(v) => `+${v.toFixed(3)}s`} />
    </Card>
  );
}

export function QualiPoleDonut({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Pole Probability", "Chance of taking pole position", <Timer size={13} />);
  const rows = p.drivers;
  const data = rows.map((d) => ({ name: d.code, value: d.pole ?? 0, team: d.team, color: d.team.color })).sort((a, b) => b.value - a.value);
  const total = data.reduce((s, d) => s + d.value, 0).toFixed(2);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Pole Probability Donut" sub="Chance of each driver taking pole" />
      <DonutChart data={data} total={total} height={300} />
    </Card>
  );
}

export function QualiTeammateBattle({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Teammate Battle", "Probability the first-listed teammate qualifies ahead", <Timer size={13} />);
  const battles = p.quali_segments?.teammate_battle ?? [];
  const data = battles.map((b: any) => {
    const drv = p.drivers.find((d: any) => d.code === b.a);
    return {
      name: `${b.a} vs ${b.b}`,
      value: b.p_a_ahead,
      team: drv?.team ?? { id: b.a, name: b.a, color: "#8d99b5" },
      color: drv?.team?.color,
    };
  }).sort((a: any, b: any) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Teammate Qualifying Battle" sub="P(A qualifies ahead of B) for each team pairing" />
      <HBar data={data} height={320} valueFmt={(v) => pct(v)} />
    </Card>
  );
}

export function QualiBothInQ3({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Both in Q3", "Chance both cars of a team reach Q3", <Timer size={13} />);
  const both = p.quali_segments?.both_in_q3 ?? [];
  const data = both.map((b: any) => ({ name: b.team, value: b.p, color: p.drivers.find((d: any) => d.team.name === b.team)?.team?.color })).sort((a: any, b: any) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Both Cars in Q3" sub="Chance that both teammates advance to Q3" />
      <VBar data={data} height={300} valueFmt={(v) => pct(v)} />
    </Card>
  );
}

// ================= RACE & SPRINT PLOTS =================

const TEAM_COLORS = ["#27F4D2","#E8002D","#FF8000","#3671C6","#6692FF","#FF87BC","#64C4FF","#B6BABD","#9B1C31","#229971","#C9A227","#7C4DFF","#22C55E","#06B6D4"];

export function RaceTeamWinShare({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Team Win-Share", "Share of race-win probability by constructor", <Flame size={13} />);
  const data = (p.team_ranges ?? []).map((t: any, i: number) => {
    const drv = p.drivers.find((d: any) => d.team.name === t.team);
    const team = drv?.team ?? { id: String(t.team || i).toLowerCase().replace(/\s+/g, "_"), name: String(t.team), color: TEAM_COLORS[i % TEAM_COLORS.length] };
    const color = team.color && team.color !== "#8d99b5" ? team.color : TEAM_COLORS[i % TEAM_COLORS.length];
    return { name: team.name, value: Number(t.win_share ?? 0), team: { ...team, color }, color, desc: `Combined win chance for both ${team.name} cars` };
  }).filter((d: any) => d.value > 0).sort((a: any, b: any) => b.value - a.value);
  const total = data.reduce((s: number, d: any) => s + d.value, 0);
  return (
    <Card className="p-4">
      <CardTitle icon={<Flame size={13} />} title="Team Win-Share Donut" sub="Combined win probability of each constructor's cars (key below)" />
      <DonutChart data={data} total={pct(total || 1)} height={340} showLegend />
    </Card>
  );
}

export function RaceGridToWin({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Grid → Win Conversion", "Win probability by starting grid slot", <Timer size={13} />);
  const winByGrid = p.win_by_grid ?? [];
  const data = winByGrid.map((v: number, i: number) => ({ name: `P${i + 1}`, value: v, color: i < 3 ? "#e10600" : "#7c4dff" }));
  if (!data.length) return emptyCard("Grid → Win Conversion", "Win probability by starting grid slot", <Timer size={13} />);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Grid Slot → Win Conversion" sub="Win probability by starting grid slot (model output)" />
      <VBar data={data} height={300} valueFmt={(v) => pct(v)} />
    </Card>
  );
}

export function RacePositionsGainedLost({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Positions Gained/Lost", "Average grid-to-finish change per driver", <Timer size={13} />);
  const rows = p.drivers;
  const data = rows.map((d: DriverPred) => ({ name: d.code, value: d.avg_gain ?? 0, team: d.team, color: d.team.color })).sort((a: any, b: any) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Positions Gained vs Lost" sub="Positive = gains from grid · negative = losses. Diverging bar." />
      <DivergingBar data={data} height={320} valueFmt={(v) => v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1)} />
    </Card>
  );
}

export function RaceScenarioDonut({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Race Scenario", "Clean / Safety Car / Attritional race split", <Timer size={13} />);
  const sc = p.scenario ?? { clean: 0.6, safety_car: 0.3, attritional: 0.1 };
  const data = [
    { name: "Clean", value: sc.clean, color: "#22c55e", desc: "No safety-car interruption and limited attrition in the simulated race." },
    { name: "Safety Car", value: sc.safety_car, color: "#f59e0b", desc: "At least one safety-car/neutralisation event affected race strategy or order." },
    { name: "Attritional (≥3 DNF)", value: sc.attritional, color: "#ef4444", desc: "High-attrition race with 3 or more DNFs, increasing variance and opportunity." },
  ];
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Race Scenario Split" sub={`${Math.round(p.safety_car_rate * 100)}% of simulated races had a safety car`} />
      <DonutChart data={data} showLegend height={320} />
    </Card>
  );
}

export function RaceWinGivenSC({ p, loading }: { p?: Prediction; loading?: boolean }) {
  if (!p) return loading ? <Skeleton className="h-64" /> : emptyCard("Win Given Safety Car", "Win probability with vs without safety car", <Timer size={13} />);
  const rows = [...p.drivers].sort((a, b) => Math.abs((b.win_sc ?? 0) - (b.win_nosc ?? 0)) - Math.abs((a.win_sc ?? 0) - (a.win_nosc ?? 0))).slice(0, 8);
  const data = rows.map((d) => ({ name: d.code, a: d.win_sc ?? 0, b: d.win_nosc ?? 0, aLabel: "With SC", bLabel: "No SC", team: d.team, color: d.team.color }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Safety-Car Sensitivity" sub="Drivers most affected by safety-car vs no-safety-car win probability" />
      <StackedBar data={data} height={300} />
    </Card>
  );
}

// ================= STANDINGS PLOTS =================

export function StandingsCumulative({ drivers, constructors, tab }: { drivers: any[]; constructors: any[]; tab: string }) {
  const list = (tab === "drivers" ? drivers : constructors).slice(0, 8);
  const hasHistory = list.some((x: any) => Array.isArray(x.history) && x.history.length);
  if (hasHistory) {
    const rounds = Array.from(new Set(list.flatMap((x: any) => (x.history ?? []).map((h: any) => h.round)))).sort((a, b) => a - b) as number[];
    const data: Array<{ name: string } & Record<string, string | number>> = rounds.map((r) => {
      const row: { name: string } & Record<string, string | number> = { name: `R${r}` };
      list.forEach((x: any) => {
        const key = tab === "drivers" ? String(x.code) : String(x.team?.name ?? x.team ?? "");
        row[key] = Number((x.history ?? []).find((h: any) => h.round === r)?.points ?? 0);
      });
      return row;
    });
    const series = list.map((x: any, i: number) => ({
      key: tab === "drivers" ? String(x.code) : String(x.team?.name ?? x.team ?? ""),
      label: tab === "drivers" ? String(x.code) : String(x.team?.name ?? x.team ?? ""),
      color: x.team?.color ?? `hsl(${(i * 47) % 360},70%,55%)`,
    }));
    return (
      <Card className="p-4">
        <CardTitle icon={<Timer size={13} />} title={`Cumulative Points — ${tab === "drivers" ? "Drivers" : "Constructors"}`} sub="Round-by-round progression (live history)" />
        <LineSeries data={data} series={series} height={300} />
      </Card>
    );
  }
  const data = list.map((x: any) => ({ name: tab === "drivers" ? x.code : (x.team?.name ?? String(x.team)), value: x.points ?? 0, team: x.team, color: x.team?.color })).sort((a: any, b: any) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Points Ladder — ${tab === "drivers" ? "Drivers" : "Constructors"}`} sub="Live round history unavailable; showing current totals" />
      <VBar data={data} height={300} valueFmt={(v) => `${v.toFixed(0)} pts`} />
    </Card>
  );
}

export function StandingsGapToLeader({ drivers, constructors, tab }: { drivers: any[]; constructors: any[]; tab: string }) {
  const list = tab === "drivers" ? drivers : constructors;
  const leader = Math.max(1, ...list.map((x) => x.points ?? 0));
  const data = list.map((x) => ({ name: tab === "drivers" ? x.code : (x.team?.name ?? String(x.team)), value: leader - (x.points ?? 0), team: x.team, color: x.team?.color }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Gap to Leader — ${tab === "drivers" ? "Drivers" : "Constructors"}`} sub="Points behind leader" />
      <HBar data={data.sort((a: any, b: any) => a.value - b.value)} height={300} valueFmt={(v) => `${v.toFixed(0)} pts`} />
    </Card>
  );
}

export function StandingsWinsPodiumsDNFs({ drivers, tab }: { drivers: any[]; tab: string }) {
  if (!drivers.length) return emptyCard("Wins / Podiums / DNFs", "Needs live data", <Timer size={13} />);
  const data = drivers.map((d: any) => ({ name: d.code, a: d.wins ?? 0, b: d.podiums ?? 0, aLabel: "Wins", bLabel: "Podiums", team: d.team, color: d.team?.color }));
  const data2 = drivers.map((d: any) => ({ name: d.code, a: d.points_finishes ?? 0, b: d.dnfs ?? 0, aLabel: "Points Finishes", bLabel: "DNFs", team: d.team, color: d.team?.color }));
  const has2 = data2.some((d) => d.a || d.b);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Wins / Podiums${has2 ? " / Points-DNFs" : ""} — Drivers`} sub={tab === "constructors" ? "Driver-level view" : "Per driver"} />
      <div className="space-y-3">
        <StackedBar data={data} height={220} />
        {has2 && <StackedBar data={data2} height={220} />}
      </div>
    </Card>
  );
}

export function StandingsAvgGridVsFinish({ drivers, tab }: { drivers: any[]; tab: string }) {
  const data = drivers.filter((d: any) => d.avg_grid != null && d.avg_finish != null).map((d: any) => ({ name: d.code, x: d.avg_grid, y: d.avg_finish, team: d.team, color: d.team?.color }));
  if (data.length) return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Avg Grid vs Avg Finish — ${tab === "drivers" ? "Drivers" : "Constructors"}`} sub="Lower = better" />
      <ScatterXY data={data} xLabel="Avg Grid" yLabel="Avg Finish" height={300} />
    </Card>
  );
  const fallback = drivers.map((d: any) => ({ name: d.code, value: d.points ?? 0, team: d.team, color: d.team?.color })).sort((a: any, b: any) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Points Contribution — Drivers`} sub="Live grid/finish history unavailable; showing points" />
      <HBar data={fallback} height={300} valueFmt={(v) => `${v.toFixed(0)} pts`} />
    </Card>
  );
}

export function StandingsFinishConsistency({ drivers, tab }: { drivers: any[]; tab: string }) {
  const data = drivers.filter((d: any) => d.avg_finish != null).map((d: any) => ({ name: d.code, value: d.avg_finish, team: d.team, color: d.team?.color })).sort((a: any, b: any) => a.value - b.value);
  if (data.length) return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Average Finish Position — ${tab === "drivers" ? "Drivers" : "Constructors"}`} sub="Lower = better" />
      <HBar data={data} height={300} valueFmt={(v) => `P${v.toFixed(1)}`} />
    </Card>
  );
  const fallback = drivers.map((d: any) => ({ name: d.code, value: d.wins ?? 0, team: d.team, color: d.team?.color })).sort((a: any, b: any) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Wins by Driver`} sub="Live finish history unavailable; showing wins" />
      <VBar data={fallback} height={300} valueFmt={(v) => `${v.toFixed(0)}`} />
    </Card>
  );
}

export function StandingsPointsShare({ drivers, constructors, tab }: { drivers: any[]; constructors: any[]; tab: string }) {
  const list = tab === "drivers" ? drivers : constructors;
  const data = list.map((x: any) => ({ name: tab === "drivers" ? (x.name ?? x.code) : (x.team?.name ?? String(x.team)), value: x.points ?? 0, team: x.team, color: x.team?.color, desc: `${x.points ?? 0} championship points` })).filter((d: any) => d.value > 0).sort((a: any, b: any) => b.value - a.value);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title={`Share of Total Points — ${tab === "drivers" ? "Drivers" : "Constructors"}`} sub="Legend shows each entry and share (no hover required)" />
      <DonutChart data={data} showLegend height={340} />
    </Card>
  );
}

// ================= H2H PLOTS =================

export function H2HCompareBars({ a, b }: { a: any; b: any }) {
  const rows = [
    { label: "Win %", av: (a.win_prob ?? 0) * 100, bv: (b.win_prob ?? 0) * 100 },
    { label: "Podium %", av: (a.podium_prob ?? 0) * 100, bv: (b.podium_prob ?? 0) * 100 },
    { label: "Pole %", av: (a.pole_prob ?? 0) * 100, bv: (b.pole_prob ?? 0) * 100 },
    { label: "Points %", av: (a.points_prob ?? 0) * 100, bv: (b.points_prob ?? 0) * 100 },
    { label: "Exp finish", av: a.exp_pos ?? 0, bv: b.exp_pos ?? 0, invert: true },
  ];
  const max = Math.max(...rows.flatMap((r) => [r.av, r.bv]), 1);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Prediction Comparison" sub="Core model probabilities for both drivers" />
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.label} className="grid grid-cols-[72px_1fr_44px_44px_1fr_72px] items-center gap-1 text-[10px]">
            <span className="text-right text-slate-300">{r.label}</span>
            <div className="h-2.5 overflow-hidden rounded-full bg-white/[0.06]"><div className="ml-auto h-full rounded-full" style={{ width: `${(r.av / max) * 100}%`, background: a.team?.color ?? "#e10600" }} /></div>
            <b className="tabular-nums text-right">{r.invert ? r.av.toFixed(1) : `${r.av.toFixed(1)}%`}</b>
            <b className="tabular-nums">{r.invert ? r.bv.toFixed(1) : `${r.bv.toFixed(1)}%`}</b>
            <div className="h-2.5 overflow-hidden rounded-full bg-white/[0.06]"><div className="h-full rounded-full" style={{ width: `${(r.bv / max) * 100}%`, background: b.team?.color ?? "#3b82f6" }} /></div>
            <span className="text-slate-300">{a.code} / {b.code}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function H2HOutcomeDiverging({ a, b }: { a: any; b: any }) {
  const rows = [
    { label: "Win", av: (a.win_prob ?? 0) * 100, bv: (b.win_prob ?? 0) * 100 },
    { label: "Podium", av: (a.podium_prob ?? 0) * 100, bv: (b.podium_prob ?? 0) * 100 },
    { label: "Points", av: (a.points_prob ?? 0) * 100, bv: (b.points_prob ?? 0) * 100 },
    { label: "DNF", av: (a.dnf ?? 0) * 100, bv: (b.dnf ?? 0) * 100 },
    { label: "Outside pts", av: Math.max(0, 100 - (a.points_prob ?? 0) * 100 - (a.dnf ?? 0) * 100), bv: Math.max(0, 100 - (b.points_prob ?? 0) * 100 - (b.dnf ?? 0) * 100) },
  ];
  const max = Math.max(...rows.flatMap((r) => [r.av, r.bv]), 1);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Outcome Profile (Both Drivers)" sub={`${a.code} left · ${b.code} right`} />
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.label} className="grid grid-cols-[70px_1fr_56px_1fr_70px] items-center gap-1.5 text-[10px]">
            <span className="text-right text-slate-300">{r.label}</span>
            <div className="relative h-3 overflow-hidden rounded-full bg-white/[0.06]"><div className="absolute inset-y-0 right-0 rounded-full" style={{ width: `${(r.av / max) * 100}%`, background: a.team?.color ?? "#e10600" }} /></div>
            <span className="text-center tabular-nums text-slate-200">{r.av.toFixed(1)} / {r.bv.toFixed(1)}</span>
            <div className="h-3 overflow-hidden rounded-full bg-white/[0.06]"><div className="h-full rounded-full" style={{ width: `${(r.bv / max) * 100}%`, background: b.team?.color ?? "#3b82f6" }} /></div>
            <span />
          </div>
        ))}
      </div>
    </Card>
  );
}

export function H2HFinishProfile({ a, b }: { a: any; b: any }) {
  const da = a?.full_dist?.length ? a.full_dist : (a?.dist ?? []);
  const db = b?.full_dist?.length ? b.full_dist : (b?.dist ?? []);
  const len = Math.max(da.length, db.length);
  if (!len) return emptyCard("Finish Profile", "P1→P22 finish probabilities for both drivers", <Timer size={13} />);
  const data = Array.from({ length: Math.min(len, 22) }, (_, i) => ({
    name: `P${i + 1}`,
    [a.code]: Number(da[i] ?? 0),
    [b.code]: Number(db[i] ?? 0),
  }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Finish Position Profile" sub="Classified finishing probability by position for both drivers" />
      <StackedBar data={data.map((d) => ({ name: d.name, a: (d[a.code] as number) ?? 0, b: (d[b.code] as number) ?? 0, aLabel: a.code, bLabel: b.code }))} height={280} />
    </Card>
  );
}

export function H2HRadarCompare({ a, b }: { a: any; b: any }) {
  const r = (x: any) => x?.ratings || { pace: Math.max(0, 100 - (x?.exp_pos ?? 11) * 4), skill: Math.max(0, (x?.points_prob ?? x?.podium_prob ?? 0) * 100), wet: 50, rel: Math.max(0, 100 - (x?.dnf ?? 0) * 100), form: Math.max(0, (x?.avg_points ?? 0) * 4) };
  const ra = r(a), rb = r(b);
  if (!ra || !rb) return emptyCard("Ratings Radar", "Pace / Skill / Wet / Reliability / Form", <Timer size={13} />);
  const axes = [{ key: "pace", label: "Pace" }, { key: "skill", label: "Skill" }, { key: "wet", label: "Wet" }, { key: "rel", label: "Reliability" }, { key: "form", label: "Form" }];
  const data = [
    { name: a.code, pace: ra.pace, skill: ra.skill, wet: ra.wet, rel: ra.rel, form: ra.form },
    { name: b.code, pace: rb.pace, skill: rb.skill, wet: rb.wet, rel: rb.rel, form: rb.form },
  ];
  const has = data.some((d) => axes.some((x) => Number((d as any)[x.key] ?? 0) > 0));
  if (!has) return emptyCard("Ratings Radar", "Pace / Skill / Wet / Reliability / Form", <Timer size={13} />);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Ratings Radar (Both)" sub="Model-derived comparison" />
      <RadarChart data={data as any} axes={axes} height={280} />
    </Card>
  );
}

export function H2HPointsHistogram({ a, b }: { a: any; b: any }) {
  const vals = a.pts_values?.length ? a.pts_values : b.pts_values?.length ? b.pts_values : [25,18,15,12,10,8,6,4,2,1,0];
  const pa = a?.pts_dist?.length ? a.pts_dist : [];
  const pb = b?.pts_dist?.length ? b.pts_dist : [];
  if (!pa.length && !pb.length) {
    // fallback from avg/win/podium when pts distribution missing
    const mk = (x: any) => [x?.win ?? 0, 0, 0, (x?.podium ?? 0) - (x?.win ?? 0), 0, 0, 0, 0, 0, Math.max(0, (x?.points_prob ?? 0) - (x?.podium ?? 0)), Math.max(0, 1 - (x?.points_prob ?? 0) - (x?.dnf ?? 0))];
    const fa = mk(a), fb = mk(b);
    const data = vals.map((v: number, i: number) => ({ name: String(v), a: Number(fa[i] ?? 0), b: Number(fb[i] ?? 0), aLabel: a.code, bLabel: b.code })).filter((d: any) => d.a > 0.001 || d.b > 0.001);
    if (!data.length) return emptyCard("Points Distribution", "Simulated points distribution for both drivers", <Timer size={13} />);
    return (
      <Card className="p-4">
        <CardTitle icon={<Timer size={13} />} title="Points Distribution (Both)" sub="Model probability by points outcome" />
        <StackedBar data={data} height={280} />
      </Card>
    );
  }
  const data = vals.map((v: number, i: number) => ({ name: String(v), a: Number(pa[i] ?? 0), b: Number(pb[i] ?? 0), aLabel: a.code, bLabel: b.code })).filter((d: any) => d.a > 0.001 || d.b > 0.001);
  if (!data.length) return emptyCard("Points Distribution", "Simulated points distribution for both drivers", <Timer size={13} />);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Points Distribution (Both)" sub="Probability of each points tally" />
      <StackedBar data={data} height={280} />
    </Card>
  );
}

export function H2HSeasonCompare({ a, b }: { a: any; b: any }) {
  const ah = Array.isArray(a.history) ? a.history : [];
  const bh = Array.isArray(b.history) ? b.history : [];
  const rounds = Array.from(new Set([...ah.map((x: any) => x.round), ...bh.map((x: any) => x.round)])).sort((x: number, y: number) => x - y);
  if (!rounds.length) {
    const data = [
      { name: "Exp pts", a: a.avg_points ?? 0, b: b.avg_points ?? 0, aLabel: a.code, bLabel: b.code },
      { name: "Win%", a: (a.win_prob ?? 0) * 100, b: (b.win_prob ?? 0) * 100, aLabel: a.code, bLabel: b.code },
      { name: "Podium%", a: (a.podium_prob ?? 0) * 100, b: (b.podium_prob ?? 0) * 100, aLabel: a.code, bLabel: b.code },
    ];
    return (
      <Card className="p-4">
        <CardTitle icon={<Timer size={13} />} title="Model Summary (Both)" sub="Live season history unavailable; comparing model outputs" />
        <StackedBar data={data} height={280} />
      </Card>
    );
  }
  const data: Array<{ name: string } & Record<string, string | number>> = rounds.map((r) => ({
    name: `R${r}`,
    [a.code]: Number(ah.find((x: any) => x.round === r)?.points ?? 0),
    [b.code]: Number(bh.find((x: any) => x.round === r)?.points ?? 0),
  }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Season Progress (Both)" sub="Cumulative/live round points" />
      <LineSeries data={data} series={[{ key: a.code, label: a.code, color: a.team?.color }, { key: b.code, label: b.code, color: b.team?.color }]} height={280} />
    </Card>
  );
}

// ================= FANTASY PLOTS =================

export function FantasyBudgetGauge({ spent, budget }: { spent: number; budget: number }) {
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Budget Gauge" sub="Spent vs total budget" />
      <Gauge value={budget ? (spent / budget) * 100 : 0} min={0} max={100} label={`${spent.toFixed(1)}M / ${budget.toFixed(0)}M`} height={200} />
    </Card>
  );
}

export function FantasyExpectedVsPool({ team, poolMedian }: { team: number; poolMedian: number }) {
  const data = [
    { name: "Your Team", value: team, color: "#e10600" },
    { name: "Pool Median", value: poolMedian, color: "#7c4dff" },
  ];
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Expected Points vs Pool Median" sub="Your team vs median random valid team" />
      <HBar data={data} height={200} valueFmt={(v) => `${v.toFixed(1)} pts`} />
    </Card>
  );
}

export function FantasyPriceVsExp({ pool, picks, optimal }: { pool: any[]; picks: string[]; optimal: string[] }) {
  const data = pool.map((d) => ({
    name: d.name ?? d.code,
    x: d.price,
    y: d.exp_points,
    team: d.team,
    color: picks.includes(d.code) ? "#e10600" : optimal.includes(d.code) ? "#22c55e" : (d.team?.color ?? "#64748b"),
  }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Price vs Expected Points" sub="Red = your picks · green = optimal picks" />
      <ScatterXY data={data} height={300} xLabel="Price (M)" yLabel="Expected Points" />
    </Card>
  );
}

export function FantasyConcentration({ concentration }: { concentration: any[] }) {
  const data = (concentration ?? []).map((c) => ({ name: c.team, value: c.share, color: "#8d99b5" })).filter((d) => d.value > 0);
  if (!data.length) return emptyCard("Team Concentration", "Risk if one team dominates your picks", <Timer size={13} />);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Team Concentration" sub="Share of picks by constructor" />
      <DonutChart data={data} height={240} />
    </Card>
  );
}

export function FantasyTeamTotalDist({ teamStats, yourMean, optimalMean, randomMedian }: { teamStats: any; yourMean: number; optimalMean: number; randomMedian: number }) {
  if (!teamStats?.hist?.bins?.length) return emptyCard("Team Total Distribution", "Histogram of simulated team totals", <Timer size={13} />);
  const data = teamStats.hist.bins.map((bin: number, i: number) => ({ bin: String(bin), count: teamStats.hist.probs[i] ?? 0 }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Your Team Total-Points Distribution" sub={`Your ${yourMean.toFixed(1)} · optimal ${optimalMean.toFixed(1)} · random median ${randomMedian.toFixed(1)}`} />
      <Histogram data={data} height={260} />
    </Card>
  );
}

export function FantasyPickRiskRadar({ pool, picks }: { pool: any[]; picks: string[] }) {
  const chosen = pool.filter((d) => picks.includes(d.code));
  if (!chosen.length) return emptyCard("Pick Risk Radar", "Select drivers to compare risk/return", <Timer size={13} />);
  const axes = [
    { key: "pace", label: "Win" }, { key: "skill", label: "Podium" }, { key: "wet", label: "Points" }, { key: "rel", label: "Reliability" }, { key: "form", label: "ExpPts" },
  ];
  const data = chosen.map((d) => ({ name: d.code, pace: (d.win ?? 0) * 100, skill: (d.podium ?? 0) * 100, wet: (d.points_prob ?? 0) * 100, rel: (1 - (d.dnf ?? 0)) * 100, form: Math.min(100, (d.exp_points ?? 0) * 4) }));
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Pick Risk Radar" sub="Win, podium, points, reliability, expected-points (scaled)" />
      <RadarChart data={data as any} axes={axes} height={260} />
    </Card>
  );
}

export function FantasySwapWaterfall({ swaps }: { swaps: any[] }) {
  const data = (swaps ?? []).map((s: any) => ({ name: `${s.out}→${s.inn}`, value: s.delta_points, color: s.delta_points > 0 ? "#22c55e" : "#ef4444" })).sort((a: any, b: any) => b.value - a.value);
  if (!data.length) return emptyCard("Swap-Gain Waterfall", "Best feasible swap per slot", <Timer size={13} />);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Swap-Gain Waterfall" sub="Expected points delta for best feasible swap per slot" />
      <HBar data={data} height={260} valueFmt={(v) => `${v > 0 ? "+" : ""}${v.toFixed(1)} pts`} />
    </Card>
  );
}

export function FantasyValueRanking({ pool, picks }: { pool: any[]; picks: string[] }) {
  const data = (pool ?? []).map((d: any) => ({ name: d.name ?? d.code, value: d.exp_points / Math.max(d.price, 0.1), team: d.team, color: picks.includes(d.code) ? "#e10600" : d.team?.color })).sort((a: any, b: any) => b.value - a.value);
  if (!data.length) return emptyCard("Value per $M Ranking", "Expected points per million spent", <Timer size={13} />);
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Value per $M Ranking" sub="Red = your picks" />
      <HBar data={data} height={320} valueFmt={(v) => v.toFixed(2)} />
    </Card>
  );
}

export function FantasyPercentileDial({ verdict, percentile }: { verdict: any; percentile: number | null }) {
  return (
    <Card className="p-4">
      <CardTitle icon={<Timer size={13} />} title="Percentile vs Random Teams" sub="Rank vs random valid teams" />
      <Gauge value={percentile ?? null} min={0} max={100} label={verdict ? `Grade ${verdict.grade} — ${verdict.label}` : undefined} height={180} />
      {Array.isArray(verdict?.reasons) && verdict.reasons.length > 0 && (
        <div className="mt-2 space-y-1 text-[11px] text-slate-300">{verdict.reasons.map((r: string, i: number) => <div key={i}>• {r}</div>)}</div>
      )}
    </Card>
  );
}
