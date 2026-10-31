import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRaces } from "../lib/hooks";
import { useApp } from "../lib/store";

export const SHORTCUTS: { label: string; keys: string; to?: string }[] = [
  { label: "Home", keys: "h", to: "/" }, { label: "Dashboard", keys: "d", to: "/dashboard" }, { label: "Predictions", keys: "p", to: "/predictions" },
  { label: "Standings", keys: "s", to: "/standings" }, { label: "Head to Head", keys: "v", to: "/head2head" }, { label: "Fantasy", keys: "f", to: "/fantasy" },
  { label: "Guide", keys: "g", to: "/guide" }, { label: "Settings", keys: ",", to: "/settings" },
];

export function useShortcuts() {
  const nav = useNavigate();
  const enabled = useApp((x) => x.s.shortcuts);
  const [help, setHelp] = useState(false);
  useEffect(() => {
    if (!enabled) return;
    let armed = 0;
    const on = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === "?") { setHelp((h) => !h); return; }
      if (e.key === "Escape") setHelp(false);
      if (e.key === "g" && Date.now() - armed > 1500) { armed = Date.now(); return; }
      if (armed && Date.now() - armed < 1500) { const hit = SHORTCUTS.find((x) => x.keys === e.key); armed = 0; if (hit?.to) { e.preventDefault(); nav(hit.to); } }
    };
    window.addEventListener("keydown", on);
    return () => window.removeEventListener("keydown", on);
  }, [enabled, nav]);
  useEffect(() => { (window as unknown as { __f1Help?: () => void }).__f1Help = () => setHelp(true); }, []);
  return help ? <ShortcutsModal onClose={() => setHelp(false)} /> : null;
}

export function ShortcutsModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4" onClick={onClose} role="dialog" aria-modal="true" aria-label="Keyboard shortcuts">
      <div className="card w-full max-w-md p-5" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between"><h3 className="text-[15px] font-bold">Keyboard shortcuts</h3><button onClick={onClose} aria-label="Close"><X size={16} /></button></div>
        <ul className="grid grid-cols-2 gap-2 text-[12px]">{SHORTCUTS.map((s) => <li key={s.label} className="flex items-center justify-between rounded-md border border-edge px-3 py-2">{s.label}<span className="text-mute"><kbd>g</kbd> then <kbd>{s.keys}</kbd></span></li>)}
          <li className="flex items-center justify-between rounded-md border border-edge px-3 py-2">Shortcuts list<kbd>?</kbd></li><li className="flex items-center justify-between rounded-md border border-edge px-3 py-2">Search<span className="text-mute"><kbd>Ctrl</kbd> <kbd>K</kbd></span></li></ul>
      </div>
    </div>
  );
}

/** Browser notification shortly before the next race starts (works while the tab is open). */
export function useReminders() {
  const { remind, remindLead } = useApp((x) => x.s);
  const { data: races } = useRaces();
  useEffect(() => {
    if (!remind || typeof Notification === "undefined" || Notification.permission !== "granted") return;
    const next = races?.find((r) => r.status === "upcoming");
    if (!next) return;
    const wait = Date.parse(next.start_utc) - remindLead * 60000 - Date.now();
    if (wait <= 0 || wait > 2_000_000_000) return;
    const id = setTimeout(() => new Notification(`${next.name} starts soon`, { body: `Lights out in about ${remindLead >= 60 ? `${remindLead / 60} h` : `${remindLead} min`}. Open F1 Predictor for the latest forecast.`, icon: "/img/logo-f1.png" }), wait);
    return () => clearTimeout(id);
  }, [remind, remindLead, races]);
}
