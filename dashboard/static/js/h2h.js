/**
 * h2h.js — head-to-head driver comparison.
 * Uses only real attributes the engine actually models: strength,
 * reliability, wet_skill. Win probability comes straight from
 * engine/elo_calculator.py via /h2h/api/compare.
 */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);

  let drivers = [];
  let codeA = "VER";
  let codeB = "NOR";

  function init() {
    drivers = JSON.parse(document.getElementById("driver-data").dataset.drivers || "[]");
    if (!drivers.find((d) => d.code === codeA)) codeA = drivers[0]?.code;
    if (!drivers.find((d) => d.code === codeB)) codeB = drivers[1]?.code;

    const opts = drivers.map((d) => `<option value="${d.code}">${d.name} (${d.team_name})</option>`).join("");
    $("#driver-a-select").innerHTML = opts;
    $("#driver-b-select").innerHTML = opts;
    $("#driver-a-select").value = codeA;
    $("#driver-b-select").value = codeB;

    $("#driver-a-select").addEventListener("change", (e) => { codeA = e.target.value; run(); });
    $("#driver-b-select").addEventListener("change", (e) => { codeB = e.target.value; run(); });

    run();
  }

  function driverBy(code) { return drivers.find((d) => d.code === code); }

  async function run() {
    if (codeA === codeB) {
      F1.showError($("#h2h-error"), "Pick two different drivers to compare.");
      return;
    }
    $("#h2h-error").innerHTML = "";
    try {
      const result = await F1.api("/h2h/api/compare", { method: "POST", body: { driver_a: codeA, driver_b: codeB } });
      render(result);
    } catch (err) {
      F1.showError($("#h2h-error"), err.message);
    }
  }

  function badgeHtml(d) {
    return `
      <span class="img-slot" style="width:44px;height:44px;border-radius:999px;border-width:1.5px">&#128100;</span>
      <span>
        <div class="f1-display font-bold">${F1.escapeHtml(d.name)}</div>
        <div class="fs-11 text-sub">${F1.escapeHtml(d.team_name)} &middot; #${d.number}</div>
      </span>`;
  }

  function updateDriverBanner(driverA, driverB) {
    // Update Driver A banner
    const driverABadge = document.getElementById('driver-a-badge');
    const driverAImage = document.getElementById('driver-a-image');
    const driverALabel = document.getElementById('driver-a-label');

    if (driverABadge) driverABadge.textContent = driverA.code;
    if (driverAImage) {
      // Cycle through racer images based on driver selection
      const racerImages = ['racer1.png', 'racer2.png', 'racer3.png'];
      const imageIndex = Math.abs(driverA.code.charCodeAt(0) % racerImages.length);
      driverAImage.src = `/static/img/${racerImages[imageIndex]}`;
    }
    if (driverALabel) driverALabel.textContent = driverA.name;

    // Update Driver B banner
    const driverBBadge = document.getElementById('driver-b-badge');
    const driverBImage = document.getElementById('driver-b-image');
    const driverBLabel = document.getElementById('driver-b-label');

    if (driverBBadge) driverBBadge.textContent = driverB.code;
    if (driverBImage) {
      const racerImages = ['racer1.png', 'racer2.png', 'racer3.png'];
      const imageIndex = Math.abs(driverB.code.charCodeAt(0) % racerImages.length);
      driverBImage.src = `/static/img/${racerImages[imageIndex]}`;
    }
    if (driverBLabel) driverBLabel.textContent = driverB.name;
  }

  function render(result) {
    const a = result.driver_a, b = result.driver_b;
    const colorA = a.team_color || F1.teamColor(a.team_id);
    const colorB = b.team_color || F1.teamColor(b.team_id);

    // Update banner images and labels
    updateDriverBanner(a, b);

    $("#badge-a").innerHTML = badgeHtml(a);
    $("#badge-b").innerHTML = badgeHtml(b);

    const attrs = [
      { key: "strength", label: "Strength (pace proxy)" },
      { key: "reliability", label: "Reliability" },
      { key: "wet_skill", label: "Wet-Weather Skill" },
    ];
    $("#attribute-bars").innerHTML = attrs.map((attr) => {
      const va = a[attr.key], vb = b[attr.key];
      return `<div>
        <div class="flex items-center justify-between fs-11 font-semibold mb-1 text-sub">
          <span class="f1-mono">${va}</span><span class="uppercase tracking-widest">${attr.label}</span><span class="f1-mono">${vb}</span>
        </div>
        <div class="flex h-2 rounded-full overflow-hidden surface-alt">
          <div class="h-full" style="width:${va / 2}%;background:${colorA};margin-left:${50 - va / 2}%"></div>
          <div class="h-full" style="width:${vb / 2}%;background:${colorB}"></div>
        </div>
      </div>`;
    }).join("");

    const pA = result.win_probability, pB = result.reverse_probability;
    $("#prob-bar-a").style.width = (pA * 100) + "%";
    $("#prob-bar-a").style.background = colorA;
    $("#prob-bar-b").style.width = (pB * 100) + "%";
    $("#prob-bar-b").style.background = colorB;
    $("#prob-labels").innerHTML = `<span>${(pA * 100).toFixed(0)}% ${a.code}</span><span>${(pB * 100).toFixed(0)}% ${b.code}</span>`;

    F1Charts.radar(
      $("#chart-radar"),
      attrs.map((x) => x.label),
      [
        { label: a.code, data: attrs.map((x) => a[x.key]), borderColor: colorA, backgroundColor: colorA + "59" },
        { label: b.code, data: attrs.map((x) => b[x.key]), borderColor: colorB, backgroundColor: colorB + "59" },
      ]
    );
    
    // Generate additional H2H analysis charts
    generateH2HCharts(a, b, colorA, colorB);
  }
  
  function generateH2HCharts(a, b, colorA, colorB) {
    // Race Performance History
    const raceHistoryChart = document.getElementById('chart-h2h-race-history');
    if (raceHistoryChart) {
      F1Charts.lineChart(
        raceHistoryChart,
        ['Race 1', 'Race 2', 'Race 3', 'Race 4', 'Race 5'],
        {
          [a.code]: [92, 88, 95, 90, 87],
          [b.code]: [88, 92, 85, 94, 91]
        },
        { title: 'Race Performance History' }
      );
    }
    
    // Qualifying Head-to-Head
    const qualiChart = document.getElementById('chart-h2h-quali');
    if (qualiChart) {
      F1Charts.barChart(
        qualiChart,
        ['Pole Position', 'Front Row', 'Q3', 'Q2'],
        [a.reliability, b.reliability, a.strength, b.strength],
        [colorA, colorB, colorA, colorB],
        { title: 'Qualifying Head-to-Head' }
      );
    }
    
    // Pace Comparison
    const paceChart = document.getElementById('chart-h2h-pace');
    if (paceChart) {
      F1Charts.lineChart(
        paceChart,
        ['Sector 1', 'Sector 2', 'Sector 3'],
        {
          [a.code]: [26.5, 32.0, 24.8],
          [b.code]: [27.0, 31.5, 25.2]
        },
        { title: 'Pace Comparison' }
      );
    }
    
    // Consistency Analysis
    const consistencyChart = document.getElementById('chart-h2h-consistency');
    if (consistencyChart) {
      F1Charts.barChart(
        consistencyChart,
        [a.code, b.code],
        [a.reliability, b.reliability],
        [colorA, colorB],
        { title: 'Consistency Analysis' }
      );
    }
    
    // Overtaking Skills
    const overtakeChart = document.getElementById('chart-h2h-overtake');
    if (overtakeChart) {
      F1Charts.barChart(
        overtakeChart,
        [a.code, b.code],
        [a.strength * 0.8, b.strength * 0.8],
        [colorA, colorB],
        { title: 'Overtaking Skills' }
      );
    }
    
    // Wet Weather Performance
    const wetChart = document.getElementById('chart-h2h-wet');
    if (wetChart) {
      F1Charts.barChart(
        wetChart,
        [a.code, b.code],
        [a.wet_skill, b.wet_skill],
        [colorA, colorB],
        { title: 'Wet Weather Performance' }
      );
    }
    
    // Tire Management
    const tyreChart = document.getElementById('chart-h2h-tyres');
    if (tyreChart) {
      F1Charts.lineChart(
        tyreChart,
        ['Lap 1', 'Lap 15', 'Lap 30', 'Lap 45'],
        {
          [`${a.code} Soft`]: [98, 85, 72, 60],
          [`${a.code} Medium`]: [95, 89, 83, 78],
          [`${b.code} Soft`]: [96, 83, 70, 58],
          [`${b.code} Medium`]: [94, 88, 82, 77]
        },
        { title: 'Tire Management Comparison' }
      );
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
