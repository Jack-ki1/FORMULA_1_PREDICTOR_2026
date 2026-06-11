# Formula 1 Predictor 2026

A modular Formula 1 race prediction platform built for the 2026 season.
It combines Monte Carlo simulation, feature engineering, championship modelling, database tracking, and a Flask dashboard to deliver race forecasts, accuracy reports, and interactive analytics.

## 🚀 Project Highlights

- **Vectorized Monte Carlo engine** using NumPy for high-performance race simulation.
- **Feature-based driver and constructor modelling** using circuit metadata, form, and reliability.
- **FastF1 support** for historical session ingestion and advanced race feature extraction.
- **Flask dashboard** for interactive prediction analytics and report downloads.
- **SQLite persistence** for prediction storage, backtesting, and accuracy evaluation.
- **Optuna optimization** for tuning weights and improving forecast performance.

## 📁 Repository Structure

- `main.py` — CLI entry point for predictions, dashboard, reports, and utilities.
- `config/` — application settings and model weight definitions.
- `data/` — static 2026 season data, circuit metadata, driver profiles, and FastF1 integration.
- `engine/` — prediction engine, simulation models, feature engineering, and tracking.
- `dashboard/` — Flask web application and templates for interactive visualization.
- `database/` — SQLAlchemy models and migration helpers.
- `reports/` — HTML report generation for race predictions.
- `scripts/` — quality checks, optimization, and post-race evaluation utilities.

## 🧠 Core Architecture

- `engine.feature_engineering` computes driver and team scores by combining circuit characteristics, weather, reliability, and historical form.
- `engine.probability_model` runs the Monte Carlo prediction logic and returns probability distributions per driver.
- `engine.vectorized_simulation` provides a NumPy-optimized simulation path for fast batch evaluation.
- `engine.predictor` orchestrates input validation, driver feature generation, simulation selection, and output formatting.
- `dashboard/app.py` exposes prediction APIs and renders the dashboard interface.
- `database/models.py` migrates static data into SQLite and stores prediction records.

## ⚙️ Requirements

- Python 3.10+
- `requirements.txt` contains dependencies for CLI, dashboard, database, and analysis.

### Main dependencies

- `numpy`
- `pandas`
- `scikit-learn`
- `flask`
- `flask-cors`
- `flask-limiter`
- `python-dotenv`
- `pydantic`
- `sqlalchemy`
- `click`
- `rich`
- `optuna`
- `fastf1`

## 🛠️ Setup

```bash
cd c:\Users\PC\Music\FORMULA_1_PREDICTOR_2026
py -3 -m pip install -r requirements.txt
```

Copy environment variables:

```bash
copy .env.example .env
```

Then edit `.env` to configure:

- `WEATHER_API_KEY`
- `F1_API_KEY`
- `FLASK_DEBUG`
- `PORT`
- `F1_DATABASE_URL`

## 🚗 CLI Usage

Run the main CLI from the project root:

```bash
py -3 main.py --help
```

### Common commands

#### Predict a race

```bash
py -3 main.py predict --race monaco --sims 10000 --vectorized
```

Options:
- `--race` / `-r`: circuit ID (use `py -3 main.py circuits` to list available IDs)
- `--rain` / `-w`: override rain probability `0.0-1.0`
- `--sims` / `-n`: simulation count
- `--grid-override` / `-g`: driver grid positions like `verstappen:1,hamilton:2`
- `--json-out`: print raw JSON
- `--auto-report`: generate an HTML report after prediction
- `--export`: export predictions to `.csv` or `.json`
- `--store`: save predictions in the database

#### Start the dashboard

```bash
py -3 main.py dashboard --port 5000
```

Then open:

```text
http://127.0.0.1:5000
```

#### Generate a report

```bash
py -3 main.py report --race monaco --sims 5000
```

#### List circuits

```bash
py -3 main.py circuits
```

## 🎯 Advanced commands

- `h2h` — compare two drivers head-to-head for a specific race
- `optimize-weights` — run Optuna to find better feature weights
- `migrate-db` — migrate static season data into SQLite
- `sync-fastf1` — ingest historical FastF1 data for configured seasons
- `evaluate-race` — score predictions against actual race results
- `accuracy-report` — print stored prediction accuracy metrics
- `championship-sim` — simulate remaining season outcomes
- `quality-check` — validate season dataset, drivers, and configuration
- `backtest` — replay historical races and evaluate model performance
- `benchmark` — compare vectorized vs original simulation performance

## 🌐 Dashboard

The Flask dashboard supports:

- single-race predictions
- H2H driver comparisons
- constructor performance views
- direct report download
- lightweight rate limiting and CORS handling

### Run dashboard only

```bash
py -3 main.py dashboard --port 5000
```

## 💾 Database support

The app uses SQLAlchemy with an SQLite backend by default.

To migrate static data into the database:

```bash
py -3 main.py migrate-db
```

Predictions can be stored during CLI runs with `--store`, then evaluated using `accuracy-report`.

## 🧪 Validation and quality

Run data checks with:

```bash
py -3 main.py quality-check
```

Use the `scripts/` utilities to inspect data quality and prediction accuracy after races.

## 📦 Folder breakdown

- `config/` — model parameters, weights, and validation
- `data/` — circuits, drivers, teams, season structure, and FastF1 integration
- `engine/` — prediction logic, simulation, calibration, and tracking
- `dashboard/` — Flask server, templates, and API endpoints
- `database/` — data models and migration helpers
- `reports/` — HTML report generation
- `scripts/` — maintenance and evaluation tools

## 💡 Notes

- Circuit IDs are based on the 2026 season dataset (e.g. `monaco`, `canada`, `britain`).
- The vectorized engine is the preferred fast path for Monte Carlo simulation.
- FastF1 integration is used for advanced feature extraction and historical race sync; if the package or schedule access is unavailable, the system falls back gracefully to static driver and circuit data.
- Prediction storage and evaluation are enabled through SQLite when running with `--store` and `migrate-db`.
- This project is designed for experimentation, model tuning, and interactive race forecasting.

## 📘 License

This project is provided as-is for experimentation and development.
Feel free to extend it with additional F1 datasets, live telemetry, or improved prediction logic.
