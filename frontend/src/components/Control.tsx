import { ArrowLeftRight, Check, ChevronDown, Cloud, CloudRain, CloudSun, Cpu, Eraser, Flag as FlagIcon, Loader2, Radio, Rocket, Sparkles, Sun, Timer, Trophy, Wand2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Prediction, Race, SessionKind } from "../lib/api";
import { useDrivers, useGridOptions, useRaces, useMeta } from "../lib/hooks";
import { useApp } from "../lib/store";
import { overtakingLabel, pad, sessionState, short } from "../lib/util";
import { Card, Flag, Skeleton, Toggle, cx, pct } from "./ui";
import { Strategy } from "./Panels";

export function useNow(ms = 1000) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), ms); return () => clearInterval(t); }, [ms]);
  return now;
}

const BADGE = { completed: "Done", live: "Live", upcoming: "" } as const;

export function RaceSelect({ races, value, onChange, nextId }: { races: Race[]; value: string; onChange: (id: string) => void; nextId?: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const sel = races.find((r) => r.id === value);
  useEffect(() => {
    const c = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    const k = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", c); document.addEventListener("keydown", k);
    return () => { document.removeEventListener("mousedown", c); document.removeEventListener("keydown", k); };
  }, []);
  return (
    <div ref={ref} className="relative">
      <button type="button" aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen(!open)} className="field flex items-center gap-3 !py-2.5 text-left text-[13px]">
        {sel ? <><Flag cc={sel.cc} className="h-4 w-6" /><span className="font-semibold">Round {sel.round} · {sel.name}</span></> : <span className="text-mute">— Select Race —</span>}
        <ChevronDown size={14} className="ml-auto text-mute" />
      </button>
      {open && (
        <ul role="listbox" aria-label="Grand Prix" className="card absolute z-40 mt-1 max-h-80 w-full overflow-auto p-1 shadow-2xl">
          {races.map((r) => (
            <li key={r.id} role="option" aria-selected={r.id === value}>
              <button type="button" onClick={() => { onChange(r.id); setOpen(false); }} className={cx("flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-[12px] hover:bg-white/5", r.id === value && "bg-f1red/15")}>
                <Flag cc={r.cc} className="h-3.5 w-5" /><span className="flex-1">Round {r.round} · {r.name}</span>
                {r.id === nextId && r.status !== "completed" ? <span className="rounded-full bg-f1red/20 px-2 py-0.5 text-[9px] font-bold text-glow">NEXT</span>
                  : BADGE[r.status] && <span className={cx("rounded-full px-2 py-0.5 text-[9px] font-bold", r.status === "live" ? "bg-emerald-500/20 text-emerald-300" : "bg-white/10 text-mute")}>{BADGE[r.status].toUpperCase()}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const WEATHER = [{ v: "auto", label: "Auto", icon: <Sparkles size={13} /> }, { v: "dry", label: "Dry", icon: <Sun size={13} /> }, { v: "mixed", label: "Mixed", icon: <CloudSun size={13} /> }, { v: "wet", label: "Wet", icon: <CloudRain size={13} /> }] as const;

function Tile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return <div className="rounded-lg border border-edge bg-black/20 px-3 py-2"><div className="label !text-[9px]">{label}</div><div className="mt-0.5 text-[18px] font-bold tabular-nums leading-tight">{value}</div>{sub && <div className="text-[9px] text-mute">{sub}</div>}</div>;
}

export function WeekendStatus({ race }: { race?: Race }) {
  const now = useNow();
  const st = useMemo(() => sessionState(race, now), [race, now]);
  const d = new Date(now);
  const left = st?.next ? Math.max(0, Math.floor((st.next.t - now) / 1000)) : 0;
  const fmt = (t: number) => new Date(t).toLocaleString(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit" });
  return (
    <div className="rounded-xl border border-edge bg-black/20 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="flex items-center gap-2 text-[12px] font-bold"><FlagIcon size={13} className="text-glow" />Race weekend status</span>
        <span className={cx("flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[9px] font-bold tracking-wider", st?.live ? "border-emerald-500/50 text-emerald-300" : "border-edge text-mute")}>
          <span className={cx("h-1.5 w-1.5 rounded-full", st?.live ? "animate-pulse bg-emerald-400" : "bg-mute")} />LIVE TIMING
        </span>
      </div>
      {!race || !st ? <Skeleton className="h-16" /> : (
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            {st.live ? (<><div className="label !text-emerald-300">Live now</div><div className="mt-1 text-[13px] font-semibold">{race.name} — {st.live.name} <span className="text-mute">• Session in progress</span></div></>)
              : st.next ? (<><div className="label">Next session in</div>
                <div className="mt-1 flex items-baseline gap-2 tabular-nums"><b className="text-[26px] leading-none">{Math.floor(left / 86400) > 0 ? `${Math.floor(left / 86400)}d ` : ""}{pad(Math.floor((left % 86400) / 3600))}:{pad(Math.floor((left % 3600) / 60))}:{pad(left % 60)}</b></div>
                <div className="mt-1 text-[11px] text-slate-300">{race.name} — {st.next.name} · {fmt(st.next.t)}{st.next.estimated ? " (est.)" : ""}</div></>)
                : (<><div className="label">Weekend complete</div><div className="mt-1 text-[13px] font-semibold">{race.name} has finished{race.winner ? ` · winner ${race.winner}` : ""}</div></>)}
          </div>
          <div className="text-right"><div className="label !text-[9px]">UTC now</div><div className="text-[15px] font-bold tabular-nums">{pad(d.getUTCHours())}:{pad(d.getUTCMinutes())}:{pad(d.getUTCSeconds())} UTC</div>
            <div className="text-[10px] text-mute">{d.toLocaleDateString("en-GB", { weekday: "short", day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" })}</div></div>
        </div>
      )}
      {st && (
        <ol className="mt-3 flex flex-wrap gap-1.5 text-[10px]" aria-label="Session schedule">
          {st.list.map((s) => {
            const state = now >= s.end ? "done" : now >= s.t ? "live" : s === st.next ? "next" : "later";
            return <li key={s.key} className={cx("rounded-md border px-2 py-1", state === "live" && "border-emerald-500/60 bg-emerald-500/10 text-emerald-300", state === "next" && "border-glow/60 bg-f1red/10", state === "done" && "border-edge opacity-50", state === "later" && "border-edge")}>
              <b>{s.key === "R" ? "Race" : s.key}</b> <span className="text-mute">{fmt(s.t)}</span></li>;
          })}
        </ol>
      )}
    </div>
  );
}

const SESSION_CARDS = (r?: Race) => {
  const L = r?.labels;
  const base = [
    { k: "practice" as SessionKind, icon: <Timer size={18} />, title: `${L?.practice_day ?? "Friday"} Practice`, sub: "FP1 · FP2 · FP3 — projected pace distribution" },
    { k: "qualifying" as SessionKind, icon: <Rocket size={18} />, title: `${L?.quali_day ?? "Saturday"} Qualifying`, sub: "Q1/Q2/Q3 elimination · Q3 advancement model" },
    { k: "race" as SessionKind, icon: <Trophy size={18} />, title: `${L?.race_day ?? "Sunday"} Grand Prix`, sub: "Full race prediction — podium, points, DNF risk" },
  ];
  if (r?.sprint) base.splice(1, 0, { k: "sprint", icon: <Radio size={18} />, title: `${L?.quali_day ?? "Saturday"} Sprint`, sub: "Short race · top-8 points · sprint grid" });
  return base;
};

export function GridEditor({ race }: { race?: Race }) {
  const { draft, setDraft } = useApp();
  const { data: drivers } = useDrivers();
  const { data: opts } = useGridOptions(race?.id);
  const n = drivers?.length ?? 22;
  const slots = Array.from({ length: n }, (_, i) => draft.grid[i] ?? "");
  const used = new Set(slots.filter(Boolean));
  const byCode = Object.fromEntries((drivers ?? []).map((d) => [d.code, d]));
  const sorted = [...(drivers ?? [])].sort((a, b) => a.code.localeCompare(b.code));
  const set = (grid: string[]) => setDraft({ grid, grid_mode: "manual" });
  const filled = slots.filter(Boolean).length;
  return (
    <div className="rounded-xl border border-edge bg-black/20 p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div><div className="flex items-center gap-2 text-[13px] font-bold"><span className="rounded bg-f1red/20 px-1.5 py-0.5 text-[10px] text-glow">P1-P{n}</span>Starting Grid</div>
          <p className="mt-0.5 max-w-xl text-[10px] text-mute">Choose how the grid is set. Auto-fetched uses live qualifying results when published; Manual lets you set each P slot. Empty slots are filled by simulated qualifying.</p></div>
        <div className="inline-flex rounded-full border border-edge bg-black/30 p-0.5 text-[11px]" role="group" aria-label="Grid mode">
          {(["auto", "manual"] as const).map((m) => <button key={m} onClick={() => setDraft({ grid_mode: m })} aria-pressed={draft.grid_mode === m} className={cx("rounded-full px-3 py-1 font-medium", draft.grid_mode === m ? "bg-f1red text-white on-accent" : "text-mute hover:text-white")}>{m === "auto" ? "Auto-fetched Grid" : "Manual Grid"}</button>)}
        </div>
      </div>
      {draft.grid_mode === "auto" ? (
        <div className="rounded-lg border border-dashed border-edge p-3 text-[11px] text-slate-300">
          {opts?.live ? (<><b className="text-emerald-300">Live qualifying grid fetched.</b><div className="mt-2 flex flex-wrap gap-1.5">{opts.live.map((c, i) => <span key={c} className="rounded border border-edge px-1.5 py-0.5 text-[10px]"><b className="text-mute">P{i + 1}</b> {c}</span>)}</div></>)
            : <span>No published qualifying result for this event yet — the engine simulates Q1/Q2/Q3 and sets the grid for you. Switch to <b>Manual Grid</b> to pin any starting positions.</span>}
        </div>
      ) : (<>
        <div className="mb-3 flex flex-wrap gap-2 text-[11px]">
          <button className="btn-ghost" onClick={() => set([])}><Eraser size={13} />Clear All P Slots</button>
          <button className="btn-ghost" disabled={!opts} onClick={() => opts && set(opts.live ?? opts.by_form)}><Wand2 size={13} />Auto-fill P1→P{n} (by {opts?.live ? "Qualifying" : "Form"})</button>
          <button className="btn-ghost" onClick={() => set([...slots].reverse())}><ArrowLeftRight size={13} />Reverse P1↔P{n}</button>
          <span className="self-center text-[10px] text-mute">Each P is one grid position. Picks are unique — the same driver cannot be in two slots.</span>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          {slots.map((c, i) => (
            <label key={i} className={cx("rounded-lg border bg-black/20 p-1.5 text-[10px]", c ? "border-glow/50" : "border-edge")}>
              <span className="mb-1 flex items-center justify-between font-bold"><span>P{i + 1}</span>{c && <span className="h-2 w-2 rounded-full" style={{ background: "currentColor" }} aria-hidden />}</span>
              <select aria-label={`Grid position P${i + 1}`} className="field !px-2 !py-1.5 text-[11px]" value={c} onChange={(e) => { const g = [...slots]; g[i] = e.target.value; set(g); }}>
                <option value="">— select —</option>
                {sorted.filter((d) => !used.has(d.code) || d.code === c).map((d) => <option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}
              </select>
            </label>
          ))}
        </div>
        <p className="mt-2 text-[11px] text-mute">{filled ? <><Check size={11} className="mr-1 inline text-emerald-300" />{filled} slot{filled > 1 ? "s" : ""} pinned{filled < n ? ` · ${n - filled} filled by simulated qualifying` : ""}{filled ? ` (${slots.map((c, i) => c && `P${i + 1} ${byCode[c]?.code}`).filter(Boolean).slice(0, 4).join(", ")}${filled > 4 ? "…" : ""})` : ""}</> : "— empty (auto grid will be used)"}</p>
      </>)}
    </div>
  );
}

export function ControlCenter({ p, loading }: { p?: Prediction; loading?: boolean }) {
  const { draft, applied, setDraft, run, s } = useApp();
  const { data: races } = useRaces();
  const { data: meta } = useMeta();
  const maxSims = meta?.max_sims ?? 20000;
  const nextId = races?.find((r) => r.status !== "completed")?.id ?? races?.[races.length - 1]?.id;
  const selId = draft.race_id ?? nextId ?? "";
  const race = races?.find((r) => r.id === selId);
  const showGrid = s.showGrid && (draft.session === "race" || draft.session === "sprint");
  const dirty = JSON.stringify(draft) !== JSON.stringify(applied);
  useEffect(() => {
    if (!race) return;
    if (!race.sprint && (draft.session === "sprint" || draft.session === "sprint_qualifying")) setDraft({ session: "race", sub: "" });
    if (race.sprint && draft.session === "practice" && draft.sub !== "FP1") setDraft({ sub: "FP1" });
    if (!race.sprint && draft.session === "practice" && !draft.sub) setDraft({ sub: "FP2" });
  }, [race?.id, race?.sprint]);
  const pick = (patch: Partial<typeof draft>) => {
    const next = { ...draft, ...patch };
    if (race && !race.sprint && (next.session === "sprint" || next.session === "sprint_qualifying")) next.session = "race";
    if (next.session !== "practice") next.sub = "";
    if (next.session === "practice" && !next.sub) next.sub = race?.sprint ? "FP1" : "FP2";
    setDraft(next);
  };
  const doRun = () => {
    const next = { ...draft };
    if (race && !race.sprint && (next.session === "sprint" || next.session === "sprint_qualifying")) next.session = "race";
    if (next.session !== "practice") next.sub = "";
    if (next.session === "practice" && !next.sub) next.sub = race?.sprint ? "FP1" : "FP2";
    run(next);
  };
  return (
    <Card className="space-y-4 p-4 md:p-5">
      <div className="grid gap-4 lg:grid-cols-[1.05fr_1fr]">
        <div className="space-y-3">
          <div><div className="label !text-glow">2026 Formula 1 World Championship</div>
            <div className="mt-1 flex flex-wrap items-center gap-3"><h2 className="text-[22px] font-extrabold leading-tight">Select a Grand Prix</h2>
              <span className="rounded-full border border-edge px-2.5 py-0.5 text-[10px] font-semibold text-slate-300">Race Day ({race?.labels.race_day ?? "Sunday"})</span></div>
            <p className="mt-1 text-[11px] text-mute">Choose a race below to start the prediction engine</p></div>
          {races ? <RaceSelect races={races} value={selId} nextId={nextId} onChange={(id) => pick({ race_id: id, grid: [], grid_mode: "auto" })} /> : <Skeleton className="h-11" />}
          <div className="flex flex-wrap gap-2" role="group" aria-label="Weather">
            {WEATHER.map((w) => <button key={w.v} aria-pressed={draft.weather === w.v} onClick={() => pick({ weather: w.v })} className={cx("flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-[12px] font-medium transition", draft.weather === w.v ? "border-glow bg-f1red/20 text-white on-accent" : "border-edge text-slate-300 hover:border-glow/50")}>{w.icon}{w.label}</button>)}
            {p && draft.weather === "auto" && <span className="flex items-center gap-1 self-center text-[10px] text-mute"><Cloud size={11} />using {p.weather_used}{p.rain_prob == null ? " (no forecast yet)" : ""}</span>}
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Tile label="Safety car %" value={p ? `${Math.round(p.safety_car_prob * 100)}%` : "—"} />
            <Tile label="Rain %" value={p?.rain_prob != null ? `${Math.round(p.rain_prob)}%` : "—"} sub={p && p.rain_prob == null ? "no forecast yet" : undefined} />
            <Tile label="Simulations" value={short(draft.sims)} />
            <Tile label="Confidence" value={p ? `${Math.round(p.confidence * 100)}%` : "—"} />
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-edge bg-black/20 px-3 py-2 text-[11px]"><Cpu size={14} className="text-glow" /><b>Monte Carlo {p?.params.enhanced ?? draft.enhanced ? "+ season form" : "(base ratings)"}</b>
            <span className="ml-auto text-mute">{p ? `${p.params.sims.toLocaleString()} sims · ${p.elapsed_ms} ms` : "…"}</span></div>
        </div>
        <div className="space-y-3">
          <WeekendStatus race={race} />
          <div className="rounded-xl border border-edge bg-black/20 p-3">
            <div className="label">Selected event</div>
            {race ? (<><div className="mt-1 flex items-center gap-2 text-[15px] font-bold"><Flag cc={race.cc} className="h-4 w-6" />{race.name}</div>
              <div className="text-[11px] text-mute">{race.circuit.name} · {race.circuit.locality}</div>
              <div className="mt-2 grid grid-cols-3 gap-2"><Tile label="Laps" value={String(race.circuit.laps ?? "—")} /><Tile label="DRS zones" value={String(race.circuit.drs ?? "—")} /><Tile label="Overtaking" value={overtakingLabel(race.circuit.overtaking)} /></div></>)
              : <p className="mt-1 text-[12px] text-mute">No Grand Prix selected</p>}
          </div>
        </div>
      </div>

      <div><div className="mb-2 text-[12px] font-bold">Select race weekend session</div>
        <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {SESSION_CARDS(race).map((c) => (
            <button key={c.k} aria-pressed={draft.session === c.k} onClick={() => pick({ session: c.k, sub: (c.k === "practice" ? "FP2" : "") as "" | "FP1" | "FP2" | "FP3" })} className={cx("flex flex-col items-start gap-2 rounded-xl border p-3 text-left transition", draft.session === c.k ? "border-glow bg-f1red/10 shadow-lg" : "border-edge bg-black/20 hover:border-glow/50")}>
              <span className={cx("grid h-9 w-9 shrink-0 place-items-center rounded-lg", draft.session === c.k ? "bg-gradient-to-br from-f1red to-glow text-white on-accent" : "bg-white/5 text-glow")}>{c.icon}</span>
              <div>
                <span className="block text-[13px] font-bold">{c.title}</span>
                <span className="block text-[10px] leading-snug text-mute">{c.sub}</span>
              </div>
              {c.k === "practice" && (
                <div className="mt-2 flex gap-1" role="group" aria-label="Practice session">
                  {(["FP1", "FP2", "FP3"] as const).map((sub) => {
                    const enabled = (race?.sessions ?? []).some((s) => s.key === sub);
                    const active = draft.sub === sub;
                    return (<button key={sub} disabled={!enabled} onClick={(e) => { e.stopPropagation(); pick({ session: "practice", sub }); }} aria-pressed={active} title={!enabled ? "No FP2/FP3 on sprint weekends" : undefined} className={cx("px-2 py-1 rounded-md text-[10px]", active ? "bg-f1red text-white" : !enabled ? "border-edge text-slate-500 opacity-50" : "border border-white/10 text-slate-300 hover:border-white/40")}>{sub}</button>);
                  })}
                </div>
              )}
              {c.k === "qualifying" && (
                <div className="mt-2 flex gap-1" role="group" aria-label="Qualifying view">
                  {["Q1", "Q2", "Q3", "Full"].map((view) => {
                    const active = draft.qualiView === view;
                    return (<button key={view} onClick={(e) => { e.stopPropagation(); setDraft({ qualiView: view as "Q1" | "Q2" | "Q3" | "Full" }); }} aria-pressed={active} className={cx("px-2 py-1 rounded-md text-[10px]", active ? "bg-f1red text-white" : "border border-white/10 text-slate-300 hover:border-white/40")}>{view}</button>);
                  })}
                </div>
              )}
              {c.k === "sprint" && (
                <div className="mt-2 flex gap-1" role="group" aria-label="Sprint session">
                  <span className="px-2 py-1 rounded-md border border-white/10 text-[10px] text-slate-300">Sprint Race</span>
                </div>
              )}
            </button>))}
        </div></div>

      {(draft.session === "race" || draft.session === "sprint") && <Strategy p={p} loading={loading} />}

      {showGrid && <GridEditor race={race} />}
      {!showGrid && s.showGrid && <p className="rounded-lg border border-dashed border-edge p-2.5 text-[11px] text-mute">The starting grid applies to Race and Sprint sessions. {draft.session === "qualifying" ? "Qualifying is simulated as Q1 → Q2 → Q3 elimination." : "Practice shows each driver's projected pace spread."}</p>}

      <div className="flex flex-wrap items-end gap-3">
        <label className="text-[11px] flex items-center gap-2"><span className="mb-1 block text-mute">Simulations</span>
          <input type="range" min="1000" max={maxSims} step="500" className="w-40" value={draft.sims} onChange={(e) => setDraft({ sims: Math.min(maxSims, Math.max(1000, Number(e.target.value) || 1000)) })} />
          <span className="font-mono text-[10px] tabular-nums">{draft.sims.toLocaleString()}</span></label>
        <button className="btn-red !px-6 !py-2.5 !text-[13px]" disabled={loading || !race} onClick={doRun}>{loading ? <Loader2 size={14} className="animate-spin" /> : <Rocket size={14} />}{loading ? "Simulating…" : "Run Prediction"}</button>
        {dirty && !loading && <span className="text-[11px] text-amber-300">Unapplied changes — press Run Prediction</span>}
        {p && !dirty && <span className="text-[11px] text-mute">Grid: {p.grid_source === "manual" ? `manual (${p.grid_locked} pinned)` : p.grid_source === "live" ? "live qualifying" : "simulated qualifying"} · P(top-3) leader {pct(Math.max(...p.drivers.map((d) => d.podium)), 0)}</span>}
      </div>
    </Card>
  );
}
