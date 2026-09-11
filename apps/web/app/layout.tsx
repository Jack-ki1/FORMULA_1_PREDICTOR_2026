import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "F1 Predictor",
  description: "Race-weekend predictions, standings, and a fantasy pick-em league for the 2026/2027 F1 seasons.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col bg-graphite-950 text-paper antialiased">
        <Providers>
          <Nav />
          <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
          <footer className="border-t border-graphite-700 px-4 py-6 text-center text-xs text-paper-dim">
            Predictions are model estimates, not betting advice. Data via Jolpica &amp; OpenF1.
          </footer>
        </Providers>
      </body>
    </html>
  );
}
