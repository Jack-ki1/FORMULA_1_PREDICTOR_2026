import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import config from "./fixtures/config.json";
import drivers from "./fixtures/drivers.json";
import fantasyPool from "./fixtures/fantasy_pool.json";
import grid19 from "./fixtures/grid_19.json";
import h2h from "./fixtures/h2h.json";
import meta from "./fixtures/meta.json";
import nextRace from "./fixtures/next_race.json";
import prediction from "./fixtures/prediction.json";
import races from "./fixtures/races.json";
import recent from "./fixtures/recent.json";
import search from "./fixtures/search.json";
import standings from "./fixtures/standings.json";

export const handlers = [
  http.all("*", async ({ request }) => {
    const url = new URL(request.url);
    const p = url.pathname;
    if (p.endsWith("/health")) return HttpResponse.json({ status: "ok" });
    if (p.endsWith("/api/v1/meta")) return HttpResponse.json(meta);
    if (p.endsWith("/api/v1/races")) return HttpResponse.json(races);
    if (p.endsWith("/api/v1/races/next")) return HttpResponse.json(nextRace);
    if (p.includes("/api/v1/races/") && p.endsWith("/grid")) return HttpResponse.json(grid19);
    if (p.endsWith("/api/v1/standings")) return HttpResponse.json(standings);
    if (p.endsWith("/api/v1/drivers")) return HttpResponse.json(drivers);
    if (p.endsWith("/api/v1/recent")) return HttpResponse.json(recent);
    if (p.includes("/api/v1/search")) return HttpResponse.json(search);
    if (p.endsWith("/api/v1/config")) return HttpResponse.json(config);
    if (p.includes("/api/v1/h2h")) return HttpResponse.json(h2h);
    if (p.includes("/api/v1/fantasy/pool")) return HttpResponse.json(fantasyPool);
    if (p.includes("/api/v1/fantasy/evaluate")) {
      const body = (await request.clone().json().catch(() => ({}))) as Record<string, unknown>;
      const picks = Array.isArray(body.picks) ? body.picks : [];
      return HttpResponse.json({
        race: { id: "19", name: "Abu Dhabi Grand Prix", country: "UAE", cc: "ae", date_start: "2026-12-06", date_end: "2026-12-08", start_utc: "2026-12-08T13:00:00Z", winner: null, status: "upcoming", circuit: { id: "yas_marina", name: "Yas Marina Circuit", locality: "Abu Dhabi", length_km: 5.281, turns: 16, lap_record: "1:39.283", drs: 3, laps: 55, overtaking: 6, tyre_wear: 6, sc_prob: 0.3, lat: 24.4556, lon: 54.6031 }, sprint: false, sessions: [], labels: { practice_day: "Friday", quali_day: "Saturday", race_day: "Sunday" } },
        budget: 100, spent: 85.5, remaining: 14.5, valid: picks.length === 5, issues: picks.length === 5 ? [] : [`Pick exactly 5 drivers (you have ${picks.length})`],
        team: { exp_points: 68.5, sd: 12.3, p10: 52, p50: 68, p90: 85, hist: { bins: [40, 50, 60, 70, 80, 90], probs: [0.05, 0.15, 0.25, 0.3, 0.15, 0.1] }, percentile_vs_random: 85, gap_to_optimal: 3.2 },
        optimal: { picks: ["VER", "NOR", "LEC", "HAM", "RUS"], price: 95.0, exp_points: 72.1 },
        pool: [
          { code: "VER", name: "Max Verstappen", team: { id: "red_bull", name: "Red Bull Racing", color: "#0600ef" }, cc: "nl", price: 24.0, exp_points: 18.5, win: 0.35, podium: 0.72, points_prob: 0.95, dnf: 0.05, picked: picks.includes("VER"), optimal: true },
          { code: "NOR", name: "Lando Norris", team: { id: "mclaren", name: "McLaren", color: "#ff8700" }, cc: "gb", price: 22.0, exp_points: 16.2, win: 0.22, podium: 0.65, points_prob: 0.92, dnf: 0.08, picked: picks.includes("NOR"), optimal: true },
          { code: "LEC", name: "Charles Leclerc", team: { id: "ferrari", name: "Ferrari", color: "#dc0000" }, cc: "mc", price: 20.0, exp_points: 14.8, win: 0.15, podium: 0.58, points_prob: 0.88, dnf: 0.1, picked: picks.includes("LEC"), optimal: true },
          { code: "HAM", name: "Lewis Hamilton", team: { id: "ferrari", name: "Ferrari", color: "#dc0000" }, cc: "gb", price: 19.5, exp_points: 14.2, win: 0.12, podium: 0.55, points_prob: 0.86, dnf: 0.08, picked: picks.includes("HAM"), optimal: true },
          { code: "RUS", name: "George Russell", team: { id: "mercedes", name: "Mercedes", color: "#00d2be" }, cc: "gb", price: 18.0, exp_points: 13.5, win: 0.08, podium: 0.48, points_prob: 0.82, dnf: 0.06, picked: picks.includes("RUS"), optimal: true },
          { code: "PIA", name: "Oscar Piastri", team: { id: "mclaren", name: "McLaren", color: "#ff8700" }, cc: "au", price: 17.0, exp_points: 12.8, win: 0.1, podium: 0.5, points_prob: 0.8, dnf: 0.07, picked: false, optimal: false },
        ],
        swaps: [{ slot: 0, out: "VER", inn: "PIA", delta_points: -2.1, delta_price: -7.0 }],
        concentration: [{ team: "Ferrari", picks: 2, share: 0.4 }, { team: "McLaren", picks: 1, share: 0.2 }],
        verdict: { grade: "A", label: "Elite", reasons: ["Best swap: VER → PIA (-2.1 pts)"] },
        progress: [{ round: 1, name: "Round 1", points: 25, optimal_hindsight: 28, random_mean: 18 }],
      });
    }
    if (p.endsWith("/api/v1/predictions")) {
      const resp = JSON.parse(JSON.stringify(prediction));
      const body = (await request.clone().json().catch(() => ({}))) as Record<string, unknown>;
      if (body.grid && Array.isArray(body.grid) && body.grid.filter(Boolean).length > 0) {
        resp.grid_source = "manual";
        resp.grid_locked = body.grid.filter(Boolean).length;
      }
      if (typeof body.session === "string") {
        resp.params.session = body.session;
      }
      return HttpResponse.json(resp);
    }
    return undefined;
  }),
];

export const server = setupServer(...handlers);
