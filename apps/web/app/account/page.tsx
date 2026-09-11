"use client";

import { useState } from "react";
import { useSession, signIn, signOut } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export default function AccountPage() {
  const { data: session, status } = useSession();
  const [devName, setDevName] = useState("");

  const picksQuery = useQuery({
    queryKey: ["my-picks", session?.apiToken],
    queryFn: () => api.myPicks(session!.apiToken!),
    enabled: !!session?.apiToken,
  });

  if (status === "loading") return null;

  if (status !== "authenticated") {
    return (
      <div className="max-w-sm space-y-6">
        <h1 className="text-2xl font-medium">Sign in</h1>
        <button
          onClick={() => signIn("github")}
          className="w-full rounded bg-paper px-4 py-2 text-sm font-medium text-graphite-950"
        >
          Continue with GitHub
        </button>

        {process.env.NODE_ENV !== "production" && (
          <div className="border-t border-graphite-700 pt-4">
            <p className="mb-2 text-xs text-paper-dim">Dev mode — no OAuth app configured yet:</p>
            <div className="flex gap-2">
              <input
                value={devName}
                onChange={(e) => setDevName(e.target.value)}
                placeholder="Display name"
                className="flex-1 border border-graphite-700 bg-graphite-900 px-3 py-2 text-sm"
              />
              <button
                onClick={() => signIn("dev-login", { name: devName || "Dev User" })}
                className="rounded border border-graphite-700 px-3 py-2 text-sm"
              >
                Dev sign in
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-xl space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium">{session.user?.name}</h1>
          <p className="text-sm text-paper-dim">{session.user?.email}</p>
        </div>
        <button onClick={() => signOut()} className="text-sm text-paper-dim underline hover:text-paper">
          Sign out
        </button>
      </div>

      <section>
        <h2 className="mb-3 text-lg font-medium">Your picks</h2>
        {picksQuery.data && picksQuery.data.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-graphite-700 text-left text-paper-dim">
                <th className="py-2 font-normal">Race</th>
                <th className="py-2 font-normal">Target</th>
                <th className="py-2 font-normal">Pick</th>
                <th className="py-2 font-normal">Status</th>
                <th className="py-2 text-right font-normal">Points</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-graphite-800">
              {picksQuery.data.map((pick) => (
                <tr key={pick.id}>
                  <td className="py-2">{pick.race_id}</td>
                  <td className="py-2 text-paper-dim">{pick.target.replace("_", " ")}</td>
                  <td className="py-2 tabular">{pick.driver_id}</td>
                  <td className="py-2 text-paper-dim">{pick.status}</td>
                  <td className="py-2 text-right tabular">{pick.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-paper-dim">
            No picks yet — head to a race&apos;s predictions page and make one before it starts.
          </p>
        )}
      </section>
    </div>
  );
}
