"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export default function LeaderboardPage() {
  const { data } = useQuery({ queryKey: ["leaderboard"], queryFn: api.leaderboard });
  const rows = data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium">Leaderboard</h1>
        <p className="mt-1 text-sm text-paper-dim">
          Pick a driver each race weekend — score based on how they actually finish.
        </p>
      </div>
      {rows.length === 0 ? (
        <p className="text-paper-dim">No picks scored yet this season.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-graphite-700 text-left text-paper-dim">
              <th className="py-2 font-normal">#</th>
              <th className="py-2 font-normal">Player</th>
              <th className="py-2 text-right font-normal">Picks</th>
              <th className="py-2 text-right font-normal">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-graphite-800">
            {rows.map((row) => (
              <tr key={row.rank}>
                <td className="py-2 tabular text-paper-dim">{row.rank}</td>
                <td className="py-2">{row.display_name}</td>
                <td className="py-2 text-right tabular text-paper-dim">
                  {row.picks_resolved}/{row.picks_made}
                </td>
                <td className="py-2 text-right tabular font-medium">{row.total_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
