const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* response wasn't JSON — keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---- Types (mirrors apps/api's Pydantic response models) ----

export interface Race {
  id: string;
  round: number;
  name: string;
  circuit: string;
  location: string;
  country: string;
  flag: string;
  date: string;
  status: "completed" | "upcoming" | "cancelled";
  sprint: boolean;
}

export interface PredictionResponse {
  race_id: string;
  session_type: string;
  status?: string;
  source: string;
  generated_at?: string;
  model_version?: string;
  winner_probabilities?: Record<string, number>;
  confidence_intervals?: Record<string, { lower: number; upper: number }>;
  predictions?: Record<
    string,
    { predictions: { driver_code: string; probability: number; percentage: number }[] }
  >;
  grid_positions?: Record<string, number>;
}

export interface DriverInfo {
  code: string;
  name: string;
  number: number;
  strength: number;
  reliability: number;
  wet_skill: number;
  team_id: string;
  team_name: string;
  team_color: string;
}

export interface H2HResult {
  driver_a: DriverInfo;
  driver_b: DriverInfo;
  win_probability: number;
  reverse_probability: number;
}

export interface TeamInfo {
  id: string;
  name: string;
  color: string;
  [key: string]: unknown;
}

export interface FeatureWeights {
  chaos_level: number;
  wet_influence: number;
  reliability_influence: number;
  strategy_aggressiveness: number;
  grid_weight: number;
  scope: "user" | "default";
}

export interface Pick {
  id: number;
  race_id: string;
  session: string;
  target: string;
  driver_id: string;
  status: string;
  points: number;
}

export interface LeaderboardRow {
  rank: number;
  display_name: string;
  avatar_url: string | null;
  total_score: number;
  picks_made: number;
  picks_resolved: number;
}

export interface StatusResponse {
  data_last_synced_at: string | null;
  minutes_since_last_sync: number | null;
  model_runs: Record<
    string,
    { accuracy: number; baseline: number; model_version: string | null; evaluated_at: string | null }
  >;
  checked_at: string;
}

// ---- Endpoints ----

export const api = {
  races: () => request<Race[]>("/races"),
  raceResult: (raceId: string) => request<Race & Record<string, unknown>>(`/race-result/${raceId}`),
  predictions: (raceId: string, sessionType: string = "race") =>
    request<PredictionResponse>(`/predictions/${raceId}?session_type=${sessionType}`),
  recompute: (
    raceId: string,
    body: {
      session_type?: string;
      weather?: string;
      grid_positions?: Record<string, number>;
      feature_weights?: Partial<FeatureWeights>;
      simulation_count?: number;
    }
  ) =>
    request<PredictionResponse>(`/predictions/${raceId}/recompute`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  standingsDrivers: () => request<{ data: unknown[]; source: string }>("/standings/drivers"),
  standingsConstructors: () => request<{ data: unknown[]; source: string }>("/standings/constructors"),
  h2hDrivers: () => request<DriverInfo[]>("/h2h/drivers"),
  h2hCompare: (driverA: string, driverB: string) =>
    request<H2HResult>("/h2h/compare", { method: "POST", body: JSON.stringify({ driver_a: driverA, driver_b: driverB }) }),
  teams: () => request<TeamInfo[]>("/constructors/teams"),
  powerRankings: () => request<unknown[]>("/constructors/power-rankings"),
  status: () => request<StatusResponse>("/status"),
  accuracy: () => request<Record<string, unknown>>("/settings/accuracy"),
  featureWeights: (token?: string) => request<FeatureWeights>("/settings/feature-weights", {}, token),
  saveFeatureWeights: (weights: Omit<FeatureWeights, "scope">, token?: string) =>
    request<{ status: string }>(
      "/settings/feature-weights",
      { method: "POST", body: JSON.stringify(weights) },
      token
    ),
  myPicks: (token: string, raceId?: string) =>
    request<Pick[]>(`/picks${raceId ? `?race_id=${raceId}` : ""}`, {}, token),
  submitPick: (
    token: string,
    body: { race_id: string; session: string; target: string; driver_id: string }
  ) => request<Pick>("/picks", { method: "POST", body: JSON.stringify(body) }, token),
  leaderboard: () => request<LeaderboardRow[]>("/leaderboard"),
};
