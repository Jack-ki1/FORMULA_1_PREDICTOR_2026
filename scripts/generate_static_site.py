"""
Static Site Generator for GitHub Pages — v2.

BUG FIXED vs v1:
  Line: `race["race"]["circuit"]` → KeyError every build because calendar
  entries have no nested "race" key. Fixed to `race["circuit"]`.

Generates:
  web/index.html            ← Full dashboard (standings, next race, calendar)
  web/predictions/*.json    ← One JSON file per circuit
  web/assets/data.json      ← All data in one payload for custom integrations

Usage:
  python scripts/generate_static_site.py
  python scripts/generate_static_site.py --sims 2000
  python scripts/generate_static_site.py --rain 0.60
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import argparse
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.progress import track

from engine.predictor import predict, PredictionRequest
from data.calendar_2026 import get_upcoming_races, CALENDAR_2026
from data.season_2026 import DRIVER_STANDINGS_AFTER_R4, CONSTRUCTOR_STANDINGS_AFTER_R4
from data.driver_data import DRIVERS

console = Console()

WEB_DIR  = Path(__file__).parent.parent / "web"
PRED_DIR = WEB_DIR / "predictions"

TEAM_COLOURS = {
    "mercedes": "#00D2BE", "mclaren": "#FF8000", "ferrari": "#E8002D",
    "red_bull": "#3671C6", "alpine": "#FF87BC", "williams": "#005AFF",
    "haas": "#B6BABD", "racing_bulls": "#6692FF", "audi": "#C00110",
    "aston_martin": "#358C75", "cadillac": "#BE3445",
}


def ensure_dirs():
    WEB_DIR.mkdir(exist_ok=True)
    PRED_DIR.mkdir(exist_ok=True)
    (WEB_DIR / "assets").mkdir(exist_ok=True)


def generate_predictions(sims: int = 2000, rain: float = None) -> dict:
    """Run predictions for every upcoming race that has circuit data."""
    upcoming = get_upcoming_races()
    all_predictions = {}

    for race in track(upcoming, description="Generating predictions…"):
        circuit_id = race["circuit"]           # BUG FIX: was race["race"]["circuit"]
        try:
            result = predict(PredictionRequest(
                circuit_id=circuit_id,
                rain_probability=rain,
                n_simulations=sims,
                output_format="summary",
            ))
            all_predictions[circuit_id] = {
                "race":         race,
                "prediction":   result,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
            with open(PRED_DIR / f"{circuit_id}.json", "w") as f:
                json.dump(all_predictions[circuit_id], f, indent=2)
            console.print(f"  [green]✓[/] {race['name']}")
        except KeyError as e:
            console.print(f"  [yellow]Skipped {circuit_id}[/] — {e}")

    return all_predictions


def save_aggregate_data(predictions: dict):
    """Write consolidated data.json for external integrations."""
    data = {
        "generated_at":        datetime.utcnow().isoformat() + "Z",
        "season":              2026,
        "driver_standings":    DRIVER_STANDINGS_AFTER_R4,
        "constructor_standings": CONSTRUCTOR_STANDINGS_AFTER_R4,
        "calendar":            CALENDAR_2026,
        "predictions":         {k: v["prediction"] for k, v in predictions.items()},
        "driver_profiles": {
            d_id: {
                "name":                 d["name"],
                "team":                 d["team"],
                "elo":                  d["elo"],
                "championship_points":  d["championship_points_2026"],
                "wins_2026":            d["wins_2026"],
            }
            for d_id, d in DRIVERS.items()
        },
    }
    out = WEB_DIR / "assets" / "data.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"[green]✓[/] Aggregate data.json → {out}")


def _standings_rows() -> str:
    rows = ""
    for s in DRIVER_STANDINGS_AFTER_R4[:10]:
        d = DRIVERS.get(s["driver"], {})
        colour = TEAM_COLOURS.get(d.get("team", ""), "#888")
        rows += (
            f'<tr><td class="pos">{s["position"]}</td>'
            f'<td><span class="dot" style="background:{colour}"></span>'
            f'{d.get("name", s["driver"])}</td>'
            f'<td class="pts">{s["points"]}</td></tr>'
        )
    return rows


def _pred_rows(next_pred: dict) -> str:
    if not next_pred:
        return ""
    rows = ""
    for p in next_pred.get("predictions", [])[:10]:
        colour = TEAM_COLOURS.get(p.get("team", ""), "#888")
        rows += (
            f'<tr><td class="pos">{p["predicted_position"]}</td>'
            f'<td><span class="dot" style="background:{colour}"></span>{p["driver"]}</td>'
            f'<td class="pts">{p["win_pct"]}%</td>'
            f'<td class="pts">{p["top3_pct"]}%</td>'
            f'<td class="pts">{p["dnf_pct"]}%</td></tr>'
        )
    return rows


def _calendar_rows() -> str:
    rows = ""
    for race in CALENDAR_2026:
        status_cls = "completed" if race["status"] == "completed" else ""
        sprint_tag = " ⚡" if race["sprint"] else ""
        done = "✓" if race["status"] == "completed" else "—"
        rows += (
            f'<tr class="{status_cls}"><td>{race["round"]}</td>'
            f'<td>{race["name"]}{sprint_tag}</td>'
            f'<td>{race["date"]}</td><td>{done}</td></tr>'
        )
    return rows


def write_index_html(predictions: dict):
    """Build the main index.html dashboard."""
    # First upcoming race
    next_race, next_pred = None, None
    for circuit_id, data in predictions.items():
        next_race = data["race"]
        next_pred = data["prediction"]
        break

    next_race_name = next_race["name"] if next_race else "TBC"
    next_race_date = next_race["date"] if next_race else "TBC"
    sprint_badge   = "<span class='badge'>⚡ Sprint</span>" if (next_race and next_race.get("sprint")) else ""
    sc_badge       = f"<span class='badge'>🚗 SC {int((next_pred['meta']['safety_car_probability'] if next_pred else 0)*100)}%</span>" if next_pred else ""
    rain_badge     = f"<span class='badge'>🌧 Rain {int((next_pred['meta']['rain_probability'] if next_pred else 0)*100)}%</span>" if next_pred else ""

    podium_html = ""
    if next_pred:
        medals = ["🥇","🥈","🥉"]
        for i, name in enumerate(next_pred.get("podium_predictions", [])[:3]):
            podium_html += f'<div class="podium-card"><div class="medal">{medals[i]}</div><div class="pname">{name}</div></div>'

    # Chart data (top 8 win probs)
    top8 = (next_pred.get("predictions", [])[:8]) if next_pred else []
    chart_labels  = json.dumps([p["driver"].split()[-1] for p in top8])
    chart_data    = json.dumps([p["win_pct"] for p in top8])
    chart_colours = json.dumps([TEAM_COLOURS.get(p.get("team",""),"#888") for p in top8])

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>F1 2026 Prediction System</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0d0f14;--surf:#13161f;--card:#191c28;--border:rgba(255,255,255,.07);
      --text:#e4e6f0;--muted:#7a7e96;--accent:#00D2BE;--faint:#3a3e52}}
body{{background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;font-size:14px;line-height:1.6}}
.container{{max-width:1100px;margin:0 auto;padding:2rem 1rem}}
header{{background:var(--surf);border-bottom:1px solid var(--border);padding:1rem 2rem;
        display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem}}
header h1{{font-size:18px;font-weight:600}}
header small{{color:var(--muted);font-size:12px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1.5rem 0}}
@media(max-width:680px){{.grid{{grid-template-columns:1fr}}}}
.card{{background:var(--surf);border:1px solid var(--border);border-radius:10px;padding:1.25rem}}
.card h2{{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
          color:var(--muted);margin-bottom:.875rem}}
.hero-card{{grid-column:1/-1;background:linear-gradient(135deg,#0b1220,#0d1626)}}
.hero-card h3{{font-size:20px;font-weight:600;margin-bottom:4px}}
.badges{{display:flex;gap:6px;flex-wrap:wrap;margin:.5rem 0}}
.badge{{font-size:11px;padding:3px 9px;border-radius:20px;background:rgba(255,255,255,.08)}}
.podium{{display:flex;gap:10px;margin-top:.875rem;flex-wrap:wrap}}
.podium-card{{background:rgba(255,255,255,.05);border-radius:8px;padding:8px 14px;flex:1;min-width:120px}}
.medal{{font-size:20px}}.pname{{font-weight:600;font-size:14px}}
table{{width:100%;border-collapse:collapse}}
thead th{{padding:8px;text-align:left;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border)}}
tbody tr{{border-bottom:1px solid var(--border);transition:background .12s}}
tbody tr:hover{{background:var(--card)}}
tbody tr.completed{{opacity:.45}}
tbody td{{padding:8px}}
.pos{{font-weight:600;color:var(--muted);width:28px}}
.pts{{text-align:right;font-variant-numeric:tabular-nums}}
.dot{{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px;vertical-align:middle}}
.chart-wrap{{height:200px;position:relative;margin-top:.5rem}}
footer{{text-align:center;color:var(--muted);font-size:12px;padding:2rem;
        border-top:1px solid var(--border);margin-top:2rem}}
footer a{{color:var(--muted)}}
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
    <p style="color:var(--muted)">{next_race_date}</p>
    <div class="badges">{sprint_badge}{sc_badge}{rain_badge}</div>
    <div class="podium">{podium_html}</div>
  </div>

  <div class="card">
    <h2>Driver Standings — Top 10</h2>
    <table>
      <thead><tr><th>P</th><th>Driver</th><th class="pts">Pts</th></tr></thead>
      <tbody>{_standings_rows()}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Prediction — {next_race_name}</h2>
    <table>
      <thead><tr><th>P</th><th>Driver</th><th class="pts">Win%</th><th class="pts">Top3%</th><th class="pts">DNF%</th></tr></thead>
      <tbody>{_pred_rows(next_pred)}</tbody>
    </table>
  </div>

  <div class="card" style="grid-column:1/-1">
    <h2>Win Probability — Top 8</h2>
    <div class="chart-wrap"><canvas id="wc" aria-label="Win probability chart"></canvas></div>
  </div>

  <div class="card" style="grid-column:1/-1">
    <h2>2026 Calendar</h2>
    <table>
      <thead><tr><th>#</th><th>Race</th><th>Date</th><th>Done</th></tr></thead>
      <tbody>{_calendar_rows()}</tbody>
    </table>
  </div>

</div>
</div>
<footer>
  F1 Prediction System · Pre-race data only · No post-race leakage<br>
  <a href="predictions/">JSON predictions</a> · <a href="assets/data.json">Full data export</a>
</footer>
<script>
const labels={chart_labels},data={chart_data},colours={chart_colours};
if(labels.length>0){{
  new Chart(document.getElementById('wc'),{{
    type:'bar',
    data:{{labels,datasets:[{{
      label:'Win %',data,
      backgroundColor:colours.map(c=>c+'BB'),
      borderColor:colours,borderWidth:1,borderRadius:4
    }}]}},
    options:{{
      responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}}},
      scales:{{
        x:{{ticks:{{color:'#7a7e96'}},grid:{{display:false}}}},
        y:{{ticks:{{color:'#7a7e96',callback:v=>v+'%'}},
           grid:{{color:'rgba(255,255,255,.05)'}},max:60}}
      }}
    }}
  }});
}}
</script>
</body>
</html>"""

    out = WEB_DIR / "index.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    console.print(f"[green]✓[/] index.html → {out}")


def main():
    parser = argparse.ArgumentParser(description="F1 static site generator")
    parser.add_argument("--sims", type=int, default=2000, help="Monte Carlo simulations per circuit")
    parser.add_argument("--rain", type=float, default=None, help="Rain probability override [0-1]")
    args = parser.parse_args()

    console.rule("[bold cyan]F1 Prediction System — Static Site Generator[/]")
    ensure_dirs()
    predictions = generate_predictions(sims=args.sims, rain=args.rain)
    save_aggregate_data(predictions)
    write_index_html(predictions)
    console.print(f"\n[bold green]✓ Site ready → {WEB_DIR}/[/]")
    console.print("[dim]Preview: cd web && python -m http.server 8080[/]\n")


if __name__ == "__main__":
    main()