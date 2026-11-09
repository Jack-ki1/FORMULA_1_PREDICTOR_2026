import type { Settings } from "./store";

const hex = (h: string) => { const m = /^#?([0-9a-f]{6})$/i.exec((h||"").trim()); return m ? [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16)) : null; };
const triplet = (rgb: number[]) => rgb.join(" ");
const mix = (a: number[], b: number[], t: number) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
const setVar = (st: CSSStyleDeclaration, k: string, v?: string) => { const c = v ? hex(v) : null; if (c) st.setProperty(k, triplet(c)); else st.removeProperty(k); };

export function resolveMode(m: Settings["mode"]): "light" | "dark" {
  return m === "system" ? (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark") : m;
}

/** Applies every appearance / accessibility setting to <html>. Pure DOM, no React needed. */
export function applyAppearance(s: Settings) {
  const r = document.documentElement, st = r.style, d = r.dataset, c = s.colors || {};
  d.mode = resolveMode(s.mode);
  const acc = hex(s.accent) ?? [225, 6, 0];
  const isDefault = (s.accent || "").toLowerCase() === "#e10600";
  st.setProperty("--accent", triplet(acc));
  st.setProperty("--accent2", triplet(hex(c.accent2 || "") ?? (isDefault ? [255, 45, 70] : mix(acc, [255, 255, 255], 0.28))));
  st.setProperty("--r", `${s.radius}px`);
  st.setProperty("--fs", String(s.fontScale));
  setVar(st, "--ink", c.bg); setVar(st, "--pf", c.surface); setVar(st, "--pt", c.surface); setVar(st, "--edge", c.border);
  setVar(st, "--fg", c.text); setVar(st, "--mute", c.mute);
  const direct: [string, string | undefined][] = [["--chart1",c.chart1],["--chart2",c.chart2],["--chart3",c.chart3],["--chart4",c.chart4],["--chart5",c.chart5],["--chart6",c.chart6],["--ok",c.success],["--warn",c.warning],["--bad",c.danger],["--info",c.info],["--tt-bg",c.tooltipBg],["--tt-fg",c.tooltipText]];
  for (const [k, v] of direct) { const x = v ? hex(v) : null; if (x) st.setProperty(k, triplet(x)); else st.removeProperty(k); }
  d.density = s.density; d.ctables = String(s.compactTables); d.hc = String(s.highContrast); d.rm = String(s.reduceMotion);
  d.dys = String(s.dyslexia); d.ul = String(s.underlineLinks); d.saver = String(s.saveData);
}
