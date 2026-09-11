"use client";

import { useState } from "react";
import { useSession, signIn } from "next-auth/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type FeatureWeights } from "@/lib/api-client";
import { Slider } from "@/components/Slider";

const DEFAULTS: Omit<FeatureWeights, "scope"> = {
  chaos_level: 50,
  wet_influence: 50,
  reliability_influence: 50,
  strategy_aggressiveness: 50,
  grid_weight: 55,
};

export default function SettingsPage() {
  const { data: session, status } = useSession();
  const queryClient = useQueryClient();
  // Only holds fields the user has actually touched this session — the
  // saved/default values from the server are the source of truth
  // otherwise, so there's no server-state-into-local-state sync to do.
  const [overrides, setOverrides] = useState<Partial<Omit<FeatureWeights, "scope">>>({});
  const [saved, setSaved] = useState(false);

  const weightsQuery = useQuery({
    queryKey: ["feature-weights", session?.apiToken],
    queryFn: () => api.featureWeights(session?.apiToken),
    enabled: status !== "loading",
  });

  const weights = { ...DEFAULTS, ...weightsQuery.data, ...overrides };

  const saveMutation = useMutation({
    mutationFn: () => {
      const { scope: _scope, ...rest } = weights;
      void _scope;
      return api.saveFeatureWeights(rest, session?.apiToken);
    },
    onSuccess: () => {
      setSaved(true);
      setOverrides({});
      queryClient.invalidateQueries({ queryKey: ["feature-weights"] });
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const update = (field: keyof typeof DEFAULTS, value: number) => setOverrides((o) => ({ ...o, [field]: value }));

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-medium">Model tuning</h1>
        <p className="mt-1 text-sm text-paper-dim">
          These weights feed the Monte Carlo simulation on every prediction page.
          {status !== "authenticated" && " Sign in to save your own instead of the defaults."}
        </p>
      </div>

      {status !== "authenticated" && (
        <button onClick={() => signIn()} className="rounded bg-paper px-4 py-2 text-sm font-medium text-graphite-950">
          Sign in to save settings
        </button>
      )}

      <div className="space-y-4 border border-graphite-700 p-4">
        <Slider label="Chaos" value={weights.chaos_level} onChange={(v) => update("chaos_level", v)} />
        <Slider label="Wet-weather influence" value={weights.wet_influence} onChange={(v) => update("wet_influence", v)} />
        <Slider
          label="Reliability influence"
          value={weights.reliability_influence}
          onChange={(v) => update("reliability_influence", v)}
        />
        <Slider
          label="Strategy aggressiveness"
          value={weights.strategy_aggressiveness}
          onChange={(v) => update("strategy_aggressiveness", v)}
        />
        <Slider label="Grid weight" value={weights.grid_weight} onChange={(v) => update("grid_weight", v)} />
      </div>

      <button
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending}
        className="rounded bg-purple-fastest px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {saved ? "Saved" : saveMutation.isPending ? "Saving…" : "Save"}
      </button>
    </div>
  );
}
