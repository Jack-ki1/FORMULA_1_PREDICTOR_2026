import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { SimParams } from "./api";

export interface Settings {
  mode: "light" | "dark" | "system"; accent: string; fontScale: number; radius: number; density: "comfortable" | "compact";
  colors: { bg?: string; surface?: string; border?: string; text?: string };
  reduceMotion: boolean; highContrast: boolean; dyslexia: boolean; underlineLinks: boolean;
  sim: SimParams;
  showGrid: boolean; showExport: boolean; compactTables: boolean; landing: "dashboard" | "predictions" | "standings" | "head2head" | "fantasy";
  remind: boolean; remindLead: number;
  displayName: string; favDriver: string; favTeam: string;
  apiBase: string; timeoutMs: number; debug: boolean; shortcuts: boolean; saveData: boolean;
}

export const DEFAULT_SIM: SimParams = {
  race_id: null, sims: 3000, session: "race", weather: "auto", mechanical_failures: true, safety_car: true, enhanced: true, chaos: 0.5,
  grid_mode: "auto", grid: [], grid_weight: 0.55, wet_influence: 0.6, reliability: 0.4, strategy_aggr: 0.5, sc_weight: 0.3,
  team_w: 0.6, driver_w: 0.4, track_w: 1, weather_w: 1, deg_w: 1, form_k: 32, ci: 0.95,
};

export const DEFAULT_SETTINGS: Settings = {
  mode: "dark", accent: "#E10600", fontScale: 1, radius: 8, density: "comfortable", colors: {},
  reduceMotion: false, highContrast: false, dyslexia: false, underlineLinks: false,
  sim: DEFAULT_SIM,
  showGrid: true, showExport: true, compactTables: false, landing: "dashboard",
  remind: false, remindLead: 60,
  displayName: "Jack", favDriver: "", favTeam: "",
  apiBase: "", timeoutMs: 20000, debug: false, shortcuts: true, saveData: false,
};

interface State {
  s: Settings; draft: SimParams; applied: SimParams; fantasy: string[];
  set: (p: Partial<Settings>) => void; setSim: (p: Partial<SimParams>) => void;
  setDraft: (p: Partial<SimParams>) => void; run: (p?: Partial<SimParams>) => void;
  setFantasy: (c: string[]) => void; replaceSettings: (s: Partial<Settings>) => void; resetAll: () => void;
}

const merge = (x?: Partial<Settings>): Settings => ({ ...DEFAULT_SETTINGS, ...(x ?? {}), colors: { ...(x?.colors ?? {}) }, sim: { ...DEFAULT_SIM, ...(x?.sim ?? {}), race_id: null, grid: [], grid_mode: "auto" } });
// Re-seed the dashboard controls from the saved defaults but keep the race and grid the user is working on.
const reseed = (s: Settings, cur: SimParams): SimParams => ({ ...s.sim, race_id: cur.race_id, grid_mode: cur.grid_mode, grid: cur.grid });

export const useApp = create<State>()(
  persist(
    (set, get) => ({
      s: DEFAULT_SETTINGS, draft: DEFAULT_SIM, applied: DEFAULT_SIM, fantasy: [],
      set: (p) => { const s = { ...get().s, ...p }; set({ s, draft: reseed(s, get().draft), applied: reseed(s, get().applied) }); },
      setSim: (p) => get().set({ sim: { ...get().s.sim, ...p } }),
      setDraft: (p) => set({ draft: { ...get().draft, ...p } }),
      run: (p) => { const d = { ...get().draft, ...p }; set({ draft: d, applied: d }); },
      setFantasy: (fantasy) => set({ fantasy }),
      replaceSettings: (x) => { const s = merge({ ...get().s, ...x }); set({ s, draft: s.sim, applied: s.sim }); },
      resetAll: () => set({ s: DEFAULT_SETTINGS, draft: DEFAULT_SIM, applied: DEFAULT_SIM, fantasy: [] }),
    }),
    {
      name: "f1p26", version: 2, partialize: (st) => ({ s: st.s, fantasy: st.fantasy }),
      merge: (p, cur) => {
        const x = (p ?? {}) as Partial<State>;
        const s = merge(x.s);
        return { ...cur, s, fantasy: x.fantasy ?? [], draft: s.sim, applied: s.sim };
      },
    },
  ),
);

export const ADMIN_KEY = "f1p26_admin";
