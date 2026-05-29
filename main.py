"""
F1 Prediction System — CLI Entry Point v2.

New in v2:
  - quality-check command (runs data_quality_report.py)
  - --grid-override flag for post-qualifying accuracy boost
  - --seed flag for reproducible results
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
    """🏁 F1 Race Outcome Prediction System — 2026 Season."""
    pass


# ── predict ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--race", "-r", required=True,
              help="Circuit ID e.g. canada, monaco, silverstone (use 'britain' for Silverstone)")
@click.option("--rain", "-w", type=float, default=None,
              help="Override rain probability (0.0-1.0)")
@click.option("--sims", "-n", type=int, default=5000,
              help="Number of Monte Carlo simulations")
@click.option("--seed", type=int, default=None,
              help="Random seed for reproducibility")
@click.option("--grid-override", "-g", default=None,
              help='Override grid positions: "driver_id:pos,driver_id:pos"')
@click.option("--json-out", is_flag=True,
              help="Output raw JSON instead of formatted table")
@click.option("--auto-report", is_flag=True,
              help="Automatically generate HTML report after prediction")
def predict(race: str, rain: float, sims: int, seed: int,
            grid_override: str, json_out: bool, auto_report: bool):
    """Run a race outcome prediction."""
    if rain is not None and not (0.0 <= rain <= 1.0):
        console.print("[red]Error:[/] --rain must be between 0.0 and 1.0"); sys.exit(1)
    if sims < 100:
        console.print("[red]Error:[/] --sims must be at least 100"); sys.exit(1)

    # Parse --grid-override "antonelli:1,russell:2"
    grid_overrides = {}
    if grid_override:
        try:
            for part in grid_override.split(","):
                driver_id, pos = part.strip().split(":")
                grid_overrides[driver_id.strip()] = int(pos)
        except ValueError:
            console.print('[red]Error:[/] --grid-override format: "driver_id:pos,driver_id:pos"')
            sys.exit(1)

    try:
        from engine.predictor import predict as run_predict, PredictionRequest
    except ImportError as e:
        console.print(f"[red]Import error:[/] {e}"); sys.exit(1)

    console.print(f"\n[bold cyan]F1 Prediction Engine v2[/] — [bold]{race.upper()}[/]\n")

    try:
        with console.status(f"Running {sims:,} Monte Carlo simulations…"):
            result = run_predict(PredictionRequest(
                circuit_id=race,
                rain_probability=rain,
                n_simulations=sims,
                seed=seed,
                grid_overrides=grid_overrides,
            ))
    except KeyError as e:
        console.print(f"[red]Circuit not found:[/] {e}\n"
                      f"[dim]Run `python main.py circuits` to list all available circuit IDs.[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Prediction failed:[/] {e}"); sys.exit(1)

    if json_out:
        click.echo(json.dumps(result, indent=2))
        return

    # Assign sequential positions (1,2,3,4,5...) instead of tied positions
    predictions = result["predictions"]
    # Sort by predicted_position, then by win probability as tiebreaker
    predictions_sorted = sorted(
        predictions,
        key=lambda x: (x.get('predicted_position', 999), -x.get('win_pct', 0))
    )
    # Assign sequential display positions
    for idx, pred in enumerate(predictions_sorted, start=1):
        pred['display_position'] = idx
    
    meta = result["meta"]
    console.print(Panel(
        f"[bold]{meta['circuit']}[/] · {meta['city']} · {meta['race_date']}\n"
        f"SC prob: [yellow]{meta['safety_car_probability']*100:.0f}%[/]  "
        f"Rain: [blue]{meta['rain_probability']*100:.0f}%[/]  "
        f"Confidence: [green]{meta['overall_model_confidence']*100:.0f}%[/]  "
        f"Sims: {meta['n_simulations']:,}"
        + ("\n[magenta]⚡ Sprint Weekend[/]" if meta["sprint_weekend"] else "")
        + (f"\n[dim]Grid overrides applied: {grid_overrides}[/]" if grid_overrides else ""),
        title="Race Info",
    ))

    console.print("\n[bold green]Predicted Podium:[/]  " + "  →  ".join(
        f"{'🥇🥈🥉'[i]} {name}" for i, name in enumerate(result["podium_predictions"])
    ))

    t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan")
    t.add_column("P",        style="bold", justify="right", width=4)
    t.add_column("Driver",   width=22)
    t.add_column("Team",     width=14)
    t.add_column("Win %",    justify="center", width=8)
    t.add_column("Top 3 %",  justify="center", width=8)
    t.add_column("Top 10 %", justify="center", width=9)
    t.add_column("DNF %",    justify="center", width=7)
    t.add_column("T/M %",    justify="center", width=7)
    t.add_column("Conf",     justify="center", width=8)

    conf_colour = {"High": "green", "Medium": "yellow", "Low": "red"}
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for p in predictions_sorted:
        pos = p.get("display_position", p["predicted_position"])
        pos_str = medals.get(pos, str(pos))
        cc = conf_colour.get(p["confidence"], "white")
        t.add_row(
            pos_str,
            p["driver"],
            p["team"].replace("_", " ").title(),
            f"[bold]{p['win_pct']}%[/]" if p["win_pct"] > 10 else f"{p['win_pct']}%",
            f"{p['top3_pct']}%",
            f"{p['top10_pct']}%",
            f"[red]{p['dnf_pct']}%[/]" if p["dnf_pct"] > 14 else f"{p['dnf_pct']}%",
            f"{p['teammate_beat_pct']}%",
            f"[{cc}]{p['confidence']}[/]",
        )

    console.print("\n")
    console.print(t)

    if result.get("likely_top_surprises"):
        console.print(
            f"\n[bold yellow]⬆ Potential overperformers:[/] "
            + ", ".join(result["likely_top_surprises"])
        )
    
    # Auto-generate HTML report if requested
    if auto_report:
        try:
            from reports.html_report import generate_report
            with console.status("[cyan]Generating HTML report…[/]"):
                path = generate_report(race, rain_probability=rain, n_simulations=sims)
            console.print(f"\n[green]✓ HTML report saved → {path}[/]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not generate HTML report:[/] {e}")
    
    console.print()


# ── report ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--race", "-r", required=True, help="Circuit ID")
@click.option("--output", "-o", default=None, help="Output HTML file path")
@click.option("--rain", "-w", type=float, default=None)
@click.option("--sims", "-n", type=int, default=5000)
@click.option("--seed", type=int, default=None)
def report(race: str, output: str, rain: float, sims: int, seed: int):
    """Generate a full HTML race prediction report with charts and feature breakdown."""
    if rain is not None and not (0.0 <= rain <= 1.0):
        console.print("[red]Error:[/] --rain must be between 0.0 and 1.0"); sys.exit(1)

    try:
        from reports.html_report import generate_report
    except ImportError as e:
        console.print(f"[red]Import error:[/] {e}"); sys.exit(1)

    console.print(f"\n[bold cyan]Generating HTML report — {race.upper()}…[/]")
    try:
        with console.status("Running prediction engine…"):
            path = generate_report(race, rain_probability=rain,
                                   n_simulations=sims, output_path=output)
        console.print(f"[green]✓ Report saved:[/] {path}")
        console.print(f"[dim]Preview: python -m http.server 8080 --directory $(dirname {path})[/]\n")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}"); sys.exit(1)


# ── quality-check ──────────────────────────────────────────────────────────────

@cli.command("quality-check")
def quality_check():
    """Run data quality checks — validates drivers, circuits, season data, and weights."""
    try:
        from scripts.data_quality_report import run_all_checks
        run_all_checks()
    except ImportError:
        # Fallback: run as subprocess in case of import path issues
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/data_quality_report.py"],
            check=False
        )


# ── circuits ───────────────────────────────────────────────────────────────────

@cli.command()
def circuits():
    """List all available circuit IDs for the 2026 season."""
    from data.circuit_data import get_all_circuits
    t = Table(title="2026 Circuit IDs", box=box.SIMPLE_HEAD, header_style="bold cyan")
    t.add_column("ID",       width=14)
    t.add_column("Name",     width=34)
    t.add_column("Round",    justify="center", width=7)
    t.add_column("Date",     width=12)
    t.add_column("Sprint",   justify="center", width=8)
    t.add_column("SC%",      justify="center", width=6)

    for c in sorted(get_all_circuits(), key=lambda x: x["round_2026"]):
        sprint = "⚡ Yes" if c.get("sprint_weekend") else "No"
        sc = f"{int(c.get('safety_car_probability', 0)*100)}%"
        t.add_row(c["id"], c["name"], str(c["round_2026"]),
                  c.get("race_date", "TBC"), sprint, sc)
    console.print("\n")
    console.print(t)
    console.print()


# ── api ─────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default=None, help="Bind host (default: from .env or 0.0.0.0)")
@click.option("--port", default=None, type=int, help="Bind port (default: from .env or 8000)")
@click.option("--port-auto", is_flag=True, help="If the requested port is in use, try the next free port")
@click.option("--max-port", default=None, type=int,
              help="Max port to try when --port-auto is enabled (default: port + 50)")
@click.option("--reload", is_flag=True, help="Enable hot-reload (development only)")
def api(host: str, port: int, port_auto: bool, max_port: int, reload: bool):
    """Start the FastAPI prediction server."""

    try:
        from fastapi import FastAPI
        from api.routes import router
        from config.settings import API_HOST, API_PORT
    except ImportError as e:
        console.print(f"[red]Import error:[/] {e}"); sys.exit(1)

    host = host or API_HOST
    port = port or API_PORT

    # If port-auto is enabled, try to start on the first available port.
    if port_auto:
        import socket

        start_port = int(port)
        upper = int(max_port) if max_port is not None else start_port + 50
        chosen_port = None

        for p in range(start_port, upper + 1):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, p))
                chosen_port = p
                break
            except OSError:
                pass
            finally:
                s.close()

        if chosen_port is None:
            console.print(f"[red]Error:[/] No free port found in range {start_port}-{upper}.")
            sys.exit(1)

        if chosen_port != start_port:
            console.print(f"[yellow]Port {start_port} in use.[/] Using free port {chosen_port} instead.")

        port = chosen_port

    app = FastAPI(
        title="F1 Race Prediction API",
        description="Probabilistic F1 race outcome prediction — 2026 season.",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # FIX-4.5: Add CORS middleware for frontend access from different origins
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For production, restrict to specific domains
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    
    app.include_router(router, prefix="/api/v1")

    console.print(f"\n[bold cyan]F1 Prediction API v2[/] → http://{host}:{port}")
    console.print(f"[dim]Swagger UI:  http://{host}:{port}/docs[/]")
    console.print(f"[dim]ReDoc:       http://{host}:{port}/redoc[/]\n")
    try:
        uvicorn.run(app, host=host, port=port, reload=reload)
    except OSError as e:
        console.print(f"[red]API failed to bind:[/] {e}")
        if not port_auto:
            console.print("[dim]Try again with --port-auto (or kill the process using port 8000).[/]")
        raise



# ── backtest ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--seasons", "-s", multiple=True, type=int, default=[2025])
def backtest(seasons):
    """Run temporal cross-validation backtest across historical seasons."""
    console.print(f"\n[bold cyan]Backtesting:[/] {list(seasons)}\n")
    console.print("[yellow]⚠[/] Requires historical snapshots in data/historical/<year>/")
    console.print("[dim]See data/historical/README.md for the expected format.[/]")
    console.print("[dim]Run scripts/backtest_2025_season.py for a demo.[/]\n")


if __name__ == "__main__":
    cli()