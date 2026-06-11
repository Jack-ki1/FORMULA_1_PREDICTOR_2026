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

```
FORMULA_1_PREDICTOR_2026/
│
├── main.py                          # CLI entry point for predictions, dashboard, reports, and utilities
├── requirements.txt                 # Python dependencies (numpy, pandas, flask, fastf1, etc.)
├── pyproject.toml                   # Project metadata and build configuration
├── .env.example                     # Environment variable template (API keys, database URL)
├── .gitignore                       # Git ignore rules for cache files, databases, virtual environments
├── cleanup_and_test.bat             # Windows batch script for cleanup and testing automation
├── sc1.png                          # Screenshot/visual asset for documentation
└── README.md                        # This file - comprehensive project documentation
│
├── .github/                         # GitHub-specific configurations
│   └── workflows/
│       ├── ci.yml                   # Continuous Integration workflow (automated testing on push/PR)
│       └── pages.yml                # GitHub Pages deployment workflow for static site hosting
│
├── config/                          # Application settings and model configuration
│   ├── __init__.py                  # Package initialization for config module
│   └── settings.py                  # Centralized settings: FEATURE_WEIGHTS, simulation defaults, paths
│
├── data/                            # Static 2026 season data and external integrations
│   ├── __init__.py                  # Package initialization for data module
│   ├── calendar_2026.py             # F1 2026 race calendar with dates, circuit IDs, round numbers
│   ├── circuit_data.py              # Circuit characteristics (length, corners, DRS zones, elevation)
│   ├── driver_data.py               # Driver profiles: names, teams, numbers, experience levels
│   ├── driver_traits_database.py    # Historical driver performance traits and statistics
│   ├── teams.py                     # Constructor information: team names, power units, budgets
│   ├── season_2026.py               # Season-specific configuration and metadata
│   ├── fastf1_integration.py        # FastF1 API integration for historical session data ingestion
│   └── _fastf1_cache_fix.py         # Workaround for FastF1 caching issues and data persistence
│
├── engine/                          # Core prediction engine and simulation logic
│   ├── __init__.py                  # Package initialization for engine module
│   ├── predictor.py                 # Main orchestrator: validates inputs, coordinates prediction flow
│   ├── feature_engineering.py       # Computes 8 key signals: ELO, form, reliability, circuit fit
│   ├── probability_model.py         # Monte Carlo prediction logic returning probability distributions
│   ├── vectorized_simulation.py     # NumPy-optimized simulation engine (40x faster than loop-based)
│   ├── optimized_simulation.py      # Alternative simulation implementation with performance tuning
│   ├── multi_dimensional_elo.py     # Multi-dimensional ELO rating system for drivers and teams
│   ├── weather_model_v3.py          # Weather impact modeling using OpenWeatherMap API integration
│   ├── tire_strategy.py             # Tire degradation and pit stop strategy simulation
│   ├── calibration.py               # Platt scaling and Brier score calibration for probability accuracy
│   └── prediction_tracker.py        # Tracks prediction history and stores results in database
│
├── dashboard/                       # Flask web application for interactive visualization
│   ├── __init__.py                  # Package initialization for dashboard module
│   ├── app.py                       # Flask server: routes for predictions, H2H, report downloads
│   └── templates/
│       └── dashboard.html           # Jinja2 template with Plotly.js charts and interactive UI
│
├── database/                        # SQLAlchemy ORM models and data persistence
│   ├── __init__.py                  # Package initialization for database module
│   └── models.py                    # SQLAlchemy models: Prediction, RaceResult, Driver, Team tables
│
├── reports/                         # HTML report generation for race predictions
│   ├── __init__.py                  # Package initialization for reports module
│   └── html_report.py               # Generates standalone HTML reports with embedded charts
│
└── scripts/                         # Maintenance, evaluation, and optimization utilities
    ├── __init__.py                  # Package initialization for scripts module
    ├── data_quality_report.py       # Validates dataset integrity: missing values, consistency checks
    └── post_race_evaluation.py      # Compares predictions against actual results, computes accuracy metrics
```

### Key File Descriptions

**Root Level:**
- [`main.py`](main.py): Primary CLI interface supporting commands like `predict`, `dashboard`, `report`, `h2h`, `optimize-weights`, `migrate-db`, `sync-fastf1`, `evaluate-race`, `accuracy-report`, `championship-sim`, `quality-check`, `backtest`, and `benchmark`
- [`requirements.txt`](requirements.txt): Lists all Python dependencies including numpy, pandas, scikit-learn, flask, sqlalchemy, click, rich, optuna, fastf1, and plotting libraries
- [`.env.example`](.env.example): Template for environment variables including `WEATHER_API_KEY`, `F1_API_KEY`, `FLASK_DEBUG`, `PORT`, and `F1_DATABASE_URL`

**config/**
- [`settings.py`](config/settings.py): Defines `FEATURE_WEIGHTS` dictionary controlling the relative importance of 8 prediction signals (ELO ratings, recent form, circuit suitability, reliability, weather adaptation, tire management, team strength, qualifying pace). Also contains default simulation parameters and file paths.

**data/**
- [`calendar_2026.py`](data/calendar_2026.py): Complete 2026 F1 calendar with 24 races, including circuit IDs, country names, round numbers, and scheduled dates
- [`circuit_data.py`](data/circuit_data.py): Detailed circuit metadata including track length, number of corners, DRS zones, elevation changes, surface type, and historical overtaking difficulty ratings
- [`driver_data.py`](data/driver_data.py): Current driver roster with full names, abbreviations, team assignments, car numbers, and years of F1 experience
- [`driver_traits_database.py`](data/driver_traits_database.py): Historical performance metrics per driver: wet weather skill, tire management, overtaking ability, consistency ratings derived from past seasons
- [`teams.py`](data/teams.py): Constructor details including team principals, power unit suppliers, budget cap status, and historical championship positions
- [`fastf1_integration.py`](data/fastf1_integration.py): Integrates with the official FastF1 library to fetch historical lap times, telemetry, stint data, and race control messages for advanced feature extraction
- [`_fastf1_cache_fix.py`](data/_fastf1_cache_fix.py): Addresses known FastF1 caching bugs that cause data retrieval failures on Windows systems

**engine/**
- [`predictor.py`](engine/predictor.py): Central coordinator that accepts circuit ID and optional overrides (rain probability, grid positions), validates inputs, calls feature engineering, selects simulation backend, and formats output as structured prediction dictionaries
- [`feature_engineering.py`](engine/feature_engineering.py): Transforms raw driver/team/circuit data into 8 normalized feature scores (0-1 scale) used by the probability model. Combines circuit metadata, weather forecasts, driver traits, and recent form into composite scores
- [`probability_model.py`](engine/probability_model.py): Implements the core Monte Carlo simulation algorithm. Takes feature scores and runs thousands of race simulations to produce probability distributions for win, podium, points finish, and DNF outcomes
- [`vectorized_simulation.py`](engine/vectorized_simulation.py): High-performance NumPy implementation of Monte Carlo simulation using array broadcasting and vectorized operations. Achieves ~40x speedup over iterative approach, enabling 10,000+ simulations in under 0.1 seconds
- [`multi_dimensional_elo.py`](engine/multi_dimensional_elo.py): Advanced ELO rating system that tracks driver performance across multiple dimensions (qualifying, race pace, wet conditions, tire management) rather than single aggregate rating
- [`weather_model_v3.py`](engine/weather_model_v3.py): Fetches real-time weather forecasts from OpenWeatherMap API for race weekend. Models impact of rain probability, temperature, wind speed on driver performance based on historical wet weather skills
- [`tire_strategy.py`](engine/tire_strategy.py): Simulates tire degradation curves for soft/medium/hard compounds. Models pit stop timing effects and strategic advantages based on driver tire management ratings
- [`calibration.py`](engine/calibration.py): Implements Platt scaling to calibrate raw simulation probabilities against historical accuracy. Computes Brier scores to measure prediction quality. **Note: Currently uses default parameters (A≈1.0, B≈0.0) pending sufficient training data**
- [`prediction_tracker.py`](engine/prediction_tracker.py): Stores prediction results in SQLite database via SQLAlchemy. Enables post-race evaluation by comparing predicted probabilities against actual outcomes

**dashboard/**
- [`app.py`](dashboard/app.py): Flask web server exposing REST-like endpoints for predictions (`/predict/<circuit_id>`), head-to-head comparisons (`/h2h/<driver1>/<driver2>/<circuit_id>`), constructor standings (`/constructors`), and report downloads (`/download-report/<circuit_id>`). Includes CORS support and rate limiting
- [`templates/dashboard.html`](dashboard/templates/dashboard.html): Single-page application using Jinja2 templating, Bootstrap CSS, and Plotly.js for interactive charts. Displays prediction probabilities as bar charts, pie charts, and comparative visualizations

**database/**
- [`models.py`](database/models.py): Defines SQLAlchemy ORM models for persistent storage. Tables include `predictions` (stores forecast probabilities), `race_results` (actual outcomes for backtesting), `drivers` (driver metadata), `teams` (constructor metadata), and `calibration_history` (tracks Platt scaling parameters over time)

**reports/**
- [`html_report.py`](reports/html_report.py): Generates self-contained HTML reports embedding prediction results, probability charts, and methodology explanations. Reports can be downloaded directly from the dashboard or generated via CLI with `--auto-report` flag

**scripts/**
- [`data_quality_report.py`](scripts/data_quality_report.py): Performs comprehensive validation of season datasets. Checks for missing driver assignments, inconsistent team mappings, duplicate circuit IDs, and round number gaps between calendar and circuit data
- [`post_race_evaluation.py`](scripts/post_race_evaluation.py): After a race concludes, compares stored predictions against actual finishing positions. Computes accuracy metrics including Brier score, log loss, and calibration error. Identifies systematic biases in the model

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
