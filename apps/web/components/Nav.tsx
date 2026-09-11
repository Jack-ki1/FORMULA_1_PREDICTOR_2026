"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signIn, signOut } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import clsx from "clsx";

const LINKS = [
  { href: "/predictions", label: "Predictions" },
  { href: "/standings", label: "Standings" },
  { href: "/h2h", label: "H2H" },
  { href: "/constructors", label: "Constructors" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/settings", label: "Model tuning" },
];

function StatusStrip() {
  const { data } = useQuery({ queryKey: ["status"], queryFn: api.status, retry: false });

  const minutes = data?.minutes_since_last_sync;
  const label =
    minutes == null
      ? "data not yet synced"
      : minutes < 1
        ? "synced just now"
        : minutes < 60
          ? `synced ${Math.round(minutes)}m ago`
          : `synced ${Math.round(minutes / 60)}h ago`;

  return (
    <div className="border-b border-graphite-700 bg-graphite-950 px-4 py-1.5 text-xs text-paper-dim">
      <div className="mx-auto flex max-w-6xl items-center gap-2">
        <span
          className={clsx(
            "h-1.5 w-1.5 rounded-full",
            minutes != null && minutes < 120 ? "bg-green-go" : "bg-amber-flag"
          )}
        />
        <span className="tabular">{label}</span>
      </div>
    </div>
  );
}

export function Nav() {
  const pathname = usePathname();
  const { data: session, status } = useSession();

  return (
    <header className="sticky top-0 z-20">
      <StatusStrip />
      <div className="border-b border-graphite-700 bg-graphite-900/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/" className="text-lg font-semibold tracking-tight text-paper">
            F1 Predictor
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "rounded px-3 py-1.5 text-sm transition-colors",
                  pathname?.startsWith(link.href)
                    ? "bg-graphite-700 text-paper"
                    : "text-paper-dim hover:bg-graphite-800 hover:text-paper"
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            {status === "authenticated" ? (
              <Link href="/account" className="text-sm text-paper-dim hover:text-paper">
                {session.user?.name ?? "Account"}
              </Link>
            ) : (
              <button
                onClick={() => signIn()}
                className="rounded bg-paper px-3 py-1.5 text-sm font-medium text-graphite-950 hover:bg-white"
              >
                Sign in
              </button>
            )}
            {status === "authenticated" && (
              <button onClick={() => signOut()} className="text-sm text-paper-dim hover:text-paper">
                Sign out
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
