"""
F1 Prediction System — CLI Entrypoint.

Usage:
  python main.py predict --race canada
  python main.py report  --race canada --output ./canada_report.html
  python main.py api
  python main.py backtest --seasons 2023 2024 2025
"""

import sys
import json
import click
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


@click.group()
def cli():
    """F1 Race Outcome Prediction System — 2026 Season."""
    pass


# ── predict ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--race", "-r", required=True, help="Circuit ID (e.g. canada, monaco, australia)")
@click.option("--rain", "-w", type=float, default=None, help="Override rain probability [0.0–1.0]")
@click.option("--sims", "-n", type=int, default=5000, help="Monte Carlo simulations (default 5000)")
@click.option("--json-out", is_flag=True, help="Output raw JSON instead of table")
def predict(race: str, rain: float, sims: int, json_out: bool):
    """Run a race outcome prediction."""
    # Validate inputs
    if rain is not None and (rain < 0.0 or rain > 1.0):
        console.print(f"[red]Error:[/] Rain probability must be between 0.0 and 1.0")
        sys.exit(1)
    
    if sims < 100:
        console.print(f"[red]Error:[/] Number of simulations must be at least 100")
        sys.exit(1)
    
    try:
        from engine.predictor import predict as run_predict, PredictionRequest
    except ImportError as e:
        console.print(f"[red]Error importing prediction engine:[/] {e}")
        sys.exit(1)

    console.print(f"\n[bold cyan]F1 Prediction Engine[/] — {race.upper()}\n")

    try:
        with console.status(f"Running {sims:,} Monte Carlo simulations…"):
            result = run_predict(PredictionRequest(
                circuit_id=race,
                rain_probability=rain,
                n_simulations=sims,
            ))
    except Exception as e:
        console.print(f"[red]Error during prediction:[/] {e}")
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(result, indent=2))
        return

    try:
        meta = result["meta"]
        console.print(Panel(
            f"[bold]{meta['circuit']}[/] · {meta['city']} · {meta['race_date']}\n"
            f"Safety Car prob: [yellow]{meta['safety_car_probability']*100:.0f}%[/]  "
            f"Rain prob: [blue]{meta['rain_probability']*100:.0f}%[/]  "
            f"Model confidence: [green]{meta['overall_model_confidence']*100:.0f}%[/]"
            + ("\n[magenta]⚡ Sprint Weekend[/]" if meta['sprint_weekend'] else ""),
            title="Race Info",
        ))

        console.print(f"\n[bold green]Predicted Podium:[/]  " + "  →  ".join(
            f"{'🥇🥈🥉'[i]} {name}" for i, name in enumerate(result["podium_predictions"])
        ))

        table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan")
        table.add_column("P", style="bold", justify="right", width=3)
        table.add_column("Driver", width=20)
        table.add_column("Team", width=14)
        table.add_column("Win %", justify="center", width=8)
        table.add_column("Top 3 %", justify="center", width=8)
        table.add_column("Top 10 %", justify="center", width=9)
        table.add_column("DNF %", justify="center", width=7)
        table.add_column("Conf", justify="center", width=8)

        conf_style = {"High": "green", "Medium": "yellow", "Low": "red"}

        for p in result["predictions"]:
            pos_str = f"{'🥇' if p['predicted_position'] == 1 else '🥈' if p['predicted_position'] == 2 else '🥉' if p['predicted_position'] == 3 else str(p['predicted_position'])}"
            table.add_row(
                pos_str,
                p["driver"],
                p["team"].replace("_", " ").title(),
                f"[bold]{p['win_pct']}%[/]" if p["win_pct"] > 10 else f"{p['win_pct']}%",
                f"{p['top3_pct']}%",
                f"{p['top10_pct']}%",
                f"[red]{p['dnf_pct']}%[/]" if p["dnf_pct"] > 14 else f"{p['dnf_pct']}%",
                f"[{conf_style.get(p['confidence'], 'white')}]{p['confidence']}[/]",
            )

        console.print("\n")
        console.print(table)

        if result.get("likely_top_surprises"):
            console.print(f"\n[bold yellow]⬆ Potential overperformers:[/] " +
                          ", ".join(result["likely_top_surprises"]))

        console.print()
    except KeyError as e:
        console.print(f"[red]Error: Missing expected data in prediction result:[/] {e}")
        sys.exit(1)


# ── report ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--race", "-r", required=True, help="Circuit ID")
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--rain", "-w", type=float, default=None)
@click.option("--sims", "-n", type=int, default=5000)
def report(race: str, output: str, rain: float, sims: int):
    """Generate a full HTML race prediction report."""
    # Validate inputs
    if rain is not None and (rain < 0.0 or rain > 1.0):
        console.print(f"[red]Error:[/] Rain probability must be between 0.0 and 1.0")
        sys.exit(1)
    
    if sims < 100:
        console.print(f"[red]Error:[/] Number of simulations must be at least 100")
        sys.exit(1)
    
    try:
        from reports.html_report import generate_report
    except ImportError as e:
        console.print(f"[red]Error importing report generator:[/] {e}")
        sys.exit(1)

    console.print(f"\n[bold cyan]Generating HTML report for {race.upper()}…[/]")
    try:
        with console.status("Running prediction engine…"):
            path = generate_report(race, rain_probability=rain, n_simulations=sims, output_path=output)

        console.print(f"[green]✓ Report saved to:[/] {path}\n")
    except Exception as e:
        console.print(f"[red]Error during report generation:[/] {e}")
        sys.exit(1)


# ── api ────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default=None)
@click.option("--port", default=None, type=int)
@click.option("--reload", is_flag=True)
def api(host: str, port: int, reload: bool):
    """Start the FastAPI prediction server."""
    try:
        from fastapi import FastAPI
        from api.routes import router
        from config.settings import API_HOST, API_PORT
    except ImportError as e:
        console.print(f"[red]Error importing API components:[/] {e}")
        sys.exit(1)

    # Use defaults if not overridden by CLI
    host = host or API_HOST
    port = port or API_PORT

    try:
        app = FastAPI(
            title="F1 Race Prediction API",
            description="Probabilistic F1 race outcome prediction system.",
            version="1.0.0",
        )
        app.include_router(router, prefix="/api/v1")

        console.print(f"\n[bold cyan]F1 Prediction API[/] starting at http://{host}:{port}")
        console.print(f"[dim]Docs → http://{host}:{port}/docs[/]\n")
        uvicorn.run(app, host=host, port=port, reload=reload)
    except Exception as e:
        console.print(f"[red]Error starting API server:[/] {e}")
        sys.exit(1)


# ── backtest ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--seasons", "-s", multiple=True, type=int, default=[2024, 2025])
def backtest(seasons):
    """
    Run temporal cross-validation backtest across historical seasons.
    NOTE: Requires historical data in data/historical/ (not included in base package).
    """
    try:
        from engine.calibration import temporal_cross_validate
    except ImportError as e:
        console.print(f"[red]Error importing backtest module:[/] {e}")
        sys.exit(1)

    console.print(f"\n[bold cyan]Backtesting seasons:[/] {list(seasons)}\n")
    console.print("[yellow]⚠ Backtest requires historical race prediction data.[/]")
    console.print("Populate data/historical/ with per-race prediction snapshots,")
    console.print("then call temporal_cross_validate() with the assembled data.\n")
    console.print("[dim]See scripts/backtest_2025_season.py for a full example.[/]")


if __name__ == "__main__":
    cli()