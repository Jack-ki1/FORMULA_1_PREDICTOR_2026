import type { Settings } from "./store";

const hex = (h: string) => { const m = /^#?([0-9a-f]{6})$/i.exec(h.trim()); return m ? [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16)) : null; };
const triplet = (rgb: number[]) => rgb.join(" ");
const mix = (a: number[], b: number[], t: number) => a.map((v, i) => Math.round(v + (b[i] - v) * t));

export function resolveMode(m: Settings["mode"]): "light" | "dark" {
  return m === "system" ? (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark") : m;
}

/** Applies every appearance / accessibility setting to <html>. Pure DOM, no React needed. */
export function applyAppearance(s: Settings) {
  const r = document.documentElement, st = r.style, d = r.dataset;
  d.mode = resolveMode(s.mode);
  const acc = hex(s.accent) ?? [225, 6, 0];
  const isDefault = s.accent.toLowerCase() === "#e10600";
  st.setProperty("--accent", triplet(acc));
  st.setProperty("--accent2", triplet(isDefault ? [255, 45, 70] : mix(acc, [255, 255, 255], 0.28)));
  st.setProperty("--r", `${s.radius}px`);
  st.setProperty("--fs", String(s.fontScale));
  const map: [string, string | undefined][] = [["--ink", s.colors.bg], ["--pf", s.colors.surface], ["--pt", s.colors.surface], ["--edge", s.colors.border], ["--fg", s.colors.text]];
  for (const [k, v] of map) { const c = v ? hex(v) : null; if (c) st.setProperty(k, triplet(c)); else st.removeProperty(k); }
  d.density = s.density; d.ctables = String(s.compactTables); d.hc = String(s.highContrast); d.rm = String(s.reduceMotion);
  d.dys = String(s.dyslexia); d.ul = String(s.underlineLinks); d.saver = String(s.saveData);
}
