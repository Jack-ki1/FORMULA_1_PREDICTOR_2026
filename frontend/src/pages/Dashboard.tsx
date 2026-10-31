import { Crosshair } from "lucide-react";
import { ControlCenter } from "../components/Control";
import Hero from "../components/Hero";
import { Confidence, Qualifying, ResultsTable, StatCards, Strategy, WinProbability } from "../components/Panels";
import { H2HCard, Promo, QuickActions, RecentRaces, SimPanel, TrackWeather } from "../components/SideCards";
import { Card, CardTitle, ErrorNote } from "../components/ui";
import { ExportPanel, GridVsFinish, PositionHeatmap, SessionVisual, TeamBattle, TrackTraits } from "../components/Visuals";
import { usePrediction } from "../lib/hooks";
import { useApp } from "../lib/store";

export default function Dashboard() {
  const applied = useApp((s) => s.applied);
  const showExport = useApp((s) => s.s.showExport);
  const q = usePrediction(applied);
  const p = q.data;
  const raceLike = p ? p.params.session === "race" || p.params.session === "sprint" : true;
  return (
    <>
      <Hero />
      <div className="space-y-3 p-3 md:p-3.5">
        <ControlCenter p={p} loading={q.isFetching} />
        {q.isError && !p && <ErrorNote error={q.error} retry={() => q.refetch()} />}
        <Card className="space-y-3 p-3.5">
          <CardTitle icon={<Crosshair size={13} />} title="Race Prediction" sub={`AI-powered predictions for ${p ? p.race.name : "the upcoming race"}${p?.source === "seed" ? " · offline snapshot data" : ""}`} />
          <StatCards p={p} />
          <div className="grid gap-3 xl:grid-cols-[2.2fr_1fr_1.2fr]"><WinProbability p={p} /><Qualifying p={p} /><Strategy p={p} /></div>
        </Card>
        <div className="grid gap-3 xl:grid-cols-[1.7fr_1fr]"><PositionHeatmap p={p} /><TeamBattle p={p} /></div>
        <div className="grid gap-3 xl:grid-cols-[1.25fr_1fr]">{raceLike ? <GridVsFinish p={p} /> : <SessionVisual p={p} />}<div className="grid gap-3">{raceLike && p?.params.session !== "practice" && <TrackTraits p={p} />}{!raceLike && <TrackTraits p={p} />}</div></div>
        <div className="grid gap-3 xl:grid-cols-[1.05fr_1.15fr_1fr]"><TrackWeather p={p} /><H2HCard p={p} /><SimPanel p={p} loading={q.isFetching} /></div>
        <div className="grid gap-3 xl:grid-cols-[1.1fr_1fr]"><ResultsTable p={p} /><Confidence p={p} /></div>
        {showExport && <ExportPanel p={p} />}
        <div className="grid gap-3 lg:grid-cols-3"><RecentRaces /><QuickActions /><Promo /></div>
      </div>
    </>
  );
}
