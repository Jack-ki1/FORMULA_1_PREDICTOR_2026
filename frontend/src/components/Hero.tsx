import { ArrowRight, CalendarDays, Gauge, MapPin, Route as RouteIcon, Ruler, RotateCw, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useNextRace } from "../lib/hooks";
import type { Race } from "../lib/api";
import { Flag, Skeleton, ordinalDate } from "./ui";

function useCountdown(iso?: string) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(t); }, []);
  if (!iso) return null;
  const s = Math.max(0, Math.floor((new Date(iso).getTime() - now) / 1000));
  return { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60, over: s === 0 };
}

const dateRange = (r: Race) => {
  const a = new Date(r.date_start + "T12:00:00Z"), b = new Date(r.date_end + "T12:00:00Z");
  const same = a.getUTCMonth() === b.getUTCMonth();
  return `${ordinalDate(r.date_start)} – ${same ? b.getUTCDate() : ordinalDate(r.date_end)}, ${b.getUTCFullYear()}`;
};

function Details({ race, onClose }: { race: Race; onClose: () => void }) {
  useEffect(() => { const k = (e: KeyboardEvent) => e.key === "Escape" && onClose(); document.addEventListener("keydown", k); return () => document.removeEventListener("keydown", k); }, [onClose]);
  const c = race.circuit;
  const rows: [string, string][] = [["Round", `${race.round} of 23`], ["Circuit", c.name], ["Weekend", dateRange(race)], ["Lights out (your time)", new Date(race.start_utc).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })],
    ["Lap record", c.lap_record ?? "—"], ["Length / turns", `${c.length_km ?? "—"} km · ${c.turns ?? "—"} turns`]];
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4" onClick={onClose} role="dialog" aria-modal="true" aria-label="Race details">
      <div className="card w-full max-w-md p-5" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between"><h3 className="flex items-center gap-2 text-[15px] font-bold"><Flag cc={race.cc} />{race.name}</h3><button onClick={onClose} aria-label="Close"><X size={16} /></button></div>
        <dl className="divide-y divide-edge text-[12px]">{rows.map(([k, v]) => <div key={k} className="flex justify-between gap-4 py-2"><dt className="text-mute">{k}</dt><dd className="text-right font-medium">{v}</dd></div>)}</dl>
      </div>
    </div>
  );
}

export default function Hero() {
  const { data: race } = useNextRace();
  const cd = useCountdown(race?.start_utc);
  const [open, setOpen] = useState(false);
  const c = race?.circuit;
  const [mapOk, setMapOk] = useState(true);
  return (
    <section className="keep-dark relative isolate min-h-[260px] overflow-hidden border-b border-edge bg-[#030814]">
      <img src="/img/hero-red.jpg" alt="" className="heavy-img absolute right-0 top-0 -z-10 h-full w-[46%] object-cover opacity-90" style={{ maskImage: "linear-gradient(to right, transparent, #000 45%)", WebkitMaskImage: "linear-gradient(to right, transparent, #000 45%)" }} />
      <img src="/img/hero-car.jpg" alt="" className="heavy-img absolute bottom-0 left-[34%] -z-10 hidden h-[78%] w-auto md:block" style={{ maskImage: "radial-gradient(ellipse at 50% 55%, #000 45%, transparent 78%)", WebkitMaskImage: "radial-gradient(ellipse at 50% 55%, #000 45%, transparent 78%)" }} />
      <div className="grid gap-4 p-5 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-center md:px-7 md:py-6">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em]">2026 Formula 1 World Championship</p>
          <p className="mt-4 text-[16px] font-medium uppercase tracking-[0.12em] text-slate-300">{race?.status === "live" ? "Live now" : "Next race"}</p>
          {race ? (
            <>
              <h1 className="mt-1 flex flex-wrap items-center gap-2 text-[22px] font-extrabold uppercase leading-tight md:text-[26px]"><Flag cc={race.cc} className="h-5 w-7" />{race.name}<Flag cc={race.cc} className="h-5 w-7" /></h1>
              <p className="mt-2 flex items-center gap-2 text-[11px] text-slate-300"><MapPin size={12} />{race.circuit.name}<span className="text-mute">•</span>{race.circuit.locality}, {race.country}</p>
              <p className="mt-1 flex items-center gap-2 text-[11px] text-slate-300"><CalendarDays size={12} />{dateRange(race)}</p>
            </>
          ) : <Skeleton className="mt-2 h-20 w-72" />}
          <div className="mt-4 flex flex-wrap items-center gap-4">
            <div className="rounded-lg border border-edge bg-black/35 px-4 py-2 backdrop-blur">
              <div className="label !text-[9px]">{cd?.over ? "Lights out" : "Race starts in"}</div>
              <div className="mt-1 flex gap-4 tabular-nums">
                {cd ? ([[cd.d, "Days"], [cd.h, "Hrs"], [cd.m, "Mins"], [cd.s, "Secs"]] as const).map(([v, l]) => (
                  <div key={l} className="text-center"><div className="text-[22px] font-bold leading-none">{String(v).padStart(2, "0")}</div><div className="mt-0.5 text-[8px] uppercase text-mute">{l}</div></div>
                )) : <Skeleton className="h-9 w-48" />}
              </div>
            </div>
            <button className="btn-red" disabled={!race} onClick={() => setOpen(true)}>View Race Details <ArrowRight size={13} /></button>
          </div>
        </div>
        <div className="w-full rounded-lg border border-edge bg-black/40 p-3 text-[11px] backdrop-blur md:w-[170px]">
          <div className="relative mx-auto grid h-[74px] place-items-center">
            {c && mapOk ? <img src={`/img/circuits/${c.id}.png`} alt={`${c.name} layout`} onError={() => setMapOk(false)} className="h-full object-contain mix-blend-screen" />
              : <RouteIcon size={34} className="text-white/25" aria-label="Circuit map not available" />}
          </div>
          <div className="label mb-2 mt-2">Circuit info</div>
          {([[<Ruler size={12} key="a" />, "Length", c?.length_km ? `${c.length_km} km` : "—"], [<RotateCw size={12} key="b" />, "Turns", c?.turns ?? "—"], [<Gauge size={12} key="c" />, "Lap Record", c?.lap_record ?? "—"], [<RouteIcon size={12} key="d" />, "DRS Zones", c?.drs ?? "—"]] as const).map(([i, l, v]) => (
            <div key={l} className="flex items-center justify-between py-1 text-slate-300"><span className="flex items-center gap-2">{i}{l}</span><b className="text-white">{v}</b></div>
          ))}
        </div>
        <div className="hidden text-right md:block md:w-[120px]">
          <img src="/img/logo-f1.png" alt="" className="ml-auto mb-4 h-7 w-auto" />
          <div className="space-y-1 text-[12px] font-semibold uppercase tracking-[0.32em] text-slate-200"><div>Faster</div><div>Smarter</div><div>Predicted</div></div>
        </div>
      </div>
      {open && race && <Details race={race} onClose={() => setOpen(false)} />}
    </section>
  );
}
