"""
One-shot script: Run the full 2026 Canadian Grand Prix prediction.

Usage:
  python scripts/run_canada_gp_2026.py
  python scripts/run_canada_gp_2026.py --rain 0.55   # wet race scenario
  python scripts/run_canada_gp_2026.py --sims 10000  # more simulations
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from engine.predictor import predict, PredictionRequest
from reports.html_report import generate_report

console = Console()


def run(rain: float = None, sims: int = 5000, save_report: bool = True):
    console.rule("[bold red]F1 2026 CANADIAN GRAND PRIX — PREDICTION[/]")
    console.print()

    with console.status(f"[cyan]Running {sims:,} Monte Carlo simulations…[/]"):
        result = predict(PredictionRequest(
            circuit_id="canada",
            rain_probability=rain,
            n_simulations=sims,
        ))

    meta = result["meta"]

    console.print(Panel(
        f"[bold white]{meta['circuit']}[/] · {meta['city']} · {meta['race_date']}\n"
        f"Sprint weekend: [{'green]YES' if meta['sprint_weekend'] else 'red]NO'}[/]\n"
        f"Safety Car prob: [yellow]{meta['safety_car_probability']*100:.0f}%[/]  "
        f"Rain: [blue]{meta['rain_probability']*100:.0f}%[/]  "
        f"Model confidence: [green]{meta['overall_model_confidence']*100:.0f}%[/]",
        title="[bold cyan]CIRCUIT GILLES-VILLENEUVE[/]",
        border_style="cyan",
    ))

    # Podium
    podium = result["podium_predictions"]
    medals = ["🥇", "🥈", "🥉"]
    console.print(f"\n[bold]PREDICTED PODIUM:[/]")
    for i, name in enumerate(podium):
        console.print(f"  {medals[i]}  {name}")

    # Driver table
    table = Table(
        title="\nFull Driver Prediction Table",
        box=box.MINIMAL_DOUBLE_HEAD,
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("Pos", justify="center", width=4)
    table.add_column("Driver", width=22)
    table.add_column("Team", width=16)
    table.add_column("Win %", justify="center", width=7)
    table.add_column("Top-3 %", justify="center", width=8)
    table.add_column("Top-10 %", justify="center", width=9)
    table.add_column("DNF %", justify="center", width=7)
    table.add_column("Beat T/M %", justify="center", width=10)
    table.add_column("Confidence", justify="center", width=10)

    CONF_COLOUR = {"High": "bright_green", "Medium": "yellow", "Low": "red"}

    for p in result["predictions"]:
        pos = p["predicted_position"]
        pos_str = {1: "[gold1]1[/]", 2: "[grey66]2[/]", 3: "[dark_orange]3[/]"}.get(pos, str(pos))
        cc = CONF_COLOUR.get(p["confidence"], "white")
        table.add_row(
            pos_str,
            p["driver"],
            p["team"].replace("_", " ").title(),
            f"[bold green]{p['win_pct']}[/]" if p["win_pct"] > 15 else str(p["win_pct"]),
            str(p["top3_pct"]),
            str(p["top10_pct"]),
            f"[red]{p['dnf_pct']}[/]" if p["dnf_pct"] > 14 else str(p["dnf_pct"]),
            str(p["teammate_beat_pct"]),
            f"[{cc}]{p['confidence']}[/]",
        )

    console.print(table)

    # Surprises
    if result["likely_top_surprises"]:
        console.print(f"\n[bold yellow]⬆ Most likely overperformers:[/]")
        for name in result["likely_top_surprises"]:
            console.print(f"  • {name}")

    # Save report
    if save_report:
        with console.status("Generating HTML report…"):
            path = generate_report("canada", rain_probability=rain, n_simulations=sims)
        console.print(f"\n[green]✓ HTML report saved → {path}[/]")

    console.print("\n[dim]Confidence statement: Model confidence dampened by Montreal's ~82% SC rate and variable late-May weather.[/]\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="2026 Canadian GP Prediction")
    parser.add_argument("--rain", type=float, default=None, help="Rain probability override")
    parser.add_argument("--sims", type=int, default=5000, help="Simulation count")
    parser.add_argument("--no-report", action="store_true", help="Skip HTML report")
    args = parser.parse_args()

    run(rain=args.rain, sims=args.sims, save_report=not args.no_report)
