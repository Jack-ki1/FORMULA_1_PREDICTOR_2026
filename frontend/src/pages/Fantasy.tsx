import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { ShieldCheck, Trash2, Sparkles } from "lucide-react";
import { Avatar, Card, CardTitle, ErrorNote, Skeleton, TeamLogo, cx } from "../components/ui";
import { useFantasyEvaluate, useRaces } from "../lib/hooks";
import { HBar, VBar, ScatterXY, DonutChart, Histogram, RadarChart } from "../charts";

export default function Fantasy() {
  const [sp, setSp] = useSearchParams();
  const { data: races } = useRaces();
  const nextId = races?.find((r) => r.status !== "completed")?.id || races?.[races.length - 1]?.id || "";
  const race = sp.get("race_id") || nextId;
  const budget = Math.max(40, Math.min(200, Number(sp.get("budget") ?? "100") || 100));
  const picks = (sp.get("picks") ?? "").split(",").map((x) => x.trim().toUpperCase()).filter(Boolean).slice(0, 5);
  useEffect(() => {
    if (!sp.get("race_id") && nextId) setSp({ race_id: nextId, budget: String(budget), picks: picks.join(",") }, { replace: true });
  }, [nextId]);
  const q = useFantasyEvaluate(race || null, budget, picks);
  const f = q.data;
  const setPicks = (codes: string[]) => setSp({ race_id: race, budget: String(budget), picks: codes.join(",") });
  const toggle = (code: string) => {
    if (picks.includes(code)) return setPicks(picks.filter((c) => c !== code));
    if (picks.length < 5) setPicks([...picks, code]);
  };
  const pool = f?.pool ?? [];
  const pickedRows = pool.filter((d: any) => picks.includes(d.code));

  return (
    <div className="space-y-3 p-3.5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><h1 className="text-[20px] font-extrabold">Fantasy League</h1><p className="text-[11px] text-mute">Pick 5 drivers, evaluate your team, and see what to change next.</p></div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-[11px]"><span className="mb-1 block text-mute">Race</span>
            <select className="field py-1 text-[11px]" value={race} onChange={(e) => setSp({ race_id: e.target.value, budget: String(budget), picks: picks.join(",") })}>
              {(races ?? []).map((r) => <option key={r.id} value={r.id}>R{r.round} — {r.name}</option>)}
              {!races?.some((r) => r.id === race) && race && <option value={race}>Race {race}</option>}
            </select></label>
          <label className="text-[11px]"><span className="mb-1 block text-mute">Budget ($M)</span>
            <input className="field w-20 py-1 text-[11px]" type="number" min={40} max={200} value={budget} onChange={(e) => setSp({ race_id: race, budget: e.target.value, picks: picks.join(",") })} /></label>
        </div>
      </div>

      {q.isError && <ErrorNote error={q.error} retry={() => q.refetch()} />}
      {q.isFetching && !f && <Skeleton className="h-40" />}

      {f && (
        <div className={cx("card p-3 text-[11px]", f.valid ? "border-emerald-500/40 bg-emerald-500/5" : "border-amber-500/40 bg-amber-500/5")}>
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex items-center gap-1.5 font-semibold">{f.valid ? <><ShieldCheck size={13} className="text-emerald-300" />Valid team</> : <>Pick exactly 5 drivers within budget</>}</span>
            <span className="text-mute">Spent {f.spent.toFixed(1)}M · Remaining {f.remaining.toFixed(1)}M · Picks {picks.length}/5</span>
            {f.issues?.map((i: string, idx: number) => <span key={idx} className="text-amber-200">⚠ {i}</span>)}
          </div>
        </div>
      )}

      {f && (
        <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
          <Card className="p-4"><CardTitle icon={<Sparkles size={13} />} title="1. Your Picks vs Team Needs" sub="Current 5 picks with expected points and budget impact" />
            <div className="space-y-1.5">{pickedRows.length ? pickedRows.map((d: any) => (
              <div key={d.code} className="flex items-center justify-between rounded-lg border border-edge bg-black/20 px-2.5 py-2">
                <div className="flex min-w-0 items-center gap-2"><Avatar code={d.code} team={d.team} size={28} /><div className="min-w-0"><div className="truncate text-[12px] font-semibold">{d.name}</div><div className="truncate text-[10px] text-mute">{d.team?.name} · ${Number(d.price).toFixed(1)}M</div></div></div>
                <div className="flex items-center gap-2"><span className="text-[11px] tabular-nums">{Number(d.exp_points).toFixed(1)} pts</span><button aria-label={`Remove ${d.name}`} onClick={() => setPicks(picks.filter((c) => c !== d.code))} className="text-mute hover:text-white"><Trash2 size={13} /></button></div>
              </div>
            )) : <div className="rounded-lg border border-dashed border-edge p-4 text-[11px] text-mute">No picks yet — choose drivers from the pool below.</div>}</div>
            {f.optimal?.picks?.length ? <div className="mt-3 rounded-lg border border-edge bg-white/[0.02] p-2.5 text-[10px] text-mute"><b className="text-slate-200">Optimal model team:</b> {f.optimal.picks.join(", ")} · {Number(f.optimal.exp_points).toFixed(1)} pts · ${Number(f.optimal.price).toFixed(1)}M</div> : null}
          </Card>

          <Card className="p-4"><CardTitle icon={<Sparkles size={13} />} title="2. Expected Points by Pick" sub="Which of your picks are carrying the team" />
            <VBar data={pickedRows.map((d: any) => ({ name: d.code, value: d.exp_points, team: d.team, color: d.team?.color }))} height={260} valueFmt={(v) => `${v.toFixed(1)} pts`} />
          </Card>

          <Card className="p-4"><CardTitle icon={<Sparkles size={13} />} title="3. Price vs Expected Points" sub="Red = your picks, green = optimal, team colors = pool" />
            <ScatterXY data={pool.map((d: any) => ({ name: d.name ?? d.code, x: d.price, y: d.exp_points, team: d.team, color: picks.includes(d.code) ? "#e10600" : d.optimal ? "#22c55e" : d.team?.color }))} height={260} xLabel="Price ($M)" yLabel="Expected Points" />
          </Card>

          <Card className="p-4"><CardTitle icon={<Sparkles size={13} />} title="4. Budget & Team Balance" sub="Spent, remaining, and constructor concentration" />
            <DonutChart data={[
              { name: "Spent", value: f.spent, color: "#e10600", desc: "Budget already allocated to your 5 picks." },
              { name: "Remaining", value: Math.max(0, f.remaining), color: "#334155", desc: "Unused budget that could be upgraded into picks." },
            ]} showLegend height={240} valueFmt={(v) => `$${v.toFixed(1)}M`} />
            <div className="mt-2"><HBar data={(f.concentration ?? []).map((c: any) => ({ name: c.team, value: c.picks, color: "#7c4dff" }))} height={120} valueFmt={(v) => `${v.toFixed(0)} picks`} /></div>
          </Card>

          <Card className="p-4"><CardTitle icon={<Sparkles size={13} />} title="5. What to Change Next" sub="Best feasible swaps and value upgrades" />
            {f.swaps?.length ? <HBar data={f.swaps.map((s: any) => ({ name: `${s.out}→${s.inn}`, value: s.delta_points, color: s.delta_points >= 0 ? "#22c55e" : "#ef4444" }))} height={180} valueFmt={(v) => `${v >= 0 ? "+" : ""}${v.toFixed(1)} pts`} /> : <div className="rounded-lg border border-dashed border-edge p-4 text-[11px] text-mute">No feasible swaps yet — add 5 picks first.</div>}
            <div className="mt-3 text-[11px] text-slate-300">Verdict: <b>{f.verdict?.grade ?? "—"}</b> {f.verdict?.label ? `— ${f.verdict.label}` : ""} {f.team?.percentile_vs_random != null ? `· ${Number(f.team.percentile_vs_random).toFixed(0)}th percentile vs random teams` : ""}</div>
            <div className="mt-1 space-y-1 text-[10px] text-mute">{(f.verdict?.reasons ?? []).map((r: string, i: number) => <div key={i}>• {r}</div>)}</div>
          </Card>

          <Card className="p-4"><CardTitle icon={<Sparkles size={13} />} title="Progress / Team Total" sub="Simulated team points distribution and target" />
            {f.team?.hist?.bins?.length ? <Histogram data={f.team.hist.bins.map((bin: number, i: number) => ({ bin: String(bin), count: f.team.hist.probs[i] ?? 0 }))} height={220} /> : <div className="rounded-lg border border-dashed border-edge p-4 text-[11px] text-mute">Pick 5 drivers to simulate your team total.</div>}
            <div className="mt-2 grid grid-cols-3 gap-2 text-[10px]"><div className="rounded bg-white/[0.03] p-2"><div className="text-mute">Your mean</div><b>{Number(f.team?.exp_points ?? 0).toFixed(1)}</b></div><div className="rounded bg-white/[0.03] p-2"><div className="text-mute">Optimal</div><b>{Number(f.optimal?.exp_points ?? 0).toFixed(1)}</b></div><div className="rounded bg-white/[0.03] p-2"><div className="text-mute">Gap</div><b>{Number(f.team?.gap_to_optimal ?? 0).toFixed(1)}</b></div></div>
          </Card>
        </div>
      )}

      {f && (
        <Card className="p-4">
          <div className="mb-2 flex items-center justify-between"><div className="label !text-[11px] !text-slate-200">Driver Pool</div><span className="text-[10px] text-mute">Click to add/remove · 5 max</span></div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {pool.map((d: any) => {
              const selected = picks.includes(d.code);
              return (
                <button key={d.code} onClick={() => toggle(d.code)} disabled={!selected && picks.length >= 5} className={cx("rounded-lg border p-2.5 text-left transition", selected ? "border-glow bg-f1red/10" : "border-edge bg-black/20 hover:bg-white/[0.03]", !selected && picks.length >= 5 && "cursor-not-allowed opacity-50")}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <Avatar code={d.code} team={d.team} size={30} />
                      <div className="min-w-0">
                        <div className="truncate text-[12px] font-semibold">{d.name}</div>
                        <div className="flex items-center gap-1 truncate text-[10px] text-mute"><TeamLogo team={d.team} size={10} />{d.team?.name} · {d.code}</div>
                      </div>
                    </div>
                    {selected && <ShieldCheck size={13} className="shrink-0 text-emerald-300" />}
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-1 text-[10px]">
                    <div className="rounded bg-white/[0.03] px-1.5 py-1"><div className="text-mute">Price</div><b>${Number(d.price).toFixed(1)}M</b></div>
                    <div className="rounded bg-white/[0.03] px-1.5 py-1"><div className="text-mute">Exp pts</div><b>{Number(d.exp_points).toFixed(1)}</b></div>
                    <div className="rounded bg-white/[0.03] px-1.5 py-1"><div className="text-mute">Top-10</div><b>{Number(d.points_prob ?? 0).toFixed(0)}%</b></div>
                  </div>
                </button>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}
