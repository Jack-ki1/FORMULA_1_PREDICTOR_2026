
export interface Team { id: string; name: string; color: string }
export interface Circuit { id: string; name: string; locality: string; length_km: number | null; turns: number | null; lap_record: string | null; drs: number | null; laps: number | null; overtaking: number; tyre_wear: number; sc_prob: number; lat: number | null; lon: number | null }
export interface Sess { key: string; name: string; start_utc: string; estimated: boolean }
export interface Race { id: string; round: number; name: string; country: string; cc: string; date_start: string; date_end: string; start_utc: string; winner: string | null; status: "completed" | "live" | "upcoming"; circuit: Circuit; sprint: boolean; sessions: Sess[]; labels: { practice_day: string; quali_day: string; race_day: string } }
export interface DriverPred { pos: number; code: string; name: string; team: Team; cc: string; number: number | null; avg_grid: number; reach_q2: number; reach_q3: number; pace_gap?: number; pace_lo?: number; pace_hi?: number; long_gap?: number; top3?: number; win: number; win_ci: number; podium: number; points_prob: number; dnf: number; avg_points: number; exp_pos: number; fastest_lap: number; pole: number; avg_quali: number; dist: number[]; gap: number; avg_gain?: number; win_sc?: number; win_nosc?: number }
export interface Qual { pos: number; code: string; pole: number; gap: number; time: string; q2: number; q3: number }
export interface Strategy { name: string; stops: string; tyres: string; prob: number; optimal: boolean }
export interface Factor { name: string; level: "High" | "Medium" | "Low"; share: number }
export interface Day { date: string; temp: number | null; rain_prob: number | null; wind: number | null; humidity: number | null; label: string; kind: string }
export interface Forecast { days: Day[]; race_day: Day }
export type SessionKind = "practice" | "qualifying" | "sprint_qualifying" | "sprint" | "race";
export interface Engine { grid_weight: number; wet_influence: number; reliability: number; strategy_aggr: number; sc_weight: number; team_w: number; driver_w: number; track_w: number; weather_w: number; deg_w: number; form_k: number; ci: 0.9 | 0.95 | 0.99 }
export interface SimParams extends Engine { race_id: string | null; sims: number; session: SessionKind; sub: "" | "FP1" | "FP2" | "FP3"; qualiView: "Q1" | "Q2" | "Q3" | "Full"; weather: "auto" | "dry" | "mixed" | "wet"; mechanical_failures: boolean; safety_car: boolean; enhanced: boolean; chaos: number; grid_mode: "auto" | "manual"; grid: string[] }
export interface Prediction {
  race: Race; params: SimParams & { weather_requested: string }; forecast: Forecast | null; rain_prob: number | null; grid_source: "manual" | "live" | "simulated"; grid_locked: number;
  team_points: { team: Team; points: number }[]; source: "live" | "seed"; as_of_round: number; elapsed_ms: number;
  drivers: DriverPred[]; qualifying: Qual[]; strategies: Strategy[]; factors: Factor[]; confidence: number; sharpness: number; safety_car_rate: number; safety_car_prob: number; seed: number; weather_used: string;
  quali_segments?: { teammate_battle: { a: string; b: string; p_a_ahead: number }[]; both_in_q3: { team: string; p: number }[] } | null;
  team_ranges?: { team: string; win_share: number; p10: number; p50: number; p90: number; mean: number }[];
  win_by_grid?: number[]; podium_by_grid?: number[]; scenario?: { clean: number; safety_car: number; attritional: number };
}
export interface GridOptions { race_id: string; live: string[] | null; by_form: string[] }
export interface ServerConfig { cache_ttl: number; live_interval: number; source_priority: string; model_type: string; admin_enabled: boolean; persistent: boolean; choices: Record<string, string[]> }
export interface Standings {
  source: string; as_of_round: number; note: string | null;
  drivers: { pos: number; code: string; name: string; team: Team; cc: string; points: number; wins: number | null; podiums: number | null; history?: { round: number; points: number }[] }[];
  constructors: { pos: number; team: Team; points: number; wins: number | null; history?: { round: number; points: number }[] }[];
}
export interface Side {
  code: string; name: string; team: Team; cc: string;
  season_points?: number | null; points?: number | null; wins: number | null; podiums: number | null;
  avg_quali_season?: number | null; avg_quali?: number | null; avg_points?: number | null;
  win_prob: number; podium_prob: number; points_prob?: number; pole_prob: number; exp_pos: number; dnf?: number;
  ratings?: { pace: number; skill: number; wet: number; rel: number; form: number };
  full_dist?: number[]; pts_dist?: number[]; pts_values?: number[];
  win?: number; podium?: number; history?: { round: number; points: number }[];
}
export interface H2H { race: Race; a: Side; b: Side; record: [number, number] | null; source: string; params?: any; pair?: { p_a_ahead: number; p_b_ahead: number; p_a_ahead_both_finish?: number; p_both_dnf: number; p_both_podium: number } | null }
export interface FantasyEvaluate { race: Race; budget: number; spent: number; remaining: number; valid: boolean; issues: string[]; team: { exp_points: number; sd: number; p10: number; p50: number; p90: number; hist: { bins: number[]; probs: number[] }; percentile_vs_random: number | null; gap_to_optimal: number }; optimal: { picks: string[]; price: number; exp_points: number }; pool: { code: string; name: string; team: Team; cc: string; price: number; exp_points: number; win: number; podium: number; points_prob: number; dnf: number; picked: boolean; optimal: boolean }[]; swaps: { slot: number; out: string; inn: string; delta_points: number; delta_price: number }[]; concentration: { team: string; picks: number; share: number }[]; verdict: { grade: string; label: string; reasons: string[] }; progress?: { round: number; name: string; points: number; optimal_hindsight: number | null; random_mean: number | null }[] }
export interface RecentRace { id: string; name: string; cc: string; winner: string | null; winner_name: string | null; points: number | null; next: boolean }
export interface FantasyPool { race: Race; budget: number; picks: number; pool: { code: string; name: string; team: Team; cc: string; price: number; exp_points: number }[]; optimal: string[]; optimal_points: number }
export interface SearchResult { races: { id: string; name: string; cc: string; circuit: string }[]; drivers: { code: string; name: string; team: Team; cc: string }[]; teams: Team[] }
export interface Meta { season: number; source: "live" | "seed"; as_of_round: number; rounds_done: number; note: string | null; max_sims: number }

import { useApp } from "./store";

const ENV_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

async function req<T>(path: string, init?: RequestInit & { admin?: boolean }): Promise<T> {
  const { s } = useApp.getState();
  const base = (s.apiBase || ENV_BASE).replace(/\/$/, "");
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), s.timeoutMs);
  const t0 = performance.now();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (init?.admin) headers["X-Admin-Token"] = sessionStorage.getItem("f1p26_admin") ?? "";
  try {
    const r = await fetch(base + path, { ...init, headers, signal: ctl.signal });
    if (s.debug) console.debug(`[f1] ${init?.method ?? "GET"} ${path} -> ${r.status} in ${Math.round(performance.now() - t0)} ms`);
    if (!r.ok) {
      const j = await r.json().catch(() => null);
      const d = j?.detail;
      throw new Error(typeof d === "string" ? d : r.statusText || "Request failed");
    }
    return (await r.json()) as T;
  } catch (e) {
    if (s.debug) console.debug(`[f1] ${path} failed`, e);
    if ((e as Error).name === "AbortError") throw new Error(`Request timed out after ${s.timeoutMs} ms`);
    throw e;
  } finally { clearTimeout(timer); }
}

const qs = (o: Record<string, string | null | undefined>) =>
  Object.entries(o).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`).join("&");

export const api = {
  meta: () => req<Meta>("/api/v1/meta"),
  races: () => req<Race[]>("/api/v1/races"),
  nextRace: () => req<Race>("/api/v1/races/next"),
  predict: (p: SimParams) => req<Prediction>("/api/v1/predictions", { method: "POST", body: JSON.stringify(p) }),
  standings: () => req<Standings>("/api/v1/standings"),
  drivers: () => req<{ code: string; name: string; team: Team; cc: string }[]>("/api/v1/drivers"),
  h2h: (a: string, b: string, race_id: string | null, body?: any) => body ? req<H2H>("/api/v1/h2h", { method: "POST", body: JSON.stringify({ a, b, race_id, ...body }) }) : req<H2H>(`/api/v1/h2h?${qs({ a, b, race_id })}`),
  recent: () => req<RecentRace[]>("/api/v1/recent"),
  fantasy: (race_id: string | null) => req<FantasyPool>(`/api/v1/fantasy/pool?${qs({ race_id })}`),
  fantasyEvaluate: (body: { race_id: string | null; sims: number; budget: number; picks: string[] }) => req<FantasyEvaluate>("/api/v1/fantasy/evaluate", { method: "POST", body: JSON.stringify(body) }),
  search: (q: string) => req<SearchResult>(`/api/v1/search?${qs({ q })}`),
  grid: (race_id: string) => req<GridOptions>(`/api/v1/races/${race_id}/grid`),
  config: () => req<ServerConfig>("/api/v1/config"),
  adminVerify: () => req<{ ok: boolean }>("/api/v1/admin/verify", { admin: true }),
  adminSet: (patch: Partial<Pick<ServerConfig, "cache_ttl" | "live_interval" | "source_priority" | "model_type">>) =>
    req<ServerConfig>("/api/v1/admin/config", { method: "PUT", body: JSON.stringify(patch), admin: true }),
};
