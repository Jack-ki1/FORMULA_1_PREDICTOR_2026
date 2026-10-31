import { Card } from "../components/ui";

const Q = (t: string, d: string) => <div className="border-t border-edge py-3 first:border-0"><dt className="text-[13px] font-semibold">{t}</dt><dd className="mt-1 text-[12px] leading-relaxed text-slate-300">{d}</dd></div>;

export default function Guide() {
  return (
    <div className="mx-auto max-w-3xl space-y-3 p-3.5">
      <h1 className="text-[20px] font-extrabold">Guide</h1>
      <Card className="p-4"><h2 className="mb-2 text-[14px] font-bold">Using the Dashboard</h2><dl>
        {Q("Pick a Grand Prix", "Every round of the 2026 season is listed. Race, session and weather changes apply instantly. Grid edits and engine tweaks apply when you press Run Prediction.")}
        {Q("Sessions", "Practice shows each driver's projected pace spread. Qualifying simulates Q1 → Q2 → Q3 elimination. Race and Sprint run the full weekend model, including safety cars and retirements.")}
        {Q("Starting grid", "Auto-fetched uses published qualifying results when available. Manual lets you pin any P slots; the rest are filled by simulated qualifying. Auto-fill (by Form) ranks drivers by their current rating; Reverse flips the grid.")}
        {Q("Race-day tuning", "Each circuit has its own overtaking difficulty, tyre wear and safety-car likelihood, so the same drivers get different predictions at Monaco and Monza. Weather can follow the live forecast (Auto) or be forced Dry, Mixed or Wet.")}
      </dl></Card>
      <Card className="p-4"><h2 className="mb-2 text-[14px] font-bold">How the engine works</h2><dl>
        {Q("Ratings", "A blend of car pace, driver skill and (optionally) season form from current points per round. These are model priors, editable in the backend seed file.")}
        {Q("Monte Carlo", "Thousands of simulated weekends are run. Probabilities are simply how often something happened (a win, a podium, a retirement). Win probabilities show a confidence interval you can set to 90, 95 or 99%.")}
        {Q("Confidence", "Combines how decisive the win distribution is, the number of simulations, weather uncertainty and the chaos setting. It measures the model's certainty, not real-world accuracy.")}
        {Q("Settings", "Every control in Settings is sent to the engine with each prediction, so changes are visible immediately on the Dashboard.")}
      </dl></Card>
      <Card className="p-4 text-[11px] text-mute">Unofficial fan project, not affiliated with Formula 1, the FIA or any team. Predictions are probabilities, not betting advice.</Card>
    </div>
  );
}
