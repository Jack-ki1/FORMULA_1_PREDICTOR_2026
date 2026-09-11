"use client";

import { useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { api, type FeatureWeights } from "@/lib/api-client";
import { ProbabilityBar } from "@/components/ProbabilityBar";
import { Slider } from "@/components/Slider";

const SESSION_TABS = [
  { value: "race", label: "Race" },
  { value: "qualifying", label: "Qualifying" },
];

const DEFAULT_WEIGHTS: Omit<FeatureWeights, "scope"> = {
  chaos_level: 50,
  wet_influence: 50,
  reliability_influence: 50,
  strategy_aggressiveness: 50,
  grid_weight: 55,
};


export default function PredictionsPage() {
  const { raceId } = useParams<{ raceId: string }>();
  const router = useRouter();
  const { data: session } = useSession();
  const queryClient = useQueryClient();

  const [sessionType, setSessionType] = useState("race");
  const [weather, setWeather] = useState("dry");
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [whatIfOpen, setWhatIfOpen] = useState(false);
  const [pickTarget, setPickTarget] = useState<"winner" | "podium" | "pole" | "fastest_lap">("winner");
  const [pickMessage, setPickMessage] = useState<string | null>(null);

  const racesQuery = useQuery({ queryKey: ["races"], queryFn: api.races });
  const driversQuery = useQuery({ queryKey: ["h2h-drivers"], queryFn: api.h2hDrivers });
  const predictionsQuery = useQuery({
    queryKey: ["predictions", raceId, sessionType],
    queryFn: () => api.predictions(raceId, sessionType),
    retry: false,
  });

  const recomputeMutation = useMutation({
    mutationFn: () =>
      api.recompute(raceId, {
        session_type: sessionType,
        weather,
        feature_weights: weights,
        simulation_count: 5000,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["predictions", raceId, sessionType], data);
    },
  });

  const pickMutation = useMutation({
    mutationFn: (driverCode: string) =>
      api.submitPick(session!.apiToken!, { race_id: raceId, session: sessionType, target: pickTarget, driver_id: driverCode }),
    onSuccess: (pick) => setPickMessage(`Saved: ${pick.driver_id} to ${pickTarget.replace("_", " ")}`),
    onError: (err: Error) => setPickMessage(err.message),
  });

  const race = racesQuery.data?.find((r) => r.id === raceId);

  const driverByCode = useMemo(() => {
    const map = new Map<string, { name: string; team_color: string }>();
    driversQuery.data?.forEach((d) => map.set(d.code, { name: d.name, team_color: d.team_color }));
    return map;
  }, [driversQuery.data]);

  const rows = useMemo(() => {
    const probs = predictionsQuery.data?.winner_probabilities ?? {};
    return Object.entries(probs)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 12)
      .map(([code, p], i) => ({ code, probability: p, rank: i + 1, ...driverByCode.get(code) }));
  }, [predictionsQuery.data, driverByCode]);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <select
            value={raceId}
            onChange={(e) => router.push(`/predictions/${e.target.value}`)}
            className="border border-graphite-700 bg-graphite-900 px-3 py-2 text-sm"
          >
            {racesQuery.data
              ?.filter((r) => r.status !== "cancelled")
              .map((r) => (
                <option key={r.id} value={r.id}>
                  {r.flag} {r.name}
                </option>
              ))}
          </select>
          {race && <p className="mt-1 text-sm text-paper-dim">{race.circuit} · Round {race.round}</p>}
        </div>
        <div className="flex gap-1 border border-graphite-700 p-1">
          {SESSION_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setSessionType(tab.value)}
              className={`px-3 py-1.5 text-sm ${sessionType === tab.value ? "bg-graphite-700" : "text-paper-dim hover:text-paper"}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {predictionsQuery.isLoading && <p className="text-paper-dim">Running the simulation…</p>}
      {predictionsQuery.isError && (
        <p className="rounded border border-red-flag/40 bg-red-flag/10 px-4 py-3 text-sm text-red-flag">
          Couldn&apos;t load predictions for this race yet.
        </p>
      )}

      {rows.length > 0 && (
        <section>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-medium">Win probability</h2>
            <span className="text-xs text-paper-dim">
              {predictionsQuery.data?.source === "precomputed" ? "precomputed" : predictionsQuery.data?.source}
            </span>
          </div>
          <div>
            {rows.map((row) => (
              <ProbabilityBar
                key={row.code}
                driverCode={row.code}
                driverName={row.name}
                teamColor={row.team_color}
                probability={row.probability}
                rank={row.rank}
              />
            ))}
          </div>
        </section>
      )}

      {/* Pick submission — only meaningful for upcoming races */}
      {race?.status === "upcoming" && (
        <section className="border border-graphite-700 p-4">
          <h3 className="mb-3 text-sm font-medium">Make your pick</h3>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={pickTarget}
              onChange={(e) => setPickTarget(e.target.value as typeof pickTarget)}
              className="border border-graphite-700 bg-graphite-900 px-2 py-1.5 text-sm"
            >
              <option value="winner">Race winner</option>
              <option value="podium">On the podium</option>
              <option value="pole">Pole position</option>
              <option value="fastest_lap">Fastest lap</option>
            </select>
            <select
              onChange={(e) => e.target.value && pickMutation.mutate(e.target.value)}
              defaultValue=""
              disabled={!session}
              className="border border-graphite-700 bg-graphite-900 px-2 py-1.5 text-sm disabled:opacity-50"
            >
              <option value="" disabled>
                {session ? "Choose a driver…" : "Sign in to pick"}
              </option>
              {rows.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.code} — {r.name ?? r.code}
                </option>
              ))}
            </select>
          </div>
          {pickMessage && <p className="mt-2 text-xs text-paper-dim">{pickMessage}</p>}
        </section>
      )}

      <section>
        <button
          onClick={() => setWhatIfOpen((o) => !o)}
          className="text-sm text-paper-dim underline decoration-graphite-600 underline-offset-4 hover:text-paper"
        >
          {whatIfOpen ? "Hide" : "Adjust model assumptions"}
        </button>
        {whatIfOpen && (
          <div className="mt-4 grid gap-6 border border-graphite-700 p-4 md:grid-cols-2">
            <div className="space-y-4">
              <Slider label="Chaos" value={weights.chaos_level} onChange={(v) => setWeights({ ...weights, chaos_level: v })} />
              <Slider
                label="Wet-weather influence"
                value={weights.wet_influence}
                onChange={(v) => setWeights({ ...weights, wet_influence: v })}
              />
              <Slider
                label="Reliability influence"
                value={weights.reliability_influence}
                onChange={(v) => setWeights({ ...weights, reliability_influence: v })}
              />
              <Slider
                label="Strategy aggressiveness"
                value={weights.strategy_aggressiveness}
                onChange={(v) => setWeights({ ...weights, strategy_aggressiveness: v })}
              />
              <Slider label="Grid weight" value={weights.grid_weight} onChange={(v) => setWeights({ ...weights, grid_weight: v })} />
            </div>
            <div className="space-y-4">
              <label className="block text-xs text-paper-dim">
                Weather
                <select
                  value={weather}
                  onChange={(e) => setWeather(e.target.value)}
                  className="mt-1 block w-full border border-graphite-700 bg-graphite-900 px-2 py-1.5 text-sm text-paper"
                >
                  <option value="dry">Dry</option>
                  <option value="wet">Wet</option>
                  <option value="mixed">Mixed</option>
                </select>
              </label>
              <button
                onClick={() => recomputeMutation.mutate()}
                disabled={recomputeMutation.isPending}
                className="w-full rounded bg-purple-fastest px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {recomputeMutation.isPending ? "Simulating…" : "Recompute prediction"}
              </button>
              <p className="text-xs text-paper-dim">
                Runs a fresh Monte Carlo simulation with these assumptions — doesn&apos;t affect the shared cached prediction.
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
