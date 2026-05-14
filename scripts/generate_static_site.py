"""
Static Site Generator for GitHub Pages.

Runs predictions for all upcoming races and writes:
  web/index.html           ← Dashboard homepage
  web/predictions/*.json   ← One JSON file per circuit
  web/assets/data.json     ← Aggregate data for the JS dashboard

Usage:
  python scripts/generate_static_site.py
  python scripts/generate_static_site.py --sims 2000  # faster
  python scripts/generate_static_site.py --rain 0.4   # wet-race scenario
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import argparse
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import track

from engine.predictor import predict, PredictionRequest
from data.calendar_2026 import get_upcoming_races, get_completed_races, CALENDAR_2026
from data.season_2026 import DRIVER_STANDINGS_AFTER_R4, CONSTRUCTOR_STANDINGS_AFTER_R4
from data.driver_data import DRIVERS

console = Console()

WEB_DIR = Path(__file__).parent.parent / "web"
PRED_DIR = WEB_DIR / "predictions"


def ensure_dirs():
    WEB_DIR.mkdir(exist_ok=True)
    PRED_DIR.mkdir(exist_ok=True)
    (WEB_DIR / "assets").mkdir(exist_ok=True)


def generate_predictions(sims: int = 2000, rain: float = None) -> dict:
    """Run predictions for all circuits that have data."""
    upcoming = get_upcoming_races()
    all_predictions = {}

    for race in track(upcoming, description="Generating predictions…"):
        circuit_id = race["circuit"]
        try:
            result = predict(PredictionRequest(
                circuit_id=circuit_id,
                rain_probability=rain,
                n_simulations=sims,
                output_format="summary",
            ))
            all_predictions[circuit_id] = {
                "race": race,
                "prediction": result,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
            # Save individual JSON
            with open(PRED_DIR / f"{circuit_id}.json", "w") as f:
                json.dump(all_predictions[circuit_id], f, indent=2)
        except KeyError:
            console.print(f"[yellow]Skipping {circuit_id} — circuit not yet in database[/]")

    return all_predictions


def save_aggregate_data(predictions: dict):
    """Write consolidated data.json for the JS dashboard."""
    data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "season": 2026,
        "driver_standings": DRIVER_STANDINGS_AFTER_R4,
        "constructor_standings": CONSTRUCTOR_STANDINGS_AFTER_R4,
        "calendar": CALENDAR_2026,
        "predictions": {k: v["prediction"] for k, v in predictions.items()},
        "driver_profiles": {
            d_id: {
                "name": d["name"], "team": d["team"],
                "elo": d["elo"], "championship_points": d["championship_points_2026"],
                "wins_2026": d["wins_2026"],
            }
            for d_id, d in DRIVERS.items()
        }
    }
    with open(WEB_DIR / "assets" / "data.json", "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"[green]✓ Aggregate data.json written[/]")


def write_index_html(predictions: dict):
    """Generate the main index.html for GitHub Pages."""
    next_race = None
    next_pred = None
    for race_id, pred_data in predictions.items():
        next_race = pred_data["race"]
        next_pred = pred_data["prediction"]
        break  # First upcoming race

    team_colours = {
        "mercedes": "#00D2BE", "mclaren": "#FF8000", "ferrari": "#E8002D",
        "red_bull": "#3671C6", "alpine": "#FF87BC", "williams": "#005AFF",
        "haas": "#B6BABD", "racing_bulls": "#6692FF", "audi": "#C00110",
        "aston_martin": "#358C75", "cadillac": "#BE3445",
    }

    standings_rows = ""
    for s in DRIVER_STANDINGS_AFTER_R4[:10]:
        d = DRIVERS.get(s["driver"], {})
        name = d.get("name", s["driver"])
        team = d.get("team", "")
        colour = team_colours.get(team, "#888")
        standings_rows += f"""
        <tr>
          <td class="pos">{s['position']}</td>
          <td><span class="dot" style="background:{colour}"></span>{name}</td>
          <td class="pts">{s['points']}</td>
        </tr>"""

    pred_rows = ""
    if next_pred:
        for p in next_pred.get("predictions", [])[:10]:
            colour = team_colours.get(p.get("team", ""), "#888")
            pred_rows += f"""
        <tr>
          <td class="pos">{p['predicted_position']}</td>
          <td><span class="dot" style="background:{colour}"></span>{p['driver']}</td>
          <td class="pts">{p['win_pct']}%</td>
          <td class="pts">{p['top3_pct']}%</td>
          <td class="pts">{p['dnf_pct']}%</td>
        </tr>"""

    next_race_name = next_race["name"] if next_race else "TBC"
    next_race_date = next_race["date"] if next_race else "TBC"
    podium_html = ""
    if next_pred:
        medals = ["🥇", "🥈", "🥉"]
        for i, name in enumerate(next_pred.get("podium_predictions", [])[:3]):
            podium_html += f'<div class="podium-card"><div class="medal">{medals[i]}</div><div class="pname">{name}</div></div>'

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    calendar_rows = ""
    for race in CALENDAR_2026:
        status_cls = "completed" if race["status"] == "completed" else "upcoming" if race["race"]["circuit"] == (next_race["circuit"] if next_race else "") else ""
        sprint_tag = " ⚡" if race["sprint"] else ""
        calendar_rows += f'<tr class="{status_cls}"><td>{race["round"]}</td><td>{race["name"]}{sprint_tag}</td><td>{race["date"]}</td><td>{"✓" if race["status"] == "completed" else "—"}</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>F1 2026 Prediction System</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0f1117;--surf:#1a1d27;--card:#1e2130;--border:rgba(255,255,255,.08);--text:#e8eaf0;--muted:#8b8fa8;--accent:#00D2BE}}
body{{background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;font-size:14px;line-height:1.6}}
.container{{max-width:1100px;margin:0 auto;padding:2rem 1rem}}
header{{background:var(--surf);border-bottom:1px solid var(--border);padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center}}
header h1{{font-size:20px;font-weight:600}}
header small{{color:var(--muted);font-size:12px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1.5rem 0}}
@media(max-width:700px){{.grid{{grid-template-columns:1fr}}}}
.card{{background:var(--surf);border:1px solid var(--border);border-radius:10px;padding:1.25rem}}
.card h2{{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:1rem}}
.hero-card{{grid-column:1/-1;background:linear-gradient(135deg,#0d1f2d,#1a1d27)}}
.hero-card h3{{font-size:22px;font-weight:600;margin-bottom:4px}}
.hero-card p{{color:var(--muted)}}
.badges{{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}}
.badge{{font-size:11px;padding:3px 10px;border-radius:20px;background:rgba(255,255,255,.1)}}
.podium{{display:flex;gap:10px;margin-top:1rem;flex-wrap:wrap}}
.podium-card{{background:rgba(255,255,255,.05);border-radius:8px;padding:8px 14px;flex:1;min-width:120px}}
.medal{{font-size:20px}}
.pname{{font-weight:600}}
table{{width:100%;border-collapse:collapse}}
thead th{{padding:8px;text-align:left;font-size:12px;color:var(--muted);border-bottom:1px solid var(--border)}}
tbody tr{{border-bottom:1px solid var(--border)}}
tbody tr.completed{{opacity:.5}}
tbody td{{padding:8px}}
.pos{{font-weight:600;color:var(--muted);width:32px}}
.pts{{text-align:right;font-variant-numeric:tabular-nums}}
.dot{{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px}}
.chart-wrap{{height:200px;position:relative;margin-top:.5rem}}
footer{{text-align:center;color:var(--muted);font-size:12px;padding:2rem;border-top:1px solid var(--border);margin-top:2rem}}
</style>
</head>
<body>
<header>
  <h1>🏁 F1 2026 Prediction System</h1>
  <small>Updated: {generated_at}</small>
</header>
<div class="container">

  <div class="grid">

    <div class="card hero-card">
      <h2>Next Race</h2>
      <h3>{next_race_name}</h3>
      <p>{next_race_date}</p>
      <div class="badges">
        {"<span class='badge'>⚡ Sprint Weekend</span>" if next_race and next_race.get('sprint') else ""}
        {"<span class='badge'>🎲 SC Prob: " + str(int((next_pred['meta']['safety_car_probability'] if next_pred else 0)*100)) + "%</span>" if next_pred else ""}
        {"<span class='badge'>🌧 Rain: " + str(int((next_pred['meta']['rain_probability'] if next_pred else 0)*100)) + "%</span>" if next_pred else ""}
      </div>
      <div class="podium">{podium_html}</div>
    </div>

    <div class="card">
      <h2>Driver Standings (Top 10)</h2>
      <table>
        <thead><tr><th>P</th><th>Driver</th><th class="pts">Pts</th></tr></thead>
        <tbody>{standings_rows}</tbody>
      </table>
    </div>

    <div class="card">
      <h2>Race Prediction — {next_race_name}</h2>
      <table>
        <thead><tr><th>P</th><th>Driver</th><th class="pts">Win%</th><th class="pts">Top3%</th><th class="pts">DNF%</th></tr></thead>
        <tbody>{pred_rows}</tbody>
      </table>
    </div>

    <div class="card" style="grid-column:1/-1">
      <h2>Win Probability — Top 8</h2>
      <div class="chart-wrap"><canvas id="wc" aria-label="Win probability chart for top 8 drivers"></canvas></div>
    </div>

    <div class="card" style="grid-column:1/-1">
      <h2>2026 Calendar</h2>
      <table>
        <thead><tr><th>#</th><th>Race</th><th>Date</th><th>Done</th></tr></thead>
        <tbody>{calendar_rows}</tbody>
      </table>
    </div>

  </div>
</div>

<footer>
  F1 Prediction System · Pre-race data only · No post-race leakage<br>
  <a href="predictions/" style="color:var(--muted)">Raw JSON predictions</a> ·
  <a href="assets/data.json" style="color:var(--muted)">Full data export</a>
</footer>

<script>
const preds = {json.dumps([p for p in (next_pred.get('predictions', [])[:8] if next_pred else [])])};
const colours = {json.dumps([{"mercedes":"#00D2BE","mclaren":"#FF8000","ferrari":"#E8002D","red_bull":"#3671C6","alpine":"#FF87BC","williams":"#005AFF","haas":"#B6BABD","racing_bulls":"#6692FF","audi":"#C00110","aston_martin":"#358C75","cadillac":"#BE3445"}.get(p.get("team",""),"#888") for p in (next_pred.get("predictions", [])[:8] if next_pred else [])])};
if(preds.length > 0) {{
  new Chart(document.getElementById('wc'), {{
    type: 'bar',
    data: {{
      labels: preds.map(p => p.driver.split(' ').pop()),
      datasets: [{{
        label: 'Win %',
        data: preds.map(p => p.win_pct),
        backgroundColor: colours.map(c => c + 'BB'),
        borderColor: colours,
        borderWidth: 1,
        borderRadius: 4,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8b8fa8' }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#8b8fa8', callback: v => v + '%' }},
             grid: {{ color: 'rgba(255,255,255,0.05)' }}, max: 60 }}
      }}
    }}
  }});
}}
</script>
</body>
</html>"""

    with open(WEB_DIR / "index.html", "w") as f:
        f.write(html)
    console.print(f"[green]✓ index.html written → {WEB_DIR / 'index.html'}[/]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=2000)
    parser.add_argument("--rain", type=float, default=None)
    args = parser.parse_args()

    console.rule("[bold cyan]F1 Prediction System — Static Site Generator[/]")
    ensure_dirs()
    predictions = generate_predictions(sims=args.sims, rain=args.rain)
    save_aggregate_data(predictions)
    write_index_html(predictions)
    console.print(f"\n[bold green]✓ Static site generated → {WEB_DIR}/[/]")
    console.print("[dim]Preview: cd web && python -m http.server 8080[/]\n")


if __name__ == "__main__":
    main()
