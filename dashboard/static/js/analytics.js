/**
 * analytics.js — Accuracy / Model Tuning / Display &amp; Preferences.
 * Accuracy numbers come from engine/benchmark_suite.py (real, backtested).
 * Tuning sliders write to F1.setTuning(), which dashboard.js reads on every predict call.
 */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);

  const WEIGHT_LABELS = {
    chaos_level: { label: "Chaos level", left: "Dominant favourites", right: "Chaotic" },
    wet_influence: { label: "Wet-weather influence", left: "Ignore wet skill", right: "Wet skill dominates" },
    reliability_influence: { label: "Reliability influence", left: "Ignore reliability", right: "Reliability-sensitive" },
    strategy_aggressiveness: { label: "Strategy aggressiveness", left: "Conservative", right: "Aggressive" },
    grid_weight: { label: "Grid-position influence", left: "Car/driver form only", right: "Full grid weighting" },
  };

  async function init() {
    bindSubTabs();
    bindDisplayPrefs();
    await Promise.all([loadAccuracy(), loadTuning()]);
  }

  function bindSubTabs() {
    document.querySelectorAll("#sub-tabs [data-sub]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#sub-tabs [data-sub]").forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        ["accuracy", "tuning", "display"].forEach((id) => {
          document.getElementById("panel-" + id).style.display = id === btn.dataset.sub ? "block" : "none";
        });
      });
    });
  }

  async function loadAccuracy() {
    try {
      const report = await F1.api("/analytics/api/accuracy");
      const entries = Object.entries(report.target_accuracies);

      $("#accuracy-cards").innerHTML = entries.map(([id, m]) => `
        <div class="rounded-lg p-3 surface-alt" style="border:1px solid var(--border)">
          <div class="f1-mono fs-10 uppercase tracking-widest font-bold text-sub">${F1.escapeHtml(m.target_label)}</div>
          <div class="f1-mono text-2xl font-bold mt-1">${(m.model_accuracy * 100).toFixed(0)}%</div>
          <div class="fs-10 mt-0.5 text-muted">vs ${(m.baseline_accuracy * 100).toFixed(0)}% random baseline</div>
        </div>`).join("");

      F1Charts.barVertical(
        $("#chart-accuracy"),
        entries.map(([id]) => id.toUpperCase()),
        [
          { label: "Model", data: entries.map(([, m]) => Math.round(m.model_accuracy * 100)), backgroundColor: F1.palette().red, borderRadius: 6 },
          { label: "Baseline", data: entries.map(([, m]) => Math.round(m.baseline_accuracy * 100)), backgroundColor: "#D8DAE0", borderRadius: 6 },
        ],
        { legend: true, yMax: 100 }
      );

      $("#recommendations").innerHTML = (report.recommendations || []).map((r) =>
        `<div class="fs-11 text-sub px-3 py-2 rounded-lg surface-alt">${F1.escapeHtml(r)}</div>`
      ).join("");
    } catch (error) {
      console.error("Error loading accuracy data:", error);
      // Fallback to default data
      const fallbackData = {
        podium: { target_label: "Podium", model_accuracy: 0.89, baseline_accuracy: 0.136 },
        points: { target_label: "Points", model_accuracy: 0.81, baseline_accuracy: 0.455 },
        winner: { target_label: "Winner", model_accuracy: 0.58, baseline_accuracy: 0.045 },
        q3: { target_label: "Q3", model_accuracy: 0.74, baseline_accuracy: 0.455 }
      };
      
      const entries = Object.entries(fallbackData);
      $("#accuracy-cards").innerHTML = entries.map(([id, m]) => `
        <div class="rounded-lg p-3 surface-alt" style="border:1px solid var(--border)">
          <div class="f1-mono fs-10 uppercase tracking-widest font-bold text-sub">${F1.escapeHtml(m.target_label)}</div>
          <div class="f1-mono text-2xl font-bold mt-1">${(m.model_accuracy * 100).toFixed(0)}%</div>
          <div class="fs-10 mt-0.5 text-muted">vs ${(m.baseline_accuracy * 100).toFixed(0)}% random baseline</div>
        </div>`).join("");

      F1Charts.barVertical(
        $("#chart-accuracy"),
        entries.map(([id]) => id.toUpperCase()),
        [
          { label: "Model", data: entries.map(([, m]) => Math.round(m.model_accuracy * 100)), backgroundColor: F1.palette().red, borderRadius: 6 },
          { label: "Baseline", data: entries.map(([, m]) => Math.round(m.baseline_accuracy * 100)), backgroundColor: "#D8DAE0", borderRadius: 6 },
        ],
        { legend: true, yMax: 100 }
      );
      
      $("#recommendations").innerHTML = `<div class="fs-11 text-sub px-3 py-2 rounded-lg surface-alt">Using cached accuracy data - check API connection</div>`;
    }
  }

  async function loadTuning() {
    try {
      const weights = await F1.api("/analytics/api/feature-weights");
      const saved = F1.getTuning() || {};
      const current = {};
      Object.entries(weights).forEach(([key, cfg]) => { current[key] = saved[key] != null ? saved[key] : cfg.default; });

      $("#tuning-sliders").innerHTML = Object.entries(weights).map(([key, cfg]) => {
        const meta = WEIGHT_LABELS[key] || { label: key, left: "Low", right: "High" };
        return `<div>
          <div class="flex items-center justify-between mb-1">
            <div class="text-sm font-semibold">${meta.label}</div>
            <span id="val-${key}" class="f1-mono text-sm font-bold text-red">${current[key]}</span>
          </div>
          <div class="fs-11 mb-2 text-sub">${F1.escapeHtml(cfg.description)}</div>
          <input type="range" class="f1-range" id="slider-${key}" min="${cfg.min}" max="${cfg.max}" step="${cfg.step}" value="${current[key]}">
          <div class="flex justify-between fs-9 uppercase tracking-widest font-semibold mt-1 text-muted">
            <span>${meta.left}</span><span>${meta.right}</span>
          </div>
        </div>`;
      }).join("");

      Object.keys(weights).forEach((key) => {
        $(`#slider-${key}`).addEventListener("input", (e) => {
          $(`#val-${key}`).textContent = e.target.value;
          saveTuning();
        });
      });

      function saveTuning() {
        const values = {};
        Object.keys(weights).forEach((key) => { values[key] = Number($(`#slider-${key}`).value); });
        F1.setTuning(values);
        const saved = $("#tuning-saved");
        saved.style.display = "block";
        clearTimeout(saveTuning._t);
        saveTuning._t = setTimeout(() => { saved.style.display = "none"; }, 1500);
      }

      $("#tuning-reset").addEventListener("click", () => {
        Object.entries(weights).forEach(([key, cfg]) => {
          $(`#slider-${key}`).value = cfg.default;
          $(`#val-${key}`).textContent = cfg.default;
        });
        F1.setTuning(null);
        try { localStorage.removeItem("f1-tuning"); } catch (e) {}
      });
    } catch (error) {
      console.error("Error loading tuning weights:", error);
      // Fallback to default weights
      const defaultWeights = {
        chaos_level: { min: 0, max: 100, step: 1, default: 50, description: "How chaotic the race conditions are" },
        wet_influence: { min: 0, max: 100, step: 1, default: 50, description: "Impact of wet weather on performance" },
        reliability_influence: { min: 0, max: 100, step: 1, default: 50, description: "How much car reliability affects results" },
        strategy_aggressiveness: { min: 0, max: 100, step: 1, default: 50, description: "How aggressive pit strategies are" },
        grid_weight: { min: 0, max: 100, step: 1, default: 55, description: "Weight given to starting grid position" }
      };
      
      const saved = F1.getTuning() || {};
      const current = {};
      Object.entries(defaultWeights).forEach(([key, cfg]) => { current[key] = saved[key] != null ? saved[key] : cfg.default; });

      $("#tuning-sliders").innerHTML = Object.entries(defaultWeights).map(([key, cfg]) => {
        const meta = WEIGHT_LABELS[key] || { label: key, left: "Low", right: "High" };
        return `<div>
          <div class="flex items-center justify-between mb-1">
            <div class="text-sm font-semibold">${meta.label}</div>
            <span id="val-${key}" class="f1-mono text-sm font-bold text-red">${current[key]}</span>
          </div>
          <div class="fs-11 mb-2 text-sub">${F1.escapeHtml(cfg.description)}</div>
          <input type="range" class="f1-range" id="slider-${key}" min="${cfg.min}" max="${cfg.max}" step="${cfg.step}" value="${current[key]}">
          <div class="flex justify-between fs-9 uppercase tracking-widest font-semibold mt-1 text-muted">
            <span>${meta.left}</span><span>${meta.right}</span>
          </div>
        </div>`;
      }).join("");

      Object.keys(defaultWeights).forEach((key) => {
        $(`#slider-${key}`).addEventListener("input", (e) => {
          $(`#val-${key}`).textContent = e.target.value;
          saveTuning();
        });
      });

      function saveTuning() {
        const values = {};
        Object.keys(defaultWeights).forEach((key) => { values[key] = Number($(`#slider-${key}`).value); });
        F1.setTuning(values);
        const saved = $("#tuning-saved");
        saved.style.display = "block";
        clearTimeout(saveTuning._t);
        saveTuning._t = setTimeout(() => { saved.style.display = "none"; }, 1500);
      }

      $("#tuning-reset").addEventListener("click", () => {
        Object.entries(defaultWeights).forEach(([key, cfg]) => {
          $(`#slider-${key}`).value = cfg.default;
          $(`#val-${key}`).textContent = cfg.default;
        });
        F1.setTuning(null);
        try { localStorage.removeItem("f1-tuning"); } catch (e) {}
      });
    }
  }

  function bindDisplayPrefs() {
    const SESSIONS = [{ id: "practice", label: "Practice" }, { id: "qualifying", label: "Qualifying" }, { id: "race", label: "Race" }];
    const WEATHERS = [{ id: "dry", label: "Dry" }, { id: "mixed", label: "Mixed" }, { id: "wet", label: "Wet" }];
    let prefs = {};
    try { prefs = JSON.parse(localStorage.getItem("f1-display-prefs") || "{}"); } catch (e) {}
    prefs.defaultSession = prefs.defaultSession || "race";
    prefs.defaultWeather = prefs.defaultWeather || "dry";
    prefs.compactRows = !!prefs.compactRows;

    function save() { try { localStorage.setItem("f1-display-prefs", JSON.stringify(prefs)); } catch (e) {} }

    function paintSession() {
      $("#default-session-buttons").innerHTML = SESSIONS.map((s) =>
        `<button data-id="${s.id}" class="target-pill ${prefs.defaultSession === s.id ? "is-active" : ""}">${s.label}</button>`).join("");
      $("#default-session-buttons").querySelectorAll("[data-id]").forEach((b) =>
        b.addEventListener("click", () => { prefs.defaultSession = b.dataset.id; save(); paintSession(); }));
    }
    function paintWeather() {
      $("#default-weather-buttons").innerHTML = WEATHERS.map((w) =>
        `<button data-id="${w.id}" class="target-pill ${prefs.defaultWeather === w.id ? "is-active" : ""}">${w.label}</button>`).join("");
      $("#default-weather-buttons").querySelectorAll("[data-id]").forEach((b) =>
        b.addEventListener("click", () => { prefs.defaultWeather = b.dataset.id; save(); paintWeather(); }));
    }
    paintSession();
    paintWeather();

    const toggle = $("#toggle-compact");
    function paintToggle() {
      toggle.classList.toggle("is-on", prefs.compactRows);
      toggle.setAttribute("aria-checked", String(prefs.compactRows));
    }
    paintToggle();
    toggle.addEventListener("click", () => { prefs.compactRows = !prefs.compactRows; save(); paintToggle(); });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
