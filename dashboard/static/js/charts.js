/**
 * charts.js — Chart.js factories, themed from F1.palette().
 * Every chart registers itself so it can be destroyed/rebuilt on theme
 * change (dark/light toggle) without leaking canvases.
 */
(function () {
  "use strict";
  if (typeof Chart === "undefined") { window.F1Charts = { }; return; }

  Chart.defaults.font.family = "'Inter', ui-sans-serif, system-ui, sans-serif";
  Chart.defaults.font.size = 11;

  const registry = [];
  function track(chart, rebuild) { registry.push({ chart, rebuild }); return chart; }

  document.addEventListener("f1:theme-change", function () {
    registry.forEach((entry) => { try { entry.rebuild(); } catch (e) {} });
  });

  function baseGrid() {
    const p = F1.palette();
    return {
      color: p.gridline,
      display: true,
      drawTicks: false,
    };
  }
  function baseTicks() {
    const p = F1.palette();
    return { color: p.sub, font: { size: 10 } };
  }

  const F1Charts = {};

  // ---- Horizontal probability bar (ResultsHero-style distribution) ----
  F1Charts.barDistribution = function (canvas, labels, values, colors, opts) {
    opts = opts || {};
    function build() {
      const p = F1.palette();
      return new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: colors || p.red,
            borderRadius: 4,
            maxBarThickness: 22,
          }],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => (opts.tooltipSuffix ? ctx.parsed.x.toFixed(1) + opts.tooltipSuffix : ctx.parsed.x),
              },
            },
          },
          scales: {
            x: { grid: baseGrid(), ticks: baseTicks(), beginAtZero: true },
            y: { grid: { display: false }, ticks: { color: p.text, font: { size: 11, weight: "600" } } },
          },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  // ---- Vertical bar (accuracy, points, power rankings) ----
  F1Charts.barVertical = function (canvas, labels, datasets, opts) {
    opts = opts || {};
    function build() {
      const p = F1.palette();
      return new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: !!opts.legend, labels: { color: p.text } } },
          scales: {
            x: { grid: { display: false }, ticks: baseTicks() },
            y: { grid: baseGrid(), ticks: baseTicks(), beginAtZero: true, ...(opts.yMax ? { max: opts.yMax } : {}) },
          },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  // ---- Doughnut (DNF risk split, points share) ----
  F1Charts.doughnut = function (canvas, labels, values, colors) {
    function build() {
      const p = F1.palette();
      return new Chart(canvas.getContext("2d"), {
        type: "doughnut",
        data: { labels, datasets: [{ data: values, backgroundColor: colors, borderColor: p.surface, borderWidth: 2 }] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "68%",
          plugins: { legend: { position: "bottom", labels: { color: p.sub, boxWidth: 10, font: { size: 10 } } } },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  // ---- Radial gauge (single value 0-100, e.g. Model Confidence) ----
  F1Charts.gauge = function (canvas, value, opts) {
    opts = opts || {};
    function build() {
      const p = F1.palette();
      const color = value >= 70 ? p.green : value >= 45 ? p.amber : p.red;
      return new Chart(canvas.getContext("2d"), {
        type: "doughnut",
        data: {
          datasets: [{
            data: [value, 100 - value],
            backgroundColor: [color, p.surfaceAlt],
            borderWidth: 0,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "78%",
          circumference: 270,
          rotation: 225,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  // ---- Line chart (pace evolution, lap trend, confidence over sims) ----
  F1Charts.line = function (canvas, labels, datasets, opts) {
    opts = opts || {};
    function build() {
      const p = F1.palette();
      return new Chart(canvas.getContext("2d"), {
        type: "line",
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: { legend: { display: !!opts.legend, position: "bottom", labels: { color: p.sub, boxWidth: 10, font: { size: 10 } } } },
          scales: {
            x: { grid: { display: false }, ticks: baseTicks() },
            y: { grid: baseGrid(), ticks: baseTicks(), reverse: !!opts.reverseY },
          },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  // ---- Radar (H2H attribute comparison) ----
  F1Charts.radar = function (canvas, labels, datasets) {
    function build() {
      const p = F1.palette();
      return new Chart(canvas.getContext("2d"), {
        type: "radar",
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: "bottom", labels: { color: p.sub, boxWidth: 10, font: { size: 10 } } } },
          scales: {
            r: {
              angleLines: { color: p.gridline },
              grid: { color: p.gridline },
              pointLabels: { color: p.sub, font: { size: 10 } },
              ticks: { display: false, backdropColor: "transparent" },
              suggestedMin: 0, suggestedMax: 100,
            },
          },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  // ---- Simple bar chart (vertical) ----
  F1Charts.barChart = function (canvas, labels, values, colors, opts) {
    opts = opts || {};
    function build() {
      const p = F1.palette();
      
      // Handle multi-dataset case
      if (Array.isArray(values[0])) {
        const datasets = values.map((dataset, index) => ({
          label: labels[index],
          data: dataset,
          backgroundColor: colors[index] || p.palette[index % p.palette.length],
          borderRadius: 4,
        }));
        
        return new Chart(canvas.getContext("2d"), {
          type: "bar",
          data: {
            labels: opts.labels || ['Data 1', 'Data 2', 'Data 3'],
            datasets: datasets,
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
              legend: { display: true, position: "bottom", labels: { color: p.sub, boxWidth: 10, font: { size: 10 } } },
              title: { display: !!opts.title, text: opts.title, color: p.text }
            },
            scales: {
              x: { grid: { display: false }, ticks: baseTicks() },
              y: { grid: baseGrid(), ticks: baseTicks(), beginAtZero: true },
            },
          },
        });
      }
      
      // Single dataset case
      return new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: colors || p.red,
            borderRadius: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { 
            legend: { display: false },
            title: { display: !!opts.title, text: opts.title, color: p.text }
          },
          scales: {
            x: { grid: { display: false }, ticks: baseTicks() },
            y: { grid: baseGrid(), ticks: baseTicks(), beginAtZero: true },
          },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  // ---- Simple line chart ----
  F1Charts.lineChart = function (canvas, labels, datasets, opts) {
    opts = opts || {};
    function build() {
      const p = F1.palette();
      const formattedDatasets = Object.entries(datasets).map(([label, data], index) => ({
        label,
        data,
        borderColor: p.palette[index % p.palette.length],
        backgroundColor: p.palette[index % p.palette.length] + '20',
        tension: 0.4,
        fill: false,
      }));
      
      return new Chart(canvas.getContext("2d"), {
        type: "line",
        data: { labels, datasets: formattedDatasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: { 
            legend: { display: true, position: "bottom", labels: { color: p.sub, boxWidth: 10, font: { size: 10 } } },
            title: { display: !!opts.title, text: opts.title, color: p.text }
          },
          scales: {
            x: { grid: { display: false }, ticks: baseTicks() },
            y: { grid: baseGrid(), ticks: baseTicks(), beginAtZero: true },
          },
        },
      });
    }
    let chart = build();
    return track(chart, function () { chart.destroy(); chart = build(); });
  };

  window.F1Charts = F1Charts;
})();
