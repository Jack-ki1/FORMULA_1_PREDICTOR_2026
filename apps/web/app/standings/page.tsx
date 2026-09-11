"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

interface DriverStandingRow {
  position: number;
  driver_code: string;
  driver_name: string;
  team: string;
  points: number;
  wins?: number;
}

interface ConstructorStandingRow {
  position: number;
  team: string;
  points: number;
  wins?: number;
}

export default function StandingsPage() {
  const [view, setView] = useState<"drivers" | "constructors">("drivers");

  const driversQuery = useQuery({ queryKey: ["standings-drivers"], queryFn: api.standingsDrivers, enabled: view === "drivers" });
  const constructorsQuery = useQuery({
    queryKey: ["standings-constructors"],
    queryFn: api.standingsConstructors,
    enabled: view === "constructors",
  });

  const driverRows = (driversQuery.data?.data ?? []) as DriverStandingRow[];
  const constructorRows = (constructorsQuery.data?.data ?? []) as ConstructorStandingRow[];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-medium">Standings</h1>
        <div className="flex gap-1 border border-graphite-700 p-1">
          {(["drivers", "constructors"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1.5 text-sm capitalize ${view === v ? "bg-graphite-700" : "text-paper-dim hover:text-paper"}`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {view === "drivers" ? (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-graphite-700 text-left text-paper-dim">
              <th className="py-2 font-normal">#</th>
              <th className="py-2 font-normal">Driver</th>
              <th className="py-2 font-normal">Team</th>
              <th className="py-2 text-right font-normal">Points</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-graphite-800">
            {driverRows.map((row) => (
              <tr key={row.driver_code}>
                <td className="py-2 tabular text-paper-dim">{row.position}</td>
                <td className="py-2">{row.driver_name ?? row.driver_code}</td>
                <td className="py-2 text-paper-dim">{row.team}</td>
                <td className="py-2 text-right tabular">{row.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-graphite-700 text-left text-paper-dim">
              <th className="py-2 font-normal">#</th>
              <th className="py-2 font-normal">Team</th>
              <th className="py-2 text-right font-normal">Points</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-graphite-800">
            {constructorRows.map((row) => (
              <tr key={row.team}>
                <td className="py-2 tabular text-paper-dim">{row.position}</td>
                <td className="py-2">{row.team}</td>
                <td className="py-2 text-right tabular">{row.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
