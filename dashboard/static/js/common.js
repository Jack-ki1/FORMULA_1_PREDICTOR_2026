/**
 * common.js — shared helpers used across every dashboard page.
 * No framework, no build step: plain ES modules-free JS attached to `window.F1`.
 */
(function () {
  "use strict";

  const F1 = {};

  // ---------------------------------------------------------------------
  // Palette (mirrors styles.css CSS variables so Chart.js / canvas code,
  // which can't read CSS vars directly in every browser reliably, has a
  // single source of truth too).
  // ---------------------------------------------------------------------
  const PALETTE_LIGHT = {
    red: "#E10600", redDark: "#B80500", redTint: "#FDEDEC",
    bg: "#F4F5F7", surface: "#FFFFFF", surfaceAlt: "#EEF0F3", border: "#E3E5EA",
    text: "#15151E", sub: "#6B7280", muted: "#9AA0AC",
    navy: "#16233F", navyLight: "#22345A",
    purple: "#9D4EDD", purpleTint: "#F4EBFC",
    green: "#1DA36B", amber: "#D97B0A", gridline: "#ECEDF1",
    palette: ["#E10600", "#1DA36B", "#D97B0A", "#16233F", "#9D4EDD", "#00A19B", "#FF8000", "#0090FF"],
  };
  const PALETTE_DARK = {
    red: "#FF3B30", redDark: "#E8002D", redTint: "rgba(255,59,48,0.14)",
    bg: "#0A0C10", surface: "#15181F", surfaceAlt: "#1C2028", border: "#2B3039",
    text: "#F1F2F5", sub: "#9BA2AF", muted: "#6B7280",
    navy: "#0D1526", navyLight: "#16233F",
    purple: "#B983F2", purpleTint: "rgba(157,78,221,0.2)",
    green: "#2ECC8F", amber: "#F0A93B", gridline: "#2B3039",
    palette: ["#FF3B30", "#2ECC8F", "#F0A93B", "#16233F", "#B983F2", "#00A19B", "#FF8000", "#0090FF"],
  };
  F1.palette = function () {
    const theme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
    return theme === "dark" ? PALETTE_DARK : PALETTE_LIGHT;
  };

  const TEAM_COLORS = {
    mclaren: "#FF8000", ferrari: "#E8002D", redbull: "#3671C6", mercedes: "#00A19B",
    astonmartin: "#229971", williams: "#1E6FCE", audi: "#BB0A30", alpine: "#0090FF",
    haas: "#9198A1", racingbulls: "#3F5FCC", cadillac: "#9C7A19",
  };
  F1.teamColor = (teamId) => TEAM_COLORS[(teamId || "").toLowerCase()] || "#9AA0AC";

  const COMPOUNDS = {
    Soft: { color: "#DA291C", label: "Soft" },
    Medium: { color: "#F5D033", label: "Medium" },
    Hard: { color: "#F2F2F2", label: "Hard", outline: "#9AA0AC" },
    Intermediate: { color: "#43A047", label: "Intermediate" },
    Wet: { color: "#1E88E5", label: "Wet" },
  };
  F1.compound = (name) => COMPOUNDS[name] || COMPOUNDS.Medium;
  F1.compoundForWeather = (weather) => (weather === "wet" ? "Wet" : weather === "mixed" ? "Intermediate" : "Medium");
  F1.tyreChipHtml = (compound) => {
    const t = F1.compound(compound);
    return `<span class="inline-flex items-center gap-1.5">
      <span class="tyre-dot" style="width:14px;height:14px;background:${t.color};border-color:${t.outline || t.color}"></span>
      <span class="fs-11 font-semibold" style="color:var(--text)">${t.label}</span>
    </span>`;
  };

  // ---------------------------------------------------------------------
  // Model tuning weights (chaos_level, wet_influence, reliability_influence,
  // strategy_aggressiveness, grid_weight) — set on the Analytics & Settings
  // page, persisted locally, and picked up by any page that calls predict.
  // ---------------------------------------------------------------------
  F1.getTuning = function () {
    try {
      const raw = localStorage.getItem("f1-tuning");
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  };
  F1.setTuning = function (weights) {
    try { localStorage.setItem("f1-tuning", JSON.stringify(weights)); } catch (e) {}
  };

  // ---------------------------------------------------------------------
  // fetch helper
  // ---------------------------------------------------------------------
  F1.api = async function (url, options) {
    const opts = Object.assign({ headers: { "Content-Type": "application/json" } }, options || {});
    if (opts.body && typeof opts.body !== "string") opts.body = JSON.stringify(opts.body);
    const res = await fetch(url, opts);
    if (!res.ok) {
      let msg = res.statusText;
      try { const j = await res.json(); msg = j.error || msg; } catch (e) {}
      throw new Error(msg || ("Request failed: " + url));
    }
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return res.json();
    return res.blob();
  };

  // ---------------------------------------------------------------------
  // Driver directory — fetched once, cached, keyed by driver code.
  // Powers every page that needs a name/team/number for a "code" the
  // prediction API returns.
  // ---------------------------------------------------------------------
  let _driverCache = null;
  F1.getDrivers = async function () {
    if (_driverCache) return _driverCache;
    const list = await F1.api("/h2h/api/drivers");
    _driverCache = list;
    return list;
  };
  F1.getDriverMap = async function () {
    const list = await F1.getDrivers();
    const map = {};
    list.forEach((d) => { map[d.code] = d; });
    return map;
  };

  let _raceCache = null;
  F1.getRaces = async function () {
    if (_raceCache) return _raceCache;
    _raceCache = await F1.api("/dashboard/api/races");
    return _raceCache;
  };

  // ---------------------------------------------------------------------
  // Formatters
  // ---------------------------------------------------------------------
  F1.pct = (v, digits) => (v == null ? "—" : (v * 100).toFixed(digits == null ? 1 : digits) + "%");
  F1.ordinal = (n) => {
    const s = ["th", "st", "nd", "rd"], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  };
  F1.riskColor = (risk) => {
    const p = F1.palette();
    if (risk === "High") return p.red;
    if (risk === "Medium") return p.amber;
    return p.green;
  };
  F1.dnfRiskFromReliability = (reliability) => {
    // Mirrors config/constants.py DNF_RISK_LEVELS thresholds against (100 - reliability)
    const risk = 100 - reliability;
    if (risk >= 32) return "High";
    if (risk >= 20) return "Medium";
    return "Low";
  };
  F1.escapeHtml = (str) => String(str == null ? "" : str).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));

  // ---------------------------------------------------------------------
  // Toast / inline error banner
  // ---------------------------------------------------------------------
  F1.showError = function (container, message) {
    if (!container) return;
    container.innerHTML =
      '<div class="fs-11 font-semibold px-3 py-2 rounded-lg flex items-center gap-2" ' +
      'style="background:var(--red-tint);color:var(--red);border:1px solid var(--border)">' +
      '<span>&#9888;</span><span>' + F1.escapeHtml(message) + "</span></div>";
  };

  // ---------------------------------------------------------------------
  // Live "Updated Xs ago" tick in the nav — purely cosmetic, matches the
  // reference's `tick` state.
  // ---------------------------------------------------------------------
  function startTick() {
    const el = document.getElementById("nav-tick");
    if (!el) return;
    let t = 0;
    setInterval(() => { t += 1; el.textContent = String(t); }, 1000);
  }
  document.addEventListener("DOMContentLoaded", startTick);

  window.F1 = F1;
})();
