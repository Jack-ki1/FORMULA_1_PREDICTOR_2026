"""
F1 Prediction System — CLI Entry Point v3.0.

New in v3.0:
  - Database integration (SQLite via SQLAlchemy)
  - Fast-F1 data ingestion
  - Vectorized simulation (20x faster)
  - Dynamic weight optimization (Optuna)
  - H2H driver comparison
  - Constructor predictions
  - Championship simulator
  - Prediction accuracy tracking
  - Web dashboard
  - Weather API integration
"""

import sys
import os
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


@click.group()
def cli():
    """🏁 F1 Race Outcome Prediction System v3.0 — 2026 Season."""
    pass


# ── predict ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--race", "-r", required=True,
              help="Circuit ID e.g. canada, monaco, britain")
@click.option("--rain", "-w", type=float, default=None,
              help="Override rain probability (0.0-1.0)")
@click.option("--sims", "-n", type=int, default=10000,
              help="Number of Monte Carlo simulations (v3.0: up to 100,000)")
@click.option("--seed", type=int, default=None,
              help="Random seed for reproducibility")
@click.option("--grid-override", "-g", default=None,
              help='Override grid positions: "driver_id:pos,driver_id:pos"')
@click.option("--json-out", is_flag=True,
              help="Output raw JSON instead of formatted table")
@click.option("--auto-report", is_flag=True,
              help="Automatically generate HTML report after prediction")
@click.option("--vectorized", is_flag=True, default=True,
              help="Use vectorized simulation (20x faster)")
@click.option("--export", default=None,
              help="Export predictions to CSV/JSON file")
@click.option("--store", is_flag=True,
              help="Store prediction in database for accuracy tracking")
def predict(race: str, rain: float, sims: int, seed: int,
            grid_override: str, json_out: bool, auto_report: bool,
            vectorized: bool, export: str, store: bool):
    """Run a race outcome prediction."""
    if rain is not None and not (0.0 <= rain <= 1.0):
        console.print("[red]Error:[/] --rain must be between 0.0 and 1.0"); sys.exit(1)
    if sims < 100:
        console.print("[red]Error:[/] --sims must be at least 100"); sys.exit(1)

    # Parse --grid-override
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

    console.print(f"\n[bold cyan]F1 Prediction Engine v3.0[/] — [bold]{race.upper()}[/]\n")

    try:
        with console.status(f"Running {sims:,} Monte Carlo simulations{' (vectorized)' if vectorized else ''}…"):
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

    # Assign sequential positions
    predictions = result["predictions"]
    predictions_sorted = sorted(
        predictions,
        key=lambda x: (x.get('predicted_position', 999), -x.get('win_pct', 0))
    )
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
    
    # Auto-generate HTML report
    if auto_report:
        try:
            from reports.html_report import generate_report
            with console.status("[cyan]Generating HTML report…[/]"):
                path = generate_report(race, rain_probability=rain, n_simulations=sims)
            console.print(f"\n[green]✓ HTML report saved → {path}[/]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not generate HTML report:[/] {e}")
    
    # Export to file
    if export:
        try:
            if export.endswith('.json'):
                with open(export, 'w') as f:
                    json.dump(result, f, indent=2)
            elif export.endswith('.csv'):
                import csv
                with open(export, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['position', 'driver', 'team', 'win_pct', 'top3_pct', 'top10_pct', 'dnf_pct'])
                    writer.writeheader()
                    for p in predictions_sorted:
                        writer.writerow({
                            'position': p.get('display_position', p['predicted_position']),
                            'driver': p['driver'],
                            'team': p['team'],
                            'win_pct': p['win_pct'],
                            'top3_pct': p['top3_pct'],
                            'top10_pct': p['top10_pct'],
                            'dnf_pct': p['dnf_pct'],
                        })
            console.print(f"[green]✓ Predictions exported → {export}[/]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not export:[/] {e}")
    
    # Store in database
    if store:
        try:
            from engine.prediction_tracker import PredictionTracker
            tracker = PredictionTracker()
            tracker.store_prediction(race, result)
            tracker.close()
            console.print("[green]✓ Prediction stored in database for accuracy tracking[/]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not store prediction:[/] {e}")
    
    console.print()


# ── h2h (NEW v3.0) ─────────────────────────────────────────────────────────────

@cli.command()
@click.option("--driver1", "-d1", required=True, help="First driver ID")
@click.option("--driver2", "-d2", required=True, help="Second driver ID")
@click.option("--race", "-r", required=True, help="Circuit ID")
@click.option("--rain", "-w", type=float, default=None)
@click.option("--sims", "-n", type=int, default=10000)
def h2h(driver1: str, driver2: str, race: str, rain: float, sims: int):
    """Head-to-head driver comparison (NEW v3.0)."""
    console.print(f"\n[bold cyan]H2H Comparison:[/] [bold]{driver1}[/] vs [bold]{driver2}[/] at {race.upper()}\n")
    
    try:
        from engine.probability_model import predict_race
        
        # Run race simulation
        sim_result = predict_race(
            circuit_id=race,
            rain_probability=rain,
            n_simulations=sims,
        )
        
        # Extract driver predictions
        predictions = {p["driver_id"]: p for p in sim_result["predictions"]}
        
        if driver1 not in predictions:
            console.print(f"[red]Driver {driver1} not found[/]"); sys.exit(1)
        if driver2 not in predictions:
            console.print(f"[red]Driver {driver2} not found[/]"); sys.exit(1)
        
        driver1_pred = predictions[driver1]
        driver2_pred = predictions[driver2]
        
        # Calculate probability driver1 finishes ahead
        pos_dist_1 = driver1_pred.get("position_distribution", [])
        pos_dist_2 = driver2_pred.get("position_distribution", [])
        
        p_driver1_ahead = 0.0
        for pos1 in range(len(pos_dist_1)):
            for pos2 in range(len(pos_dist_2)):
                if pos1 < pos2:
                    p_driver1_ahead += pos_dist_1[pos1] * pos_dist_2[pos2]
        
        total = p_driver1_ahead + (1 - p_driver1_ahead)
        p_driver1_ahead = p_driver1_ahead / total if total > 0 else 0.5
        
        console.print(Panel(
            f"[bold]{driver1_pred['driver_name']}[/] finishes ahead: [green]{round(p_driver1_ahead * 100, 2)}%[/]\n"
            f"[bold]{driver2_pred['driver_name']}[/] finishes ahead: [yellow]{round((1 - p_driver1_ahead) * 100, 2)}%[/]\n\n"
            f"Avg positions: {driver1_pred['driver_name']} ({driver1_pred['expected_position_float']:.1f}), {driver2_pred['driver_name']} ({driver2_pred['expected_position_float']:.1f})\n"
            f"[dim]Based on {sims:,} Monte Carlo simulations[/]",
            title="H2H Result",
        ))
        
    except Exception as e:
        console.print(f"[red]H2H comparison failed:[/] {e}"); sys.exit(1)


# ── optimize-weights (NEW v3.0) ───────────────────────────────────────────────

@cli.command("optimize-weights")
@click.option("--trials", "-t", type=int, default=100, help="Number of optimization trials")
@click.option("--output", "-o", default="weights_optimized.json")
def optimize_weights(trials: int, output: str):
    """Optimize feature weights using Optuna Bayesian optimization (NEW v3.0)."""
    console.print(f"\n[bold cyan]Weight Optimization:[/] Running {trials} trials\n")
    
    try:
        from scripts.optimize_weights_v3 import run_weight_optimization
        best_weights = run_weight_optimization(n_trials=trials, save_path=output)
        console.print(f"\n[green]✓ Optimized weights saved → {output}[/]")
    except Exception as e:
        console.print(f"[red]Optimization failed:[/] {e}"); sys.exit(1)


# ── migrate-db (NEW v3.0) ─────────────────────────────────────────────────────

@cli.command("migrate-db")
def migrate_db():
    """Migrate data from static Python modules to SQLite database (NEW v3.0)."""
    console.print("\n[bold cyan]Database Migration:[/] Static modules → SQLite\n")
    
    try:
        from database.models import migrate_from_static
        migrate_from_static()
        console.print("\n[green]✓ Migration completed successfully![/]")
    except Exception as e:
        console.print(f"[red]Migration failed:[/] {e}"); sys.exit(1)


# ── sync-fastf1 (NEW v3.0) ─────────────────────────────────────────────────────

@cli.command("sync-fastf1")
@click.option("--seasons", "-s", multiple=True, type=int, default=[2024, 2025])
def sync_fastf1(seasons):
    """Sync historical data from Fast-F1 library (NEW v3.0)."""
    console.print(f"\n[bold cyan]Fast-F1 Sync:[/] Importing data for seasons {list(seasons)}\n")
    
    try:
        from data.fastf1_integration import sync_all_historical_data
        sync_all_historical_data(list(seasons))
    except ImportError:
        console.print("[red]fastf1 library not installed.[/] Run: pip install fastf1"); sys.exit(1)
    except Exception as e:
        console.print(f"[red]Sync failed:[/] {e}"); sys.exit(1)


# ── evaluate-race (NEW v3.0) ───────────────────────────────────────────────────

@cli.command("evaluate-race")
@click.option("--race", "-r", required=True, help="Circuit ID")
@click.option("--results", required=True, help='JSON file with actual results: {"verstappen": 1, "hamilton": 2}')
def evaluate_race(race: str, results: str):
    """Evaluate prediction accuracy after a race (NEW v3.0)."""
    console.print(f"\n[bold cyan]Race Evaluation:[/] {race.upper()}\n")
    
    try:
        import json
        with open(results, 'r') as f:
            actual_results = json.load(f)
        
        from scripts.post_race_evaluation import run_post_race_evaluation
        result = run_post_race_evaluation(race, actual_results)
        
        console.print(f"[green]✓ Evaluation completed:[/] Average Brier score = {result['avg_brier_score']}")
    except Exception as e:
        console.print(f"[red]Evaluation failed:[/] {e}"); sys.exit(1)


# ── accuracy-report (NEW v3.0) ─────────────────────────────────────────────────

@cli.command("accuracy-report")
def accuracy_report():
    """Generate prediction accuracy report (NEW v3.0)."""
    console.print("\n[bold cyan]Prediction Accuracy Report[/]\n")
    
    try:
        from engine.prediction_tracker import PredictionTracker
        tracker = PredictionTracker()
        report = tracker.get_accuracy_report()
        tracker.close()
        
        console.print(Panel(
            f"Total predictions: [bold]{report.get('total_predictions', 0)}[/]\n"
            f"Evaluated: [bold]{report.get('evaluated_predictions', 0)}[/]\n"
            f"Avg Brier score: [bold]{report.get('avg_brier_score', 'N/A')}[/]\n"
            f"Calibration: [bold]{report.get('calibration', 'N/A')}[/]",
            title="Accuracy Stats",
        ))
    except Exception as e:
        console.print(f"[red]Failed to generate report:[/] {e}"); sys.exit(1)


# ── championship-sim (NEW v3.0) ────────────────────────────────────────────────

@cli.command("championship-sim")
@click.option("--remaining", "-r", type=int, default=10, help="Remaining races to simulate")
@click.option("--sims", "-n", type=int, default=5000, help="Number of simulations")
def championship_sim(remaining: int, sims: int):
    """Simulate remaining championship season (NEW v3.0)."""
    console.print(f"\n[bold cyan]Championship Simulator:[/] {remaining} races remaining\n")
    
    try:
        from data.circuit_data import get_all_circuits
        from engine.probability_model import predict_race
        import numpy as np
        
        # Get remaining circuits
        all_circuits = get_all_circuits()
        remaining_circuits = all_circuits[:remaining]
        
        # Points system
        def _get_points_for_position(position: int) -> float:
            points_map = {
                1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
                6: 8, 7: 6, 8: 4, 9: 2, 10: 1,
            }
            return points_map.get(position, 0)
        
        # Run Monte Carlo over multiple races
        driver_championship_wins = {}
        constructor_championship_wins = {}
        
        for sim in range(sims):
            driver_points = {}
            constructor_points = {}
            
            for circuit in remaining_circuits:
                # Simulate race
                sim_result = predict_race(
                    circuit_id=circuit["id"],
                    n_simulations=1000,
                    seed=sim,
                )
                
                # Add points
                for driver_pred in sim_result["predictions"]:
                    pos = driver_pred["predicted_position"]
                    points = _get_points_for_position(pos)
                    
                    driver_id = driver_pred["driver_id"]
                    team = driver_pred["team"]
                    
                    driver_points[driver_id] = driver_points.get(driver_id, 0) + points
                    constructor_points[team] = constructor_points.get(team, 0) + points
            
            # Track winners
            driver_winner = max(driver_points, key=driver_points.get)
            constructor_winner = max(constructor_points, key=constructor_points.get)
            
            driver_championship_wins[driver_winner] = driver_championship_wins.get(driver_winner, 0) + 1
            constructor_championship_wins[constructor_winner] = constructor_championship_wins.get(constructor_winner, 0) + 1
        
        # Calculate probabilities
        driver_probs = {
            driver: round(count / sims * 100, 2)
            for driver, count in driver_championship_wins.items()
        }
        constructor_probs = {
            team: round(count / sims * 100, 2)
            for team, count in constructor_championship_wins.items()
        }
        
        # Sort by probability
        driver_probs = dict(sorted(driver_probs.items(), key=lambda x: x[1], reverse=True)[:5])
        constructor_probs = dict(sorted(constructor_probs.items(), key=lambda x: x[1], reverse=True)[:5])
        
        console.print("[bold green]Driver Championship Probabilities:[/]")
        for driver, prob in driver_probs.items():
            console.print(f"  {driver}: {prob}%")
        
        console.print("\n[bold yellow]Constructor Championship Probabilities:[/]")
        for team, prob in constructor_probs.items():
            console.print(f"  {team}: {prob}%")
        
    except Exception as e:
        console.print(f"[red]Championship simulation failed:[/] {e}"); sys.exit(1)


# ── dashboard (NEW v3.0) ───────────────────────────────────────────────────────

@cli.command()
@click.option("--port", "-p", type=int, default=5000, help="Dashboard port")
def dashboard(port: int):
    """Start the interactive web dashboard (NEW v3.0)."""
    console.print(f"\n[bold cyan]F1 Predictor Dashboard v3.0[/] → http://127.0.0.1:{port}\n")
    
    try:
        import subprocess
        # Pass port as environment variable to Flask app
        env = os.environ.copy()
        env['FLASK_PORT'] = str(port)
        subprocess.run([sys.executable, "dashboard/app.py"], env=env, check=True)
    except Exception as e:
        console.print(f"[red]Dashboard failed to start:[/] {e}"); sys.exit(1)


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


# ── backtest ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--seasons", "-s", multiple=True, type=int, default=[2025])
def backtest(seasons):
    """Run temporal cross-validation backtest across historical seasons."""
    console.print(f"\n[bold cyan]Backtesting:[/] {list(seasons)}\n")
    console.print("[yellow]⚠[/] Requires historical snapshots in data/historical/<year>/")
    console.print("[dim]See data/historical/README.md for the expected format.[/]")
    console.print("[dim]Run scripts/backtest_2025_season.py for a demo.[/]\n")


# ── benchmark (NEW v3.0) ──────────────────────────────────────────────────────

@cli.command()
@click.option("--circuit", "-c", default="canada")
@click.option("--sims", "-n", type=int, default=5000)
def benchmark(circuit: str, sims: int):
    """Benchmark vectorized vs original simulation performance (NEW v3.0)."""
    console.print(f"\n[bold cyan]Performance Benchmark:[/] {circuit.upper()}, {sims:,} sims\n")
    
    try:
        from engine.vectorized_simulation import compare_performance
        result = compare_performance(circuit, n_runs=sims, seed=42)
        
        console.print(Panel(
            f"Vectorized time: [bold green]{result['vectorized_time_ms']:.2f} ms[/]\n"
            f"Original time:   [yellow]{result['original_time_ms']:.2f} ms[/]\n"
            f"Speedup:         [bold]{result['speedup_factor']:.2f}x[/]\n"
            f"Accuracy diff:   {result['max_prob_diff']:.4f}\n"
            f"Accuracy check:  [{'green' if result['accuracy_check'] == 'PASS' else 'red'}]{result['accuracy_check']}[/]",
            title="Benchmark Results",
        ))
    except Exception as e:
        console.print(f"[red]Benchmark failed:[/] {e}"); sys.exit(1)


if __name__ == "__main__":
    cli()
