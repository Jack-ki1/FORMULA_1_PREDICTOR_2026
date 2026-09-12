/**
 * theme_toggle.js — dark/light mode switch.
 * Persists choice in localStorage and fires "f1:theme-change" so any page
 * with live charts can redraw them in the new palette.
 */
(function () {
  "use strict";

  function applyIcon(theme) {
    const moon = document.getElementById("icon-moon");
    const sun = document.getElementById("icon-sun");
    if (!moon || !sun) return;
    moon.style.display = theme === "dark" ? "none" : "block";
    sun.style.display = theme === "dark" ? "block" : "none";
  }

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("f1-theme", theme); } catch (e) {}
    applyIcon(theme);
    document.dispatchEvent(new CustomEvent("f1:theme-change", { detail: { theme } }));
  }

  document.addEventListener("DOMContentLoaded", function () {
    const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
    applyIcon(current);

    const btn = document.getElementById("theme-toggle-btn");
    if (btn) {
      btn.addEventListener("click", function () {
        const now = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        setTheme(now);
      });
    }
  });

  window.F1Theme = { setTheme: setTheme };
})();
