import { Crosshair } from "lucide-react";
import { ControlCenter } from "../components/Control";
import Hero from "../components/Hero";
import { Confidence, ResultsPanel, StatCards, WinProbability } from "../components/Panels";
import { Promo, QuickActions, RecentRaces, TrackWeather } from "../components/SideCards";
import { Card, CardTitle, ErrorNote } from "../components/ui";
import { AwaitRun } from "../components/ui";
import { ExportPanel, GridVsFinish, PositionHeatmap, SessionVisual, TeamBattle, TrackTraits } from "../components/Visuals";
import {
  PracticePaceGap, PracticeFastestDonut, PracticeOneLapVsLongRun, PracticeTeamPaceLadder, PracticeTop3Top10,
  QualiSurvivalFunnel, QualiGapToPole, QualiPoleDonut, QualiTeammateBattle, QualiBothInQ3,
  RaceTeamWinShare, RaceGridToWin, RacePositionsGainedLost, RaceScenarioDonut, RaceWinGivenSC,
} from "../components/SessionPlots";
import { usePrediction } from "../lib/hooks";
import { useApp } from "../lib/store";
import { resultState } from "../lib/util";

export default function Dashboard() {
  const { draft, applied } = useApp();
  const showExport = useApp((s) => s.s.showExport);
  const q = usePrediction(applied);
  const p = q.data;
  const loading = q.isFetching;
  const state = resultState(draft, applied, p);
  const showResults = state === "fresh" || state === "stale";
  const isRaceLike = draft.session === "race" || draft.session === "sprint";
  const isPractice = draft.session === "practice";
  const isQualifying = draft.session === "qualifying" || draft.session === "sprint_qualifying";
  const title = ({ practice: "Practice Prediction", qualifying: "Qualifying Prediction", sprint_qualifying: "Sprint Qualifying", sprint: "Sprint Prediction", race: "Grand Prix Prediction" } as Record<string, string>)[draft.session] ?? "Prediction";
  const sub = `· ${isPractice ? draft.sub ?? "FP2" : ""}`.trim() || (p?.race.name ?? "the upcoming race");

  return (
    <>
      <Hero />
      <div className="space-y-3 p-3 md:p-3.5">
        <ControlCenter p={p} loading={loading} />
        {q.isError && !p && <ErrorNote error={q.error} retry={() => q.refetch()} />}
        <Card className="space-y-3 p-3.5">
          <CardTitle icon={<Crosshair size={13} />} title={title} sub={`AI-powered predictions for ${sub}${p?.source === "seed" ? " · offline snapshot data" : ""}`} />
          {state === "stale" && <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-3 text-[11px] text-amber-200">Inputs changed — press Run Prediction to refresh.</div>}
          {!showResults ? <AwaitRunPanel /> : (
            <>
              <StatCards p={p} loading={loading} />
              <div className="grid gap-3 xl:grid-cols-[1.2fr_1.2fr]">
                <WinProbability p={p} loading={loading} />
                <ResultsPanel p={p} loading={loading} />
              </div>
              <div className="grid gap-3 xl:grid-cols-[1.6fr_1fr]"><PositionHeatmap p={p} loading={loading} /><TeamBattle p={p} loading={loading} /></div>
              {isRaceLike && (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <RaceTeamWinShare p={p} loading={loading} />
                  <RaceScenarioDonut p={p} loading={loading} />
                  <GridVsFinish p={p} loading={loading} />
                  <RaceGridToWin p={p} loading={loading} />
                  <RacePositionsGainedLost p={p} loading={loading} />
                  <RaceWinGivenSC p={p} loading={loading} />
                </div>
              )}
              {isPractice && (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <PracticePaceGap p={p} loading={loading} />
                  <PracticeFastestDonut p={p} loading={loading} />
                  <PracticeOneLapVsLongRun p={p} loading={loading} />
                  <PracticeTeamPaceLadder p={p} loading={loading} />
                  <PracticeTop3Top10 p={p} loading={loading} />
                </div>
              )}
              {isQualifying && (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <QualiSurvivalFunnel p={p} loading={loading} />
                  <QualiGapToPole p={p} loading={loading} />
                  <QualiPoleDonut p={p} loading={loading} />
                  <QualiTeammateBattle p={p} loading={loading} />
                  <QualiBothInQ3 p={p} loading={loading} />
                </div>
              )}
              {isQualifying && <SessionVisual p={p} loading={loading} />}
              <div className="grid gap-3 xl:grid-cols-[1fr_1fr_1.2fr]">
                <TrackTraits p={p} loading={loading} />
                <TrackWeather p={p} loading={loading} />
                <Confidence p={p} loading={loading} />
              </div>
              {showExport && p && <ExportPanel p={p} />}
            </>
          )}
        </Card>
        <div className="grid gap-3 lg:grid-cols-3"><RecentRaces /><QuickActions /><Promo /></div>
      </div>
    </>
  );
}

function AwaitRunPanel() {
  return <div className="card p-6 text-center"><AwaitRun /></div>;
}
