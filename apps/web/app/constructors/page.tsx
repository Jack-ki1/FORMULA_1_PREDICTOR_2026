"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type TeamInfo } from "@/lib/api-client";

export default function ConstructorsPage() {
  const teamsQuery = useQuery({ queryKey: ["teams"], queryFn: api.teams });
  const teams = (teamsQuery.data ?? []) as TeamInfo[];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-medium">Constructors</h1>
      <div className="grid gap-3 sm:grid-cols-2">
        {teams.map((team) => (
          <div key={team.id} className="flex items-center gap-3 border border-graphite-700 p-4">
            <span className="h-8 w-1.5 shrink-0" style={{ backgroundColor: team.color }} />
            <span className="font-medium">{team.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
