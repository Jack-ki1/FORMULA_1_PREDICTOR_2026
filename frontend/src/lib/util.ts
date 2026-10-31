import type { Prediction, Race, SessionKind } from "./api";

export const DURATION: Record<string, number> = { FP1: 60, FP2: 60, FP3: 60, SQ: 45, SPR: 45, Q: 60, R: 120 }; // minutes

export function sessionState(r: Race | undefined, now: number) {
  if (!r) return null;
  const list = r.sessions.map((s) => { const t = Date.parse(s.start_utc); return { ...s, t, end: t + (DURATION[s.key] ?? 60) * 60000 }; });
  const live = list.find((s) => now >= s.t && now < s.end);
  const next = list.find((s) => s.t > now);
  return { list, live, next, done: !live && !next, estimated: list.some((s) => s.estimated) };
}

export const overtakingLabel = (v: number) => (v >= 0.65 ? "Easy" : v >= 0.4 ? "Medium" : "Hard");
export const sessionWord = (s: SessionKind) => ({ practice: "Practice", qualifying: "Qualifying", race: "Race", sprint: "Sprint" })[s];
export const headlineWord = (s: SessionKind) => ({ practice: "Fastest in session", qualifying: "Pole position", race: "Race win", sprint: "Sprint win" })[s];
export const pad = (n: number) => String(n).padStart(2, "0");
export const short = (n: number) => (n >= 1000 ? `${n % 1000 === 0 ? n / 1000 : (n / 1000).toFixed(1)}k` : String(n));

export function download(name: string, text: string, type = "text/plain") {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

export function predictionCsv(p: Prediction) {
  const head = ["pos", "code", "name", "team", "win", "podium", "points_prob", "dnf", "avg_points", "exp_pos", "fastest_lap", "pole", "avg_grid", "reach_q2", "reach_q3"];
  const rows = p.drivers.map((d) => [d.pos, d.code, d.name, d.team.name, d.win, d.podium, d.points_prob, d.dnf, d.avg_points, d.exp_pos, d.fastest_lap, d.pole, d.avg_grid, d.reach_q2, d.reach_q3]
    .map((v) => (typeof v === "number" ? Number(v.toFixed(4)) : `"${String(v).replace(/"/g, '""')}"`)).join(","));
  return [head.join(","), ...rows].join("\n");
}
