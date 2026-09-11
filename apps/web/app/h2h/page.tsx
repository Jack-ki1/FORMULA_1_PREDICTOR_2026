"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export default function H2HPage() {
  const driversQuery = useQuery({ queryKey: ["h2h-drivers"], queryFn: api.h2hDrivers });
  const [driverA, setDriverA] = useState("");
  const [driverB, setDriverB] = useState("");

  const compareMutation = useMutation({
    mutationFn: () => api.h2hCompare(driverA, driverB),
  });

  const drivers = driversQuery.data ?? [];
  const result = compareMutation.data;

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-2xl font-medium">Head to head</h1>
      <div className="flex items-center gap-3">
        <select
          value={driverA}
          onChange={(e) => setDriverA(e.target.value)}
          className="flex-1 border border-graphite-700 bg-graphite-900 px-3 py-2 text-sm"
        >
          <option value="">Driver A</option>
          {drivers.map((d) => (
            <option key={d.code} value={d.code}>
              {d.name}
            </option>
          ))}
        </select>
        <span className="text-paper-dim">vs</span>
        <select
          value={driverB}
          onChange={(e) => setDriverB(e.target.value)}
          className="flex-1 border border-graphite-700 bg-graphite-900 px-3 py-2 text-sm"
        >
          <option value="">Driver B</option>
          {drivers.map((d) => (
            <option key={d.code} value={d.code}>
              {d.name}
            </option>
          ))}
        </select>
      </div>
      <button
        onClick={() => compareMutation.mutate()}
        disabled={!driverA || !driverB || compareMutation.isPending}
        className="rounded bg-paper px-4 py-2 text-sm font-medium text-graphite-950 disabled:opacity-40"
      >
        Compare
      </button>

      {result && (
        <div className="space-y-3 border border-graphite-700 p-4">
          <div className="flex items-center justify-between text-sm">
            <span style={{ color: result.driver_a.team_color }}>{result.driver_a.name}</span>
            <span style={{ color: result.driver_b.team_color }}>{result.driver_b.name}</span>
          </div>
          <div className="flex h-8 overflow-hidden rounded-sm">
            <div
              style={{ width: `${result.win_probability * 100}%`, backgroundColor: result.driver_a.team_color }}
            />
            <div
              style={{ width: `${result.reverse_probability * 100}%`, backgroundColor: result.driver_b.team_color }}
            />
          </div>
          <div className="flex justify-between text-sm tabular text-paper-dim">
            <span>{(result.win_probability * 100).toFixed(1)}%</span>
            <span>{(result.reverse_probability * 100).toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
