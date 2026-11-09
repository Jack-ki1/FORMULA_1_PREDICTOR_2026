import { useQueryClient } from "@tanstack/react-query";
import { Accessibility, Bell, Cpu, Database, Keyboard, LayoutDashboard, Palette, Server, Shield, SlidersHorizontal, User, Wrench } from "lucide-react";
import { type ReactNode, useEffect, useRef, useState } from "react";
import { api, type SimParams } from "../lib/api";
import { useDrivers, useServerConfig, useMeta } from "../lib/hooks";
import { DEFAULT_SETTINGS, DEFAULT_SIM, type Settings, useApp } from "../lib/store";
import { download } from "../lib/util";
import { SHORTCUTS } from "../components/Shortcuts";
import { Segmented, Toggle, cx } from "../components/ui";

type Tone = "live" | "admin" | "fixed";
const TAG: Record<Tone, [string, string]> = { live: ["LIVE", "bg-emerald-500/15 text-emerald-300"], admin: ["NEEDS ADMIN ACCESS", "bg-sky-500/15 text-sky-300"], fixed: ["FIXED", "bg-white/10 text-mute"] };
const Tag = ({ t }: { t: Tone }) => <span className={cx("ml-2 rounded px-1.5 py-0.5 align-middle text-[9px] font-bold tracking-wide", TAG[t][1])}>{TAG[t][0]}</span>;

const SECTIONS = [
  ["appearance", "Appearance", Palette], ["accessibility", "Accessibility", Accessibility], ["engine", "Prediction Engine", Cpu], ["backend", "Backend Config", Server],
  ["reference", "Reference Params", SlidersHorizontal], ["layout", "Dashboard Layout", LayoutDashboard], ["notifications", "Notifications", Bell], ["profile", "Profile", User],
  ["advanced", "Advanced", Wrench], ["shortcuts", "Keyboard Shortcuts", Keyboard], ["data", "Data & Privacy", Database],
] as const;

function Section({ id, title, desc, icon: Icon, children }: { id: string; title: string; desc: string; icon: typeof Palette; children: ReactNode }) {
  return (
    <section id={id} data-section className="card scroll-mt-20 p-4 md:p-5">
      <div className="mb-3 flex gap-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-f1red/15 text-glow"><Icon size={16} /></span>
        <div><h2 className="text-[15px] font-bold">{title}</h2><p className="text-[11px] text-mute">{desc}</p></div></div>
      <div className="divide-y divide-edge">{children}</div>
    </section>
  );
}
function Row({ label, tag, desc, children, wide }: { label: string; tag?: Tone; desc?: string; children?: ReactNode; wide?: boolean }) {
  return (
    <div className={cx("flex flex-wrap items-center justify-between gap-x-6 gap-y-2 py-3", wide && "flex-col items-stretch")}>
      <div className="min-w-0 max-w-md"><div className="text-[12px] font-semibold">{label}{tag && <Tag t={tag} />}</div>{desc && <p className="mt-0.5 text-[10px] leading-snug text-mute">{desc}</p>}</div>
      {children && <div className={cx("flex items-center gap-2", wide ? "" : "w-full sm:w-[260px] sm:justify-end")}>{children}</div>}
    </div>
  );
}
function Slider({ value, min, max, step, onChange, fmt }: { value: number; min: number; max: number; step: number; onChange: (v: number) => void; fmt: (v: number) => string }) {
  return <><input type="range" aria-label="value" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full" /><b className="w-16 shrink-0 text-right text-[12px] tabular-nums text-glow">{fmt(value)}</b></>;
}

const encode = (s: Settings) => btoa(unescape(encodeURIComponent(JSON.stringify(s))));
const decode = (h: string): Partial<Settings> => JSON.parse(decodeURIComponent(escape(atob(h))));

export default function SettingsPage() {
  const { s, set, setSim, replaceSettings, resetAll } = useApp();
  const qc = useQueryClient();
  const { data: drivers } = useDrivers();
  const { data: cfg, refetch: refetchCfg } = useServerConfig();
  const { data: meta } = useMeta();
  const maxSims = meta?.max_sims ?? 20000;
  const [msg, setMsg] = useState("");
  const [active, setActive] = useState("appearance");
  const [token, setToken] = useState(sessionStorage.getItem("f1p26_admin") ?? "");
  const [srv, setSrv] = useState({ cache_ttl: "", live_interval: "", source_priority: "", model_type: "" });
  const file = useRef<HTMLInputElement>(null);
  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(""), 4000); };
  const sim = s.sim; const pctf = (v: number) => `${Math.round(v * 100)}%`;
  const S = (k: keyof SimParams) => (v: number) => setSim({ [k]: v } as Partial<SimParams>);

  useEffect(() => {
    if (location.hash.startsWith("#s=")) { try { replaceSettings(decode(location.hash.slice(3))); flash("Settings imported from the shared link."); } catch { flash("That settings link could not be read."); } history.replaceState(null, "", location.pathname); }
  }, [replaceSettings]);
  useEffect(() => { // scroll-spy for the left navigation
    if (typeof IntersectionObserver === "undefined") return;
    const els = [...document.querySelectorAll<HTMLElement>("[data-section]")];
    const io = new IntersectionObserver((es) => { const v = es.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]; if (v) setActive(v.target.id); }, { rootMargin: "-20% 0px -65% 0px" });
    els.forEach((e) => io.observe(e)); return () => io.disconnect();
  }, []);
  useEffect(() => { if (cfg) setSrv((x) => ({ cache_ttl: x.cache_ttl || String(cfg.cache_ttl), live_interval: x.live_interval || String(cfg.live_interval), source_priority: x.source_priority || cfg.source_priority, model_type: x.model_type || cfg.model_type })); }, [cfg]);

  const saveSrv = async (k: "cache_ttl" | "live_interval" | "source_priority" | "model_type") => {
    try { await api.adminSet({ [k]: k === "cache_ttl" || k === "live_interval" ? Number(srv[k]) : srv[k] } as never); await refetchCfg(); qc.invalidateQueries(); flash(`Saved ${k.replace("_", " ")} on the server.`); }
    catch (e) { flash((e as Error).message); }
  };
  const permission = typeof Notification === "undefined" ? "unsupported" : Notification.permission;
  const enableReminders = async (on: boolean) => {
    if (on && typeof Notification !== "undefined" && Notification.permission === "default") await Notification.requestPermission();
    set({ remind: on && typeof Notification !== "undefined" && Notification.permission === "granted" });
    if (on && (typeof Notification === "undefined" || Notification.permission !== "granted")) flash("Notifications are blocked or unsupported in this browser.");
  };
  const colorRow = (k: keyof Settings["colors"], label: string, fallback: string) => (
    <label className="flex items-center gap-2 text-[11px]"><input type="color" value={s.colors[k] ?? fallback} onChange={(e) => set({ colors: { ...s.colors, [k]: e.target.value } })} />{label}</label>
  );
  const teams = [...new Map((drivers ?? []).map((d) => [d.team.id, d.team])).values()];

  return (
    <div className="mx-auto flex max-w-6xl gap-5 p-3.5">
      <aside className="sticky top-20 hidden h-fit w-52 shrink-0 lg:block"><div className="card p-2"><nav aria-label="Settings sections">
        {SECTIONS.map(([id, label, Icon]) => <a key={id} href={`#${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: "smooth" }); }} className={cx("flex items-center gap-2 rounded-md px-3 py-2 text-[12px]", active === id ? "bg-f1red/15 font-semibold text-glow" : "text-slate-300 hover:bg-white/5")}><Icon size={13} />{label}</a>)}
      </nav></div></aside>

      <div className="min-w-0 flex-1 space-y-4">
        <div><h1 className="text-[22px] font-extrabold">Settings</h1><p className="text-[11px] text-mute">Every control here is either <Tag t="live" /> — it genuinely changes what you see or what the prediction engine does right now — or clearly marked when it isn't yet.</p></div>
        {msg && <div role="status" className="card sticky top-16 z-30 border-glow/50 p-3 text-[12px]">{msg}</div>}

        <Section id="appearance" icon={Palette} title="Appearance" desc="Theme, accent color, and layout density. Applies instantly across the app.">
          <Row label="Theme" tag="live" desc="System follows your OS/browser preference automatically."><Segmented value={s.mode} onChange={(mode) => set({ mode })} options={[{ v: "light", label: "Light" }, { v: "dark", label: "Dark" }, { v: "system", label: "System" }]} /></Row>
          <Row label="Quick presets" tag="live" desc="Reset colors to a curated light or dark palette."><button className="btn-ghost" onClick={() => set({ mode: "light", accent: "#E10600", colors: {} })}>Light preset</button><button className="btn-ghost" onClick={() => set({ mode: "dark", accent: "#E10600", colors: {} })}>Dark preset</button></Row>
          <Row label="Accent color" tag="live" desc="Used for buttons, links, active states, and highlights everywhere."><input type="color" aria-label="Accent color" value={s.accent} onChange={(e) => set({ accent: e.target.value })} /><input className="field !w-28 font-mono" value={s.accent} maxLength={7} onChange={(e) => /^#[0-9a-f]{0,6}$/i.test(e.target.value) && set({ accent: e.target.value })} /></Row>
          <Row label="Font size" tag="live" desc="Scales all text app-wide, independent of your browser zoom."><Slider value={s.fontScale} min={0.85} max={1.25} step={0.05} onChange={(fontScale) => set({ fontScale })} fmt={(v) => `${v.toFixed(2)}×`} /></Row>
          <Row label="Corner roundness" tag="live" desc="Applies to cards, buttons, inputs, and panels."><Slider value={s.radius} min={0} max={16} step={1} onChange={(radius) => set({ radius })} fmt={(v) => `${v}px`} /></Row>
          <Row label="Density" tag="live" desc="Compact tightens spacing across every page for more on-screen at once."><Segmented value={s.density} onChange={(density) => set({ density })} options={[{ v: "comfortable", label: "Comfortable" }, { v: "compact", label: "Compact" }]} /></Row>
          <details className="py-3"><summary className="cursor-pointer text-[12px] font-semibold">Project colors (tune all UI/chart/tooltip colors)</summary>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-mute sm:col-span-2 lg:col-span-3">Core</div>
              {colorRow("bg", "Background", "#050a17")}{colorRow("surface", "Surface", "#0b1430")}{colorRow("border", "Border", "#182644")}{colorRow("text", "Text", "#f1f5f9")}{colorRow("mute", "Muted text", "#8793ad")}{colorRow("accent2", "Accent highlight", "#ff2d46")}
              <div className="mt-1 text-[10px] font-semibold uppercase tracking-wide text-mute sm:col-span-2 lg:col-span-3">Status</div>
              {colorRow("success", "Success", "#22c55e")}{colorRow("warning", "Warning", "#f59e0b")}{colorRow("danger", "Danger", "#ef4444")}{colorRow("info", "Info", "#38bdf8")}
              <div className="mt-1 text-[10px] font-semibold uppercase tracking-wide text-mute sm:col-span-2 lg:col-span-3">Charts & tooltips</div>
              {colorRow("chart1", "Chart 1", "#e10600")}{colorRow("chart2", "Chart 2", "#7c4dff")}{colorRow("chart3", "Chart 3", "#22c55e")}{colorRow("chart4", "Chart 4", "#f59e0b")}{colorRow("chart5", "Chart 5", "#06b6d4")}{colorRow("chart6", "Chart 6", "#ec4899")}{colorRow("tooltipBg", "Tooltip background", "#38bdf8")}{colorRow("tooltipText", "Tooltip text", "#dc2626")}
            </div>
            <div className="mt-3"><button className="btn-ghost" onClick={() => set({ colors: {} })}>Reset all custom colors</button></div>
          </details>
          <Row label="Share these settings" desc="Colors, theme and every control are stored in this browser. Copy a link to restore them on another device."><button className="btn-ghost" onClick={async () => { const url = `${location.origin}/settings#s=${encode({ ...s, apiBase: "" })}`; try { await navigator.clipboard.writeText(url); flash("Settings link copied."); } catch { flash(url); } }}>Sync now</button></Row>
        </Section>

        <Section id="accessibility" icon={Accessibility} title="Accessibility" desc="Every toggle here is wired to real CSS applied across the whole app, not just this page.">
          <Row label="Reduce motion" tag="live" desc="Disables animations and transitions app-wide."><Toggle checked={s.reduceMotion} onChange={(v) => set({ reduceMotion: v })} label="Reduce motion" /></Row>
          <Row label="High contrast" tag="live" desc="Thicker borders and stronger contrast for low-vision readability."><Toggle checked={s.highContrast} onChange={(v) => set({ highContrast: v })} label="High contrast" /></Row>
          <Row label="Dyslexia-friendly font" tag="live" desc="Switches body text to Atkinson Hyperlegible."><Toggle checked={s.dyslexia} onChange={(v) => set({ dyslexia: v })} label="Dyslexia-friendly font" /></Row>
          <Row label="Always underline links" tag="live" desc="Makes links identifiable without relying on color alone."><Toggle checked={s.underlineLinks} onChange={(v) => set({ underlineLinks: v })} label="Always underline links" /></Row>
        </Section>

        <Section id="engine" icon={Cpu} title="Prediction Engine Defaults" desc="These seed the Dashboard's race-condition sliders every time you open it. Change them per-race on the Dashboard, or set your usual baseline here.">
          <div className="my-3 rounded-lg border border-sky-500/40 bg-sky-500/10 p-3 text-[11px] text-sky-200">These parameters are applied by the prediction engine on every request (sent from your browser with each run). They are not admin-gated and need no backend configuration.</div>
          <Row label="Simulation count" tag="live" desc="Default Monte Carlo simulations per prediction (100–50,000)."><Slider value={sim.sims} min={100} max={maxSims} step={100} onChange={S("sims")} fmt={(v) => String(v)} /></Row>
          <Row label="Chaos level" tag="live" desc="How random races get: higher means more upsets."><Slider value={sim.chaos * 100} min={0} max={100} step={1} onChange={(v) => setSim({ chaos: v / 100 })} fmt={(v) => String(Math.round(v))} /></Row>
          <Row label="Grid weight" tag="live" desc="How strongly the starting grid decides the finishing order."><Slider value={sim.grid_weight} min={0} max={1} step={0.01} onChange={S("grid_weight")} fmt={pctf} /></Row>
          <Row label="Wet influence" tag="live" desc="How much rain rewards wet-weather specialists."><Slider value={sim.wet_influence} min={0} max={1} step={0.01} onChange={S("wet_influence")} fmt={pctf} /></Row>
          <Row label="Reliability influence" tag="live" desc="Scales mechanical-failure risk."><Slider value={sim.reliability} min={0} max={1} step={0.01} onChange={S("reliability")} fmt={pctf} /></Row>
          <Row label="Strategy aggressiveness" tag="live" desc="Shifts strategy odds toward bolder, higher-variance calls."><Slider value={sim.strategy_aggr} min={0} max={1} step={0.01} onChange={S("strategy_aggr")} fmt={pctf} /></Row>
          <Row label="Safety car weight" tag="live" desc="Scales how often safety cars bunch up the field."><Slider value={sim.sc_weight} min={0} max={1} step={0.01} onChange={S("sc_weight")} fmt={pctf} /></Row>
          <Row label="Default weather" tag="live"><select className="field" value={sim.weather} onChange={(e) => setSim({ weather: e.target.value as SimParams["weather"] })}><option value="auto">Auto (forecast)</option><option value="dry">Dry</option><option value="mixed">Mixed</option><option value="wet">Wet</option></select></Row>
          <Row label="Default session" tag="live"><select className="field" value={sim.session} onChange={(e) => setSim({ session: e.target.value as SimParams["session"] })}><option value="practice">Practice</option><option value="qualifying">Qualifying</option><option value="race">Race</option><option value="sprint">Sprint</option></select></Row>
          <Row label="Mechanical failures" tag="live"><Toggle checked={sim.mechanical_failures} onChange={(v) => setSim({ mechanical_failures: v })} label="Mechanical failures" /></Row>
          <Row label="Safety cars" tag="live"><Toggle checked={sim.safety_car} onChange={(v) => setSim({ safety_car: v })} label="Safety cars" /></Row>
          <Row label="Enhanced model (blend season form)" tag="live"><Toggle checked={sim.enhanced} onChange={(v) => setSim({ enhanced: v })} label="Enhanced model" /></Row>
          <div className="flex items-center justify-between pt-3 text-[10px] text-mute"><span>Open the Dashboard to see these applied to a real prediction.</span><button className="btn-ghost" onClick={() => set({ sim: { ...DEFAULT_SIM } })}>Reset to defaults</button></div>
        </Section>

        <Section id="backend" icon={Server} title="Backend Configuration" desc="Server-side settings that affect every visitor, not just you. Saving requires the admin token (set it in Advanced below).">
          {!cfg?.admin_enabled && <div className="my-3 rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-[11px] text-amber-200">Admin changes are disabled until <code>SETTINGS_ADMIN_TOKEN</code> is set in your Vercel project's environment variables. Values below show what the server is currently using.</div>}
          <Row label="Cache TTL" tag="admin" desc="How long live API responses are cached in memory, in seconds."><input className="field" inputMode="numeric" value={srv.cache_ttl} onChange={(e) => setSrv({ ...srv, cache_ttl: e.target.value })} /><button className="btn-ghost" onClick={() => saveSrv("cache_ttl")}>Save</button></Row>
          <Row label="Data source priority" tag="admin" desc="Which upstream source the backend uses first."><select className="field" value={srv.source_priority} onChange={(e) => setSrv({ ...srv, source_priority: e.target.value })}><option value="jolpica_first">Live data → snapshot fallback</option><option value="seed_only">Snapshot only (offline)</option></select><button className="btn-ghost" onClick={() => saveSrv("source_priority")}>Save</button></Row>
          <Row label="Live update interval" tag="admin" desc="Seconds between live data refreshes advertised to clients."><input className="field" inputMode="numeric" value={srv.live_interval} onChange={(e) => setSrv({ ...srv, live_interval: e.target.value })} /><button className="btn-ghost" onClick={() => saveSrv("live_interval")}>Save</button></Row>
          <Row label="Model type" tag="admin" desc="Which rating model the backend uses when a request doesn't specify one."><select className="field" value={srv.model_type} onChange={(e) => setSrv({ ...srv, model_type: e.target.value })}><option value="monte_carlo">Monte Carlo (base ratings)</option><option value="monte_carlo_form">Monte Carlo + season form</option></select><button className="btn-ghost" onClick={() => saveSrv("model_type")}>Save</button></Row>
          <p className="pt-3 text-[10px] text-mute">Server currently reports: cache_ttl={cfg?.cache_ttl ?? "…"}, model_type={cfg?.model_type ?? "…"}, live_update_interval={cfg?.live_interval ?? "…"}, source_priority={cfg?.source_priority ?? "…"}. On serverless hosting these changes last until the instance recycles; set the matching environment variables to make them permanent.</p>
        </Section>

        <Section id="reference" icon={SlidersHorizontal} title="Reference Parameters" desc="Model weights behind every prediction. All of these are sent to the engine with each request.">
          <Row label="Driver strength weight" tag="live" desc="Weight of driver skill in the base rating."><Slider value={sim.driver_w} min={0} max={1} step={0.05} onChange={S("driver_w")} fmt={pctf} /></Row>
          <Row label="Team pace weight" tag="live" desc="Weight of car performance in the base rating."><Slider value={sim.team_w} min={0} max={1} step={0.05} onChange={S("team_w")} fmt={pctf} /></Row>
          <Row label="Track characteristics weight" tag="live" desc="Amplifies or mutes circuit traits (overtaking, tyre wear, safety cars)."><Slider value={sim.track_w} min={0} max={2} step={0.05} onChange={S("track_w")} fmt={pctf} /></Row>
          <Row label="Weather impact weight" tag="live" desc="Amplifies or mutes the effect of rain."><Slider value={sim.weather_w} min={0} max={2} step={0.05} onChange={S("weather_w")} fmt={pctf} /></Row>
          <Row label="Tyre degradation weight" tag="live" desc="Scales tyre wear in strategy odds and race variance."><Slider value={sim.deg_w} min={0} max={2} step={0.05} onChange={S("deg_w")} fmt={pctf} /></Row>
          <Row label="Form responsiveness (Elo K-factor equivalent)" tag="live" desc="How quickly ratings follow current-season results. 32 blends 50% season form."><Slider value={sim.form_k} min={8} max={64} step={1} onChange={S("form_k")} fmt={(v) => String(v)} /></Row>
          <Row label="Confidence interval" tag="live" desc="Interval shown on win probabilities."><select className="field" value={sim.ci} onChange={(e) => setSim({ ci: Number(e.target.value) as SimParams["ci"] })}><option value={0.9}>90%</option><option value={0.95}>95%</option><option value={0.99}>99%</option></select></Row>
          <Row label="Ensemble ML / MC weight" tag="fixed" desc="This build is a pure Monte Carlo engine."><span className="text-[11px] text-mute">100% Monte Carlo</span></Row>
          <Row label="Calibration method" tag="fixed" desc="Probabilities are raw simulation frequencies."><span className="text-[11px] text-mute">None (raw frequencies)</span></Row>
        </Section>

        <Section id="layout" icon={LayoutDashboard} title="Dashboard Layout" desc="Hide panels you don't use, and pick which page opens first.">
          <Row label="Show manual grid editor" tag="live" desc="Turn off if you always let qualifying set the grid."><Toggle checked={s.showGrid} onChange={(v) => set({ showGrid: v })} label="Show manual grid editor" /></Row>
          <Row label="Show export panel" tag="live" desc="The CSV / JSON / PDF export card at the bottom of the Dashboard."><Toggle checked={s.showExport} onChange={(v) => set({ showExport: v })} label="Show export panel" /></Row>
          <Row label="Compact tables" tag="live" desc="Tighter row spacing in Standings, Predictions and H2H tables."><Toggle checked={s.compactTables} onChange={(v) => set({ compactTables: v })} label="Compact tables" /></Row>
          <Row label="Default landing page" tag="live" desc="Where the F1 logo and “/” take you."><select className="field" value={s.landing} onChange={(e) => set({ landing: e.target.value as Settings["landing"] })}><option value="dashboard">Dashboard</option><option value="predictions">Predictions</option><option value="standings">Standings</option><option value="head2head">Head2Head</option><option value="fantasy">Fantasy League</option></select></Row>
        </Section>

        <Section id="notifications" icon={Bell} title="Notifications" desc="Real browser notifications, scheduled entirely in your browser — no backend or account needed. They fire only while a tab with this app is open.">
          <Row label="Race start reminders" tag="live" desc={`Requires notification permission for this site (currently: ${permission}).`}><Toggle checked={s.remind} onChange={enableReminders} label="Race start reminders" /></Row>
          <Row label="Remind me before" tag="live" desc="How far ahead of the next race start to notify you."><select className="field" value={s.remindLead} onChange={(e) => set({ remindLead: Number(e.target.value) })}><option value={15}>15 minutes</option><option value={30}>30 minutes</option><option value={60}>1 hour</option><option value={180}>3 hours</option><option value={1440}>1 day</option></select></Row>
          <Row label="Test notification" desc="Check that notifications reach you."><button className="btn-ghost" disabled={permission !== "granted"} onClick={() => new Notification("F1 Predictor 2026", { body: "Notifications are working.", icon: "/img/logo-f1.png" })}>Send test</button></Row>
        </Section>

        <Section id="profile" icon={User} title="Profile" desc="There's no account system, so this is local personalization only — your favorite driver and team are highlighted in the Standings tables.">
          <Row label="Display name" tag="live"><input className="field" maxLength={24} value={s.displayName} onChange={(e) => set({ displayName: e.target.value })} /></Row>
          <Row label="Favorite driver code" tag="live" desc="Highlighted with a star in Standings."><select className="field" value={s.favDriver} onChange={(e) => set({ favDriver: e.target.value })}><option value="">None</option>{[...(drivers ?? [])].sort((a, b) => a.code.localeCompare(b.code)).map((d) => <option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}</select></Row>
          <Row label="Favorite team" tag="live" desc="Highlighted in both Standings tables."><select className="field" value={s.favTeam} onChange={(e) => set({ favTeam: e.target.value })}><option value="">None</option>{teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select></Row>
        </Section>

        <Section id="advanced" icon={Wrench} title="Advanced" desc="API connection, admin access, and developer options.">
          {import.meta.env.PROD && !import.meta.env.VITE_ALLOW_API_OVERRIDE ? null : (
          <Row label="API base URL override" tag="live" desc="Point this frontend at a different backend host without rebuilding. Leave blank to use the default."><input className="field font-mono" placeholder="https://api.example.com" value={s.apiBase} onChange={(e) => set({ apiBase: e.target.value.trim() })} /></Row>
          )}
          <Row label="Request timeout" tag="live" desc="Aborts a stalled request after this long."><Slider value={s.timeoutMs} min={2000} max={60000} step={1000} onChange={(timeoutMs) => set({ timeoutMs })} fmt={(v) => `${v}ms`} /></Row>
          <Row label="Debug logging" tag="live" desc="Logs every API request's timing and status to the browser console."><Toggle checked={s.debug} onChange={(v) => set({ debug: v })} label="Debug logging" /></Row>
          <Row label="Keyboard shortcuts" tag="live" desc="Enable the g-then-letter navigation shortcuts (see below)."><Toggle checked={s.shortcuts} onChange={(v) => set({ shortcuts: v })} label="Keyboard shortcuts" /></Row>
          <Row label="Reduce data usage" tag="live" desc="Hides hero imagery and heavy photos."><Toggle checked={s.saveData} onChange={(v) => set({ saveData: v })} label="Reduce data usage" /></Row>
          <Row label="Admin access" wide desc="Needed only for the Backend Configuration fields above. Kept in this browser tab's session only — never saved to disk, never exported. If your backend has no SETTINGS_ADMIN_TOKEN configured, no token will work.">
            <input className="field font-mono" type="password" autoComplete="off" placeholder="Admin token" value={token} onChange={(e) => setToken(e.target.value)} />
            <button className="btn-ghost shrink-0" onClick={async () => { sessionStorage.setItem("f1p26_admin", token); try { await api.adminVerify(); flash("Admin token accepted."); } catch (e) { flash((e as Error).message); } }}>Save &amp; test</button></Row>
        </Section>

        <Section id="shortcuts" icon={Keyboard} title="Keyboard Shortcuts" desc="Active whenever the toggle in Advanced is on and you're not typing in a field.">
          <div className="grid gap-2 py-3 sm:grid-cols-2">{SHORTCUTS.map((x) => <div key={x.label} className="flex items-center justify-between rounded-md border border-edge px-3 py-2 text-[12px]">{x.label}<span className="text-mute"><kbd>g</kbd> then <kbd>{x.keys}</kbd></span></div>)}
            <div className="flex items-center justify-between rounded-md border border-edge px-3 py-2 text-[12px]">Open this shortcuts list<kbd>?</kbd></div></div>
        </Section>

        <Section id="data" icon={Shield} title="Data & Privacy" desc="Everything on this page lives in your browser's local storage. Nothing here is sent anywhere except the specific backend syncs described above.">
          <div className="flex flex-wrap gap-2 py-3">
            <button className="btn-ghost" onClick={() => download("f1-predictor-settings.json", JSON.stringify({ ...s, apiBase: "" }, null, 2), "application/json")}>Export settings as JSON</button>
            <button className="btn-ghost" onClick={() => file.current?.click()}>Import settings</button>
            <input ref={file} type="file" accept="application/json" hidden onChange={async (e) => { const f = e.target.files?.[0]; if (!f) return; try { replaceSettings(JSON.parse(await f.text())); flash("Settings imported."); } catch { flash("That file isn't valid settings JSON."); } e.target.value = ""; }} />
            <button className="btn-ghost" onClick={() => { qc.clear(); sessionStorage.removeItem("f1p26_admin"); setToken(""); flash("Local cache cleared."); }}>Clear local cache</button>
          </div>
          <div className="py-3"><div className="mb-2 text-[12px] font-bold text-glow">Danger zone</div>
            <button className="rounded-md border border-glow/60 px-3 py-2 text-[12px] font-semibold text-glow hover:bg-f1red/10" onClick={() => { if (confirm("Reset all settings to their defaults?")) { resetAll(); qc.clear(); flash("All settings reset."); } }}>Reset all settings to defaults</button></div>
        </Section>
      </div>
    </div>
  );
}
