/**
 * constructors.js — team cards + power-ranking chart.
 * `teams` (with full stats: championships, wins, podiums, engine, base…)
 * comes server-rendered from get_all_enhanced_teams(); power rankings and
 * current constructor points are fetched live.
 */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);

  async function init() {
    const teams = JSON.parse(document.getElementById("team-data").dataset.teams || "[]");
    const [rankings, standingsPayload] = await Promise.all([
      F1.api("/constructors/api/power-rankings"),
      F1.api("/standings/api/constructor-standings"),
    ]);
    const standings = standingsPayload.data || [];
    const pointsByTeam = {};
    standings.forEach((s) => { pointsByTeam[s.team_id] = s.points; });

    renderChart(rankings, teams);
    renderCards(teams, rankings, pointsByTeam);
  }

  function renderChart(rankings, teams) {
    const byId = {};
    teams.forEach((t) => { byId[t.id] = t; });
    const sorted = rankings.slice().sort((a, b) => a.position - b.position);
    F1Charts.barDistribution(
      $("#chart-power-rankings"),
      sorted.map((r) => (byId[r.team_id] || {}).name || r.team_id),
      sorted.map((r) => r.points),
      sorted.map((r) => (byId[r.team_id] || {}).color || F1.teamColor(r.team_id)),
      {}
    );
  }

  function renderCards(teams, rankings, pointsByTeam) {
    const rankByTeam = {};
    rankings.forEach((r) => { rankByTeam[r.team_id] = r; });

    const sorted = teams.slice().sort((a, b) => (pointsByTeam[b.id] || 0) - (pointsByTeam[a.id] || 0));

    // Update banner with top 3 teams
    updateConstructorBanner(sorted.slice(0, 3));

    $("#team-cards").innerHTML = sorted.map((t) => {
      const rank = rankByTeam[t.id];
      const points = pointsByTeam[t.id] != null ? pointsByTeam[t.id] : "—";
      const drivers = (t.drivers || []).map((d) => `
        <div class="flex items-center justify-between text-sm py-1">
          <span class="flex items-center gap-2 min-w-0">
            <span class="f1-mono font-bold text-sub" style="width:26px">#${d.number}</span>
            <span class="truncate">${F1.escapeHtml(d.name)}</span>
          </span>
          <span class="f1-mono fs-11 text-sub">${d.code}</span>
        </div>`).join("");

      return `<div class="card p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <span class="team-bar" style="height:28px;background:${t.color}"></span>
            <div>
              <div class="f1-display font-bold">${F1.escapeHtml(t.name)}</div>
              <div class="fs-10 text-sub">${F1.escapeHtml(t.base || "")}</div>
            </div>
          </div>
          <div class="text-right">
            <div class="f1-mono text-xl font-bold text-red">${points}</div>
            <div class="fs-9 uppercase tracking-widest text-sub">points</div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 mb-3 fs-11">
          ${stat("Engine", t.engine)}
          ${stat("Chassis", t.chassis)}
          ${stat("Principal", t.team_principal)}
          ${stat("Since", t.first_season)}
          ${stat("Championships", t.championships)}
          ${stat("Wins", t.wins)}
          ${stat("Podiums", t.podiums)}
          ${stat("Poles", t.pole_positions)}
        </div>

        ${rank ? `<div class="fs-11 mb-3 px-2 py-1.5 rounded surface-alt"><span class="text-sub">Form:</span> <span class="font-semibold">${rank.form}</span> <span class="text-sub">&middot; power rank #${rank.position}</span></div>` : ""}

        <div class="pt-2" style="border-top:1px solid var(--border)">
          <div class="fs-10 uppercase tracking-widest font-semibold mb-1 text-sub">Drivers</div>
          ${drivers}
        </div>
      </div>`;
    }).join("");
  }

  function stat(label, value) {
    return `<div><div class="text-sub">${label}</div><div class="font-semibold">${value == null || value === "" ? "—" : F1.escapeHtml(String(value))}</div></div>`;
  }

  function updateConstructorBanner(topTeams) {
    const teamImages = ['car_parts.png', 'pit_stop.jpg', 'circuit1.png', 'circuit2.png', 'f1_cartoon.png', 'f1_simulation.png', 'night_race.png', 'sunset_race.png'];

    topTeams.forEach((team, index) => {
      const badge = document.getElementById(`team-${index + 1}-badge`);
      const image = document.getElementById(`team-${index + 1}-image`);
      const label = document.getElementById(`team-${index + 1}-label`);

      if (badge) badge.textContent = `#${index + 1}`;
      if (image) {
        const imageIndex = Math.abs(team.name.charCodeAt(0) % teamImages.length);
        image.src = `/static/img/${teamImages[imageIndex]}`;
      }
      if (label) label.textContent = team.name;
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
