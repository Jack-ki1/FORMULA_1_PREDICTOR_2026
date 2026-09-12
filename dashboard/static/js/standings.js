/**
 * standings.js — real driver/constructor standings.
 * Handles both API shapes: {data:[...], source:'local'|'simulated'} from the
 * fallback path, and a best-effort parse of the raw Jolpica/Ergast shape if
 * the live path ever returns 'live' (see jolpica_client.py get()).
 */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);

  function normalizeDrivers(payload) {
    if (payload.source === "live" && payload.MRData) {
      try {
        const list = payload.MRData.StandingsTable.StandingsLists[0].DriverStandings;
        return list.map((e) => ({
          position: Number(e.position),
          driver_code: e.Driver.code || (e.Driver.familyName || "").slice(0, 3).toUpperCase(),
          points: Number(e.points),
          team: (e.Constructors && e.Constructors[0] && e.Constructors[0].constructorId) || "",
        }));
      } catch (e) { /* fall through */ }
    }
    return payload.data || [];
  }
  function normalizeConstructors(payload) {
    if (payload.source === "live" && payload.MRData) {
      try {
        const list = payload.MRData.StandingsTable.StandingsLists[0].ConstructorStandings;
        return list.map((e) => ({ position: Number(e.position), team_id: e.Constructor.constructorId, points: Number(e.points) }));
      } catch (e) { /* fall through */ }
    }
    return payload.data || [];
  }

  async function init() {
    const [driverPayload, constructorPayload, driverMap] = await Promise.all([
      F1.api("/standings/api/driver-standings"),
      F1.api("/standings/api/constructor-standings"),
      F1.getDriverMap(),
    ]);

    const drivers = normalizeDrivers(driverPayload);
    const constructors = normalizeConstructors(constructorPayload);

    const sourceLabel = { live: "Live · Jolpica API", local: "Season snapshot", simulated: "Simulated fallback" }[driverPayload.source] || driverPayload.source || "";
    $("#source-badge").textContent = sourceLabel;

    renderDriverTable(drivers, driverMap);
    renderConstructorTable(constructors);
    renderDriverChart(drivers, driverMap);
    renderShareChart(constructors);
  }

  function teamName(id) {
    const names = { mclaren: "McLaren", ferrari: "Ferrari", redbull: "Red Bull Racing", mercedes: "Mercedes", astonmartin: "Aston Martin", williams: "Williams", audi: "Audi", alpine: "Alpine", haas: "Haas", racingbulls: "Racing Bulls", cadillac: "Cadillac" };
    return names[id] || id;
  }

  function renderDriverTable(drivers, driverMap) {
    const head = `<div class="fs-10 uppercase tracking-widest font-bold px-4 py-2 surface-alt text-sub" style="display:grid;grid-template-columns:36px 1fr 90px 120px;gap:8px">
      <span>#</span><span>Driver</span><span>Points</span><span>Team</span>
    </div>`;
    const rows = drivers.map((d) => {
      const info = driverMap[d.driver_code] || {};
      const color = info.team_color || F1.teamColor(d.team);
      return `<div style="display:grid;grid-template-columns:36px 1fr 90px 120px;gap:8px;border-top:1px solid var(--border)" class="items-center px-4 py-2.5 text-sm">
        <span class="f1-mono font-bold">${d.position}</span>
        <span class="flex items-center gap-2 min-w-0">
          <span class="team-bar" style="background:${color}"></span>
          <span class="min-w-0">
            <div class="f1-display font-bold truncate">${F1.escapeHtml(info.name || d.driver_code)}</div>
            <div class="fs-10 text-sub truncate">${F1.escapeHtml(info.team_name || teamName(d.team))}</div>
          </span>
        </span>
        <span class="f1-mono font-bold">${d.points}</span>
        <span class="fs-11 text-sub">${F1.escapeHtml(info.team_name || teamName(d.team))}</span>
      </div>`;
    }).join("");
    $("#driver-table-wrap").innerHTML = `<div class="f1-table" style="min-width:520px">${head}${rows}</div>`;
  }

  function renderConstructorTable(constructors) {
    const head = `<div class="fs-10 uppercase tracking-widest font-bold px-4 py-2 surface-alt text-sub" style="display:grid;grid-template-columns:36px 1fr 90px;gap:8px">
      <span>#</span><span>Constructor</span><span>Points</span>
    </div>`;
    const rows = constructors.map((t) => `<div style="display:grid;grid-template-columns:36px 1fr 90px;gap:8px;border-top:1px solid var(--border)" class="items-center px-4 py-2.5 text-sm">
      <span class="f1-mono font-bold">${t.position}</span>
      <span class="flex items-center gap-2">
        <span class="team-bar" style="background:${F1.teamColor(t.team_id)}"></span>
        <span class="f1-display font-bold">${F1.escapeHtml(teamName(t.team_id))}</span>
      </span>
      <span class="f1-mono font-bold">${t.points}</span>
    </div>`).join("");
    $("#constructor-table-wrap").innerHTML = `<div class="f1-table" style="min-width:420px">${head}${rows}</div>`;
  }

  function renderDriverChart(drivers, driverMap) {
    const top = drivers.slice(0, 12);
    F1Charts.barDistribution(
      $("#chart-driver-points"),
      top.map((d) => d.driver_code),
      top.map((d) => d.points),
      top.map((d) => (driverMap[d.driver_code] || {}).team_color || F1.teamColor(d.team)),
      {}
    );
  }

  function renderShareChart(constructors) {
    F1Charts.doughnut(
      $("#chart-points-share"),
      constructors.map((t) => teamName(t.team_id)),
      constructors.map((t) => t.points),
      constructors.map((t) => F1.teamColor(t.team_id))
    );
  }

  document.addEventListener("DOMContentLoaded", init);
})();
