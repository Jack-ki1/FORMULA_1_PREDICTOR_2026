import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { applyAppearance } from "./lib/appearance";
import { useApp } from "./lib/store";
import Dashboard from "./pages/Dashboard";
import Fantasy from "./pages/Fantasy";
import Guide from "./pages/Guide";
import Head2Head from "./pages/Head2Head";
import Predictions from "./pages/Predictions";
import SettingsPage from "./pages/Settings";
import Standings from "./pages/Standings";

const LANDING = { dashboard: "/dashboard", predictions: "/predictions", standings: "/standings", head2head: "/head2head", fantasy: "/fantasy" } as const;

export default function App() {
  const s = useApp((x) => x.s);
  useEffect(() => {
    applyAppearance(s);
    if (s.mode !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    const on = () => applyAppearance(s);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [s]);
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to={LANDING[s.landing]} replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="predictions" element={<Predictions />} />
        <Route path="standings" element={<Standings />} />
        <Route path="head2head" element={<Head2Head />} />
        <Route path="fantasy" element={<Fantasy />} />
        <Route path="guide" element={<Guide />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<div className="p-10 text-center text-mute">Page not found.</div>} />
      </Route>
    </Routes>
  );
}
