import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import App from "../App";
import { applyAppearance } from "../lib/appearance";
import { DEFAULT_SETTINGS, useApp } from "../lib/store";

afterEach(() => { cleanup(); useApp.getState().resetAll(); });
const mount = (path: string) =>
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[path]}><App /></MemoryRouter>
    </QueryClientProvider>,
  );

describe("pages render against the live API", () => {
  it("dashboard: control center, panels and visuals", async () => {
    mount("/dashboard");
    expect(await screen.findByText("Select a Grand Prix")).toBeTruthy();
    expect(await screen.findByText("Race weekend status")).toBeTruthy();
    expect(await screen.findByText("Select race weekend session")).toBeTruthy();
    expect(await screen.findByText("Starting Grid")).toBeTruthy();
    expect(await screen.findByText("Winner prediction")).toBeTruthy();
    expect(await screen.findByText("Finishing Position Probability")).toBeTruthy();
    expect(await screen.findByText("Constructor Battle")).toBeTruthy();
    expect(await screen.findByText("Grid → Predicted Finish")).toBeTruthy();
    expect(await screen.findByText("Predicted Race Results")).toBeTruthy();
    expect(await screen.findByText("Export this prediction")).toBeTruthy();
  });
  it("manual grid: pin a driver, run, and the grid source updates", async () => {
    mount("/dashboard");
    fireEvent.click(await screen.findByText("Manual Grid", { selector: "button" }));
    const p1 = (await screen.findByLabelText("Grid position P1")) as HTMLSelectElement;
    await waitFor(() => expect(p1.options.length).toBeGreaterThan(20));
    fireEvent.change(p1, { target: { value: "HAM" } });
    fireEvent.click(await screen.findByText("Run Prediction"));
    expect(await screen.findByText(/manual \(1 pinned\)/, {}, { timeout: 6000 })).toBeTruthy();
  });
  it("switching session swaps the visuals", async () => {
    mount("/dashboard");
    fireEvent.click(await screen.findByText(/Saturday Qualifying|Friday Qualifying|Qualifying$/, { selector: "span" }));
    expect(await screen.findByText("Q1 → Q2 → Q3 Advancement")).toBeTruthy();
  });
  it("other pages", async () => {
    mount("/predictions"); expect(await screen.findByText("Kimi Antonelli")).toBeTruthy(); cleanup();
    mount("/standings"); expect(await screen.findByText("Kimi Antonelli")).toBeTruthy(); cleanup();
    mount("/head2head?a=VER&b=NOR"); expect(await screen.findByText("Season points")).toBeTruthy(); cleanup();
    mount("/fantasy"); expect(await screen.findByText("Auto-pick best team")).toBeTruthy(); cleanup();
    mount("/guide"); expect(await screen.findByText("How the engine works")).toBeTruthy();
  });
  it("settings: all eleven sections render and controls change the store", async () => {
    mount("/settings");
    for (const t of ["Appearance", "Accessibility", "Prediction Engine Defaults", "Backend Configuration", "Reference Parameters", "Dashboard Layout", "Notifications", "Profile", "Advanced", "Keyboard Shortcuts", "Data & Privacy"])
      expect((await screen.findAllByText(t)).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByText("Light"));
    expect(useApp.getState().s.mode).toBe("light");
    fireEvent.click(screen.getByLabelText("High contrast"));
    expect(useApp.getState().s.highContrast).toBe(true);
    applyAppearance(useApp.getState().s);
    expect(document.documentElement.dataset.hc).toBe("true");
    expect(document.documentElement.dataset.mode).toBe("light");
    applyAppearance(DEFAULT_SETTINGS);
  });
  it("landing page setting redirects the index route", async () => {
    useApp.getState().set({ landing: "standings" });
    mount("/");
    expect(await screen.findByText("2026 Championship Standings")).toBeTruthy();
  });
});
