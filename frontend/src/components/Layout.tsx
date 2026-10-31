import { ChevronDown, Home, Moon, Search, Settings, Trophy, Users } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { MotionConfig } from "framer-motion";
import { useRaces, useSearch } from "../lib/hooks";
import { useApp } from "../lib/store";
import { Flag, TeamLogo, cx } from "./ui";
import { useReminders, useShortcuts } from "./Shortcuts";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: <Home size={16} /> },
  { to: "/standings", label: "Standings", icon: <Trophy size={16} /> },
  { to: "/head2head", label: "Head2Head", icon: <span className="w-4 text-center text-[11px] font-black leading-none">VS</span> },
  { to: "/fantasy", label: "Fantasy League", icon: <Users size={16} /> },
  { to: "/settings", label: "Settings", icon: <Settings size={16} /> },
];

function SearchBox() {
  const [q, setQ] = useState(""); const [dq, setDq] = useState(""); const [open, setOpen] = useState(false);
  const nav = useNavigate(); const run = useApp((s) => s.run); const ref = useRef<HTMLDivElement>(null); const input = useRef<HTMLInputElement>(null);
  const { data } = useSearch(dq);
  useEffect(() => { const t = setTimeout(() => setDq(q.trim()), 200); return () => clearTimeout(t); }, [q]);
  useEffect(() => {
    const click = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    const key = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); input.current?.focus(); } if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", click); document.addEventListener("keydown", key);
    return () => { document.removeEventListener("mousedown", click); document.removeEventListener("keydown", key); };
  }, []);
  const go = (to: string) => { setOpen(false); setQ(""); nav(to); };
  const empty = data && !data.races.length && !data.drivers.length && !data.teams.length;
  return (
    <div ref={ref} className="relative w-full max-w-[370px]">
      <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-mute" />
      <input ref={input} value={q} onChange={(e) => { setQ(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)} placeholder="Search races, drivers, teams…  (Ctrl K)"
        aria-label="Search" className="field !rounded-lg !py-2 !pl-9" />
      {open && dq && (
        <div className="card absolute left-0 right-0 top-11 z-50 max-h-80 overflow-auto p-1.5 text-[12px] shadow-2xl">
          {empty && <p className="p-3 text-mute">No matches for “{dq}”.</p>}
          {data?.races.map((r) => (
            <button key={r.id} className="flex w-full items-center gap-2 rounded-md p-2 text-left hover:bg-white/5" onClick={() => { run({ race_id: r.id }); go("/"); }}>
              <Flag cc={r.cc} /><span className="font-medium">{r.name}</span><span className="ml-auto text-[10px] text-mute">Race</span>
            </button>
          ))}
          {data?.drivers.map((d) => (
            <button key={d.code} className="flex w-full items-center gap-2 rounded-md p-2 text-left hover:bg-white/5" onClick={() => go(`/head2head?a=${d.code}`)}>
              <TeamLogo team={d.team} size={16} /><span className="font-medium">{d.name}</span><span className="ml-auto text-[10px] text-mute">Driver</span>
            </button>
          ))}
          {data?.teams.map((t) => (
            <button key={t.id} className="flex w-full items-center gap-2 rounded-md p-2 text-left hover:bg-white/5" onClick={() => go("/standings?tab=constructors")}>
              <TeamLogo team={t} size={16} /><span className="font-medium">{t.name}</span><span className="ml-auto text-[10px] text-mute">Team</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function TopBar() {
  const { s, set } = useApp();
  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-4 border-b border-edge bg-ink/90 px-4 backdrop-blur">
      <Link to="/" className="flex shrink-0 items-center gap-3" aria-label="F1 Predictor 2026 home">
        <img src="/img/logo-f1.png" alt="" className="h-6 w-auto" />
        <div className="hidden leading-tight sm:block"><div className="text-[13px] font-extrabold tracking-wide">F1 PREDICTOR 2026</div><div className="text-[8px] font-medium tracking-[0.12em] text-mute">RACE INTELLIGENCE, REIMAGINED</div></div>
      </Link>
      <div className="flex flex-1 justify-center lg:justify-start lg:pl-24"><SearchBox /></div>
      <button onClick={() => set({ mode: s.mode === "light" ? "dark" : "light" })} aria-label="Toggle light and dark theme" title="Toggle light / dark theme" className="grid h-8 w-8 place-items-center rounded-full border border-edge bg-white/[0.03] text-slate-300 hover:text-white"><Moon size={14} /></button>
      <div className="hidden items-center gap-2 sm:flex">
        <img src="/img/avatar-user.png" alt="" className="h-8 w-8 rounded-full object-cover ring-1 ring-white/10" />
        <div className="text-[11px] leading-tight"><div className="font-semibold">{s.displayName || "Guest"}</div><div className="text-mute">Racing Fan</div></div>
        <ChevronDown size={14} className="text-mute" />
      </div>
    </header>
  );
}

const Footer = () => (
  <footer className="mt-5 border-t border-edge px-4 py-4 text-[10px] text-mute">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2"><img src="/img/logo-f1.png" alt="" className="h-4 w-auto" /><b className="text-slate-200">F1 PREDICTOR 2026</b><span>Race Intelligence, Reimagined</span></div>
      <nav className="flex gap-5">{[...NAV, { to: "/guide", label: "Guide" }].map((n) => <Link key={n.to} to={n.to} className="hover:text-white">{n.label}</Link>)}</nav>
      <span>© 2026 F1 Predictor. Predictions are modeled estimates, not betting advice.</span>
    </div>
    <p className="mt-2 text-center opacity-70">Unofficial fan project. Not affiliated with Formula 1, the FIA or any team. Predictions are probabilities, not promises.</p>
  </footer>
);

export function Layout() {
  const help = useShortcuts(); useReminders();
  const reduce = useApp((x) => x.s.reduceMotion);
  return (
    <MotionConfig reducedMotion={reduce ? "always" : "user"}>
    <div className="min-h-screen">
      <TopBar />
      <div className="flex">
        <aside className="sticky top-14 hidden h-[calc(100vh-56px)] w-36 shrink-0 border-r border-edge p-2 lg:block" style={{ background: "rgb(var(--side))" }}>
          <nav className="mt-2 space-y-1">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end className={({ isActive }) => cx("flex items-center gap-3 rounded-md px-3 py-2.5 text-[12px] font-medium transition", isActive ? "bg-gradient-to-r from-[#c1121f] to-[#7a0c28] text-white on-accent shadow-[0_8px_24px_-10px_rgba(225,6,0,.8)]" : "text-slate-300 hover:bg-white/5")}>
                {n.icon}{n.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1 pb-16 lg:pb-0"><Outlet /><Footer /></main>
        {help}
      </div>
      <nav className="fixed inset-x-0 bottom-0 z-40 flex justify-around border-t border-edge bg-ink/95 py-2 backdrop-blur lg:hidden" aria-label="Mobile">
        {NAV.map((n) => (
          <NavLink key={n.to} to={n.to} end aria-label={n.label} className={({ isActive }) => cx("grid h-10 w-12 place-items-center rounded-md", isActive ? "bg-f1red/20 text-glow" : "text-slate-400")}>{n.icon}</NavLink>
        ))}
      </nav>
    </div>
    </MotionConfig>
  );
}
