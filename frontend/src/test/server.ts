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
    if (p.includes("/api/v1/fantasy/pool") || p.includes("/api/v1/fantasy/evaluate")) return HttpResponse.json(fantasyPool);
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
