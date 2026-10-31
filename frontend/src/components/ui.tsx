import type { ReactNode } from "react";
import { useState } from "react";
import { AE, AR, AT, AU, AZ, BE, BH, BR, CA, CN, DE, ES, FI, FR, GB, HU, IT, JP, MC, MX, MY, NL, NZ, PT, QA, SA, SG, TH, US } from "country-flag-icons/react/3x2";
import type { FlagComponent } from "country-flag-icons/react/3x2";
import type { Team } from "../lib/api";

export const cx = (...a: (string | false | null | undefined)[]) => a.filter(Boolean).join(" ");
export const pct = (x: number, d = 1) => `${(x * 100).toFixed(d)}%`;
export const surname = (n: string) => n.split(" ").slice(-1)[0];
export const ordinalDate = (iso: string) => new Date(iso + "T12:00:00Z").toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });

const FLAGS: Record<string, FlagComponent> = { AE, AR, AT, AU, AZ, BE, BH, BR, CA, CN, DE, ES, FI, FR, GB, HU, IT, JP, MC, MX, MY, NL, NZ, PT, QA, SA, SG, TH, US };
export function Flag({ cc, className = "h-3.5 w-5" }: { cc: string; className?: string }) {
  const F = FLAGS[cc];
  return F ? <F className={cx("rounded-[2px] object-cover", className)} aria-label={cc} /> : <span className={cx("inline-block rounded-[2px] bg-white/10", className)} />;
}

const LOGOS = new Set(["red_bull", "mclaren", "ferrari", "mercedes", "aston_martin"]);
export function TeamLogo({ team, size = 20 }: { team: Team; size?: number }) {
  if (LOGOS.has(team.id)) return <img src={`/img/teams/${team.id}.png`} alt={team.name} width={size} height={size} className="rounded-[4px] object-cover" style={{ width: size * 1.35, height: size }} />;
  return (
    <span className="grid shrink-0 place-items-center rounded-[4px] text-[9px] font-bold text-white/90" style={{ width: size * 1.35, height: size, background: `${team.color}33`, border: `1px solid ${team.color}88` }}>
      {team.name.split(" ").map((w) => w[0]).join("").slice(0, 2)}
    </span>
  );
}

const PHOTOS = new Set(["VER", "NOR"]);
export function Avatar({ code, team, size = 40 }: { code: string; team: Team; size?: number }) {
  const [bad, setBad] = useState(false);
  if (PHOTOS.has(code) && !bad)
    return <img src={`/img/drivers/${code}.png`} alt={code} onError={() => setBad(true)} className="shrink-0 rounded-full object-cover ring-1 ring-white/10" style={{ width: size, height: size }} />;
  return (
    <span className="grid shrink-0 place-items-center rounded-full text-[11px] font-bold text-white" style={{ width: size, height: size, background: `linear-gradient(135deg, ${team.color}55, #0b1630)`, border: `1px solid ${team.color}99` }}>
      {code}
    </span>
  );
}

export function Progress({ value, tone = "red" }: { value: number; tone?: "red" | "violet" | "green" }) {
  const g = { red: "from-f1red to-glow", violet: "from-violet to-[#a78bfa]", green: "from-emerald-500 to-emerald-300" }[tone];
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.07]">
      <div className={cx("h-full rounded-full bg-gradient-to-r transition-[width] duration-700", g)} style={{ width: `${Math.max(2, Math.min(100, value * 100))}%` }} />
    </div>
  );
}

export function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} onClick={() => onChange(!checked)}
      className={cx("relative h-[18px] w-8 shrink-0 rounded-full transition", checked ? "bg-gradient-to-r from-f1red to-glow" : "bg-white/15")}>
      <span className={cx("absolute top-[2px] h-[14px] w-[14px] rounded-full bg-white transition-all", checked ? "left-[16px]" : "left-[2px]")} />
    </button>
  );
}

export function Segmented<T extends string>({ value, options, onChange }: { value: T; options: { v: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <div className="inline-flex rounded-full border border-edge bg-black/30 p-0.5 text-[10px]">
      {options.map((o) => (
        <button key={o.v} onClick={() => onChange(o.v)} className={cx("rounded-full px-3 py-1 font-medium transition", value === o.v ? "bg-f1red text-white on-accent" : "text-mute hover:text-white")}>{o.label}</button>
      ))}
    </div>
  );
}

export function CardTitle({ icon, title, sub, right }: { icon?: ReactNode; title: string; sub?: string; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-start justify-between gap-2">
      <div className="flex items-center gap-2">
        {icon && <span className="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-f1red/30 to-transparent text-glow ring-1 ring-f1red/40">{icon}</span>}
        <div><h3 className="text-[13px] font-bold leading-tight">{title}</h3>{sub && <p className="text-[10px] text-mute">{sub}</p>}</div>
      </div>
      {right}
    </div>
  );
}

export const Card = ({ className, children }: { className?: string; children: ReactNode }) => <div className={cx("card", className)}>{children}</div>;

export const Skeleton = ({ className }: { className?: string }) => <div className={cx("skeleton", className)} />;

export function ErrorNote({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <div className="card flex items-center justify-between gap-3 p-4 text-[12px] text-red-300" role="alert">
      <span>Could not load data: {error instanceof Error ? error.message : "unknown error"}</span>
      {retry && <button className="btn-ghost" onClick={retry}>Retry</button>}
    </div>
  );
}
