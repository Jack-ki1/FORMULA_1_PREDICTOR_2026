import Link from "next/link";
import { api } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let races: Awaited<ReturnType<typeof api.races>> = [];
  let loadError = false;
  try {
    races = await api.races();
  } catch {
    loadError = true;
  }

  const nextRace = races.find((r) => r.status === "upcoming");
  const recentlyCompleted = [...races].reverse().find((r) => r.status === "completed");

  return (
    <div className="space-y-12">
      <section className="border-b border-graphite-700 pb-10">
        <p className="text-sm text-paper-dim">Next on the calendar</p>
        {nextRace ? (
          <>
            <h1 className="mt-2 text-4xl font-medium tracking-tight text-paper md:text-5xl">
              {nextRace.flag} {nextRace.name}
            </h1>
            <p className="mt-2 text-paper-dim">
              {nextRace.circuit}, {nextRace.location} · {nextRace.date} · Round {nextRace.round}
            </p>
            <Link
              href={`/predictions/${nextRace.id}`}
              className="mt-6 inline-block rounded bg-paper px-4 py-2 text-sm font-medium text-graphite-950 hover:bg-white"
            >
              View predictions
            </Link>
          </>
        ) : (
          <h1 className="mt-2 text-3xl font-medium text-paper">Season complete</h1>
        )}
      </section>

      {loadError && (
        <p className="rounded border border-red-flag/40 bg-red-flag/10 px-4 py-3 text-sm text-red-flag">
          Couldn&apos;t reach the prediction API. Is it running at{" "}
          <code className="font-mono">NEXT_PUBLIC_API_URL</code>?
        </p>
      )}

      {recentlyCompleted && (
        <section>
          <p className="text-sm text-paper-dim">Most recent result</p>
          <Link
            href={`/predictions/${recentlyCompleted.id}`}
            className="mt-2 flex items-center justify-between border border-graphite-700 px-4 py-3 hover:bg-graphite-900"
          >
            <span>
              {recentlyCompleted.flag} {recentlyCompleted.name}
            </span>
            <span className="text-sm text-paper-dim">Round {recentlyCompleted.round}</span>
          </Link>
        </section>
      )}

      <section>
        <p className="mb-3 text-sm text-paper-dim">2026 calendar</p>
        <div className="divide-y divide-graphite-800 border-y border-graphite-800">
          {races.map((race) => (
            <Link
              key={race.id}
              href={`/predictions/${race.id}`}
              className="flex items-center justify-between px-2 py-2.5 text-sm hover:bg-graphite-900"
            >
              <span className="flex items-center gap-3">
                <span className="w-6 tabular text-paper-dim">{String(race.round).padStart(2, "0")}</span>
                <span>
                  {race.flag} {race.name}
                </span>
                {race.sprint && (
                  <span className="rounded bg-graphite-700 px-1.5 py-0.5 text-[10px] text-paper-dim">SPRINT</span>
                )}
              </span>
              <span className="flex items-center gap-3 text-paper-dim">
                <span>{race.date}</span>
                <span
                  className={
                    race.status === "completed"
                      ? "text-paper-dim"
                      : race.status === "upcoming"
                        ? "text-green-go"
                        : "text-paper-dim"
                  }
                >
                  {race.status}
                </span>
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
