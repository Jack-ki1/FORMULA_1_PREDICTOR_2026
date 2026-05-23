"""
Script to run predictions for the Canadian Grand Prix 2026.

This script demonstrates the usage of the prediction engine and generates
both raw data and HTML reports for the Canadian GP.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
from pathlib import Path
from datetime import datetime

import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from engine.predictor import predict, PredictionRequest
from reports.html_report import generate_report
from config.settings import REPORT_CONFIG

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Run F1 predictions for Canadian GP 2026")
    parser.add_argument("--circuit", default="canada", help="Circuit ID (default: canada)")
    parser.add_argument("--rain-prob", type=float, default=None, help="Rain probability (0.0-1.0)")
    parser.add_argument("--sim-count", type=int, default=5000, help="Number of simulations")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic runs")
    parser.add_argument("--output-dir", default=None, help="Output directory for reports")
    parser.add_argument("--output-format", default="full", choices=["full", "summary", "intermediate", "winner_only"],
                        help="Output format for predictions")
    parser.add_argument("--save-json", action="store_true", help="Save raw JSON output")
    
    args = parser.parse_args()
    
    # Use provided output directory or fall back to config
    output_dir = args.output_dir or REPORT_CONFIG.output_dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create prediction request
    request = PredictionRequest(
        circuit_id=args.circuit,
        rain_probability=args.rain_prob,
        n_simulations=args.sim_count,
        seed=args.seed,
        output_format=args.output_format,
        include_intermediate_artifacts=(args.output_format == 'intermediate')
    )
    
    console.print(f"Generating prediction for {args.circuit} GP with {args.sim_count:,} simulations...")
    if args.seed:
        console.print(f"Using seed: {args.seed}")
    if args.rain_prob is not None:
        console.print(f"Rain probability: {args.rain_prob:.2f}")
    
    console.print(f"[cyan]Running {args.sim_count:,} Monte Carlo simulations…[/]")
    
    # Run prediction
    result = predict(request)
    
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

    # Save raw JSON if requested
    if args.save_json or True:  # Always save JSON for reproducibility
        json_filename = f"{args.circuit}_gp_2026_pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_path = os.path.join(output_dir, json_filename)
        
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        console.print(f"[green]✓ Raw prediction JSON saved to {json_path}[/]")

    # Generate HTML report
    html_filename = f"{args.circuit}_gp_2026_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    html_path = os.path.join(output_dir, html_filename)
    
    generate_report(result, html_path)
    
    console.print(f"[green]✓ HTML report saved to {html_path}[/]")
    console.print("\n[dim]Confidence statement: Model confidence dampened by Montreal's ~82% SC rate and variable late-May weather.[/]")

    console.print("\n[bold green]Prediction completed successfully![/]")

    return result


if __name__ == "__main__":
    main()
