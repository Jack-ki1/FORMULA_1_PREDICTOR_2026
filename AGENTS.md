# F1 Predictor 2026 - Project Guide

## Project Overview

This is a comprehensive Formula 1 race prediction system for the 2026 season, featuring ML-based predictions, live data integration, and interactive dashboards.

## Build Status

✅ **Project Structure**: Complete folder structure (see tree below)
✅ **Configuration**: All config modules (settings, API settings, feature weights, constants, team/driver lineup)
✅ **Data Foundation**: Calendar, driver data, team data, circuit data, season data
✅ **API Clients**: Generic client, Jolpica, OpenF1, FastF1, Hugging Face integration
✅ **Prediction Engine**: Feature engineering, ML models, probability model, main predictor
✅ **Advanced Models**: Elo calculator, Monte Carlo simulator, grid model, pit strategy, tire model, weather model, safety car model, ensemble predictor, calibration
✅ **Database**: SQLAlchemy models and connection management
✅ **Flask Dashboard**: 7 blueprints (landing, predictions, standings, H2H, constructors, analytics/settings, reports)
✅ **Templates & Static Assets**: HTML templates, CSS styles, JavaScript files
✅ **Reports Module**: CSV/Excel, PDF, and share card generators
✅ **Utility Scripts**: Migration, seeding, accuracy measurement, calibration, weight optimization, post-race evaluation, data quality reporting
✅ **Fantasy Scoring**: Real F1 Fantasy rules implementation
✅ **Main Entry Point**: main.py with Flask app and background schedulers
✅ **Tests**: Test suite for probability model, grid model, fantasy scoring, API clients

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/migrate_db.py
python scripts/seed_2026_calendar.py
```

### Running the Application

```bash
python main.py
```

The dashboard will be available at `http://localhost:5000`

## Project Structure

```
f1_predictor_2026/
├── main.py                          # Application entry point
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── .dockerignore
├── .env.example
├── README.md
├── NEXT_SEASON_MIGRATION_GUIDE.md
│
├── cache/
│   ├── api_responses/               # Raw API JSON with TTL
│   ├── fastf1_cache/                # FastF1 on-disk cache
│   └── model_cache/                 # Trained model artifacts
│
├── config/
│   ├── settings.py                  # Season year, debug flag, cache TTLs
│   ├── api_settings.py              # API base URLs, retry/backoff, rate limits
│   ├── feature_weights.py           # Model tuning parameters (chaos, wet, reliability, strategy, grid)
│   ├── constants.py                 # Team colors, Pirelli compounds, F1 points, target definitions
│   └── team_driver_lineup_2026.py   # 11 teams / 22 drivers with attributes
│
├── dashboard/
│   ├── app.py                       # Flask app factory
│   ├── blueprints/
│   │   ├── landing.py               # Landing page
│   │   ├── predictions.py           # Main prediction dashboard
│   │   ├── standings.py             # Driver/constructor standings
│   │   ├── h2h.py                   # Head-to-head comparison
│   │   ├── constructors.py          # Team performance analysis
│   │   ├── analytics_settings.py    # Accuracy metrics and parameter tuning
│   │   └── reports.py               # Export functionality
│   ├── static/
│   │   ├── css/styles.css
│   │   ├── js/
│   │   │   ├── common.js
│   │   │   ├── dashboard.js
│   │   │   ├── charts.js
│   │   │   ├── grid_editor.js
│   │   │   └── theme_toggle.js
│   │   └── img/
│   └── templates/
│       ├── base.html                # Shared layout
│       ├── landing.html
│       ├── dashboard.html
│       ├── standings.html
│       ├── h2h.html
│       ├── constructors.html
│       ├── analytics_settings.html
│       └── reports.html
│
├── data/
│   ├── calendar_2026.py              # 23-round 2026 calendar
│   ├── driver_data.py                # Driver biographies
│   ├── team_data.py                  # Team statistics
│   ├── circuit_data.py               # Circuit specifications
│   ├── season_2026.py                # Season-to-date results
│   ├── api_client.py                 # Generic HTTP client with caching
│   ├── jolpica_client.py             # Standings/results/qualifying data
│   ├── openf1_client.py              # Live session and telemetry data
│   ├── fastf1_integration.py         # Lap-by-lap telemetry data
│   ├── huggingface_dataset.py        # Historical race data archive
│   └── live_updater.py               # Background data refresh scheduler
│
├── engine/
│   ├── predictor.py                  # Main prediction orchestrator
│   ├── feature_engineering.py        # Feature matrix generation
│   ├── ml_models.py                  # Model zoo (GB, RF, Logistic Regression)
│   ├── probability_model.py          # Probability shaping with chaos level
│   ├── ensemble_predictor.py         # Ensemble combination
│   ├── elo_calculator.py             # Driver skill rating system
│   ├── monte_carlo.py                # Race simulation engine
│   ├── grid_model.py                 # Qualifying-to-grid conversion
│   ├── pit_strategy.py               # Pit stop prediction
│   ├── tire_model.py                 # Tire degradation modeling
│   ├── weather_model.py              # Weather effects on performance
│   ├── safety_car_model.py           # Safety car probability modeling
│   ├── fantasy_scoring.py            # Real F1 Fantasy rules
│   ├── benchmark_suite.py            # Backtesting and accuracy evaluation
│   └── calibration.py                # Probability calibration
│
├── database/
│   ├── models.py                     # SQLAlchemy models
│   └── connection.py                  # Database connection and session management
│
├── reports/
│   ├── csv_excel_report.py
│   ├── pdf_generator.py
│   └── share_card_generator.py
│
├── scripts/
│   ├── migrate_db.py
│   ├── seed_2026_calendar.py
│   ├── measure_accuracy.py
│   ├── calibrate_probabilities.py
│   ├── optimize_weights.py
│   ├── post_race_evaluation.py
│   ├── data_quality_report.py
│   └── generate_results_template.py
│
└── tests/
    ├── test_ai_client.py
    ├── test_dashboard_blueprints.py
    └── test_predictor.py
```

## Key Features

- **ML-Powered Predictions**: Gradient boosting with ensemble methods
- **Live Data Integration**: Jolpica (standings/results), OpenF1 (live timing), FastF1 (telemetry)
- **Tunable Model Parameters**: Chaos level, wet-weather influence, reliability factors, strategy aggressiveness, grid weight
- **Grid Position Modeling**: Real qualifying results with manual override and empirical pole-to-win weighting (~43%)
- **Fantasy Scoring**: Real F1 Fantasy rules implementation
- **Championship Tracking**: Live driver and constructor standings
- **Export Reports**: CSV, JSON, PDF, and shareable summary cards
- **Multiple Dashboard Views**: Dashboard, Standings, H2H, Constructors, Analytics & Settings, Reports

## API Integration Status

| Source | Status | Notes |
|--------|--------|-------|
| Jolpica | ✅ Live | Standings, per-round results, qualifying data |
| OpenF1 | ✅ Available | Live session & timing (new for 2026) |
| FastF1 | ✅ Available | Lap-by-lap telemetry for practice/qualifying |
| Hugging Face | ✅ Available | Historical race data archive (tracinginsights/RaceData) |

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_predictor.py

# Run with coverage
pytest tests/ --cov=engine --cov-report=html
```

## Available Scripts

- `python scripts/migrate_db.py` - Initialize database schema
- `python scripts/seed_2026_calendar.py` - Load 2026 calendar and roster
- `python scripts/measure_accuracy.py` - Evaluate model accuracy
- `python scripts/calibrate_probabilities.py` - Calibrate probability outputs
- `python scripts/optimize_weights.py` - Optimize feature weights
- `python scripts/post_race_evaluation.py` - Resolve user picks after races
- `python scripts/data_quality_report.py` - Check data quality and coverage
- `python scripts/generate_results_template.py` - Create race results entry template

## Docker Deployment

```bash
# Build image
docker build -t f1-predictor-2026 .

# Run container
docker run -p 5000:5000 f1-predictor-2026
```

## Environment Variables

Key variables in `.env`:
- `SEASON_YEAR` - Current season (default: 2026)
- `DEBUG` - Debug mode (default: False)
- `DATABASE_URL` - Database connection string
- `JOLPICA_BASE_URL` - Jolpica API endpoint
- `OPENF1_BASE_URL` - OpenF1 API endpoint
- `LIVE_UPDATE_INTERVAL` - Background refresh interval in seconds

## Model Performance

Target accuracies (backtested on historical data):
- **Podium**: 89% (vs 13.6% random baseline)
- **Points**: 81% (vs 45.5% random baseline)
- **Winner**: 58% (vs 4.5% random baseline)
- **Q3**: 74% (vs 45.5% random baseline)

## Next Season Migration

See `NEXT_SEASON_MIGRATION_GUIDE.md` for detailed instructions on migrating to the 2027 season.

## Support

For issues or questions, please refer to `AUDIT.md` for known issues and their status, or the `docs/` directory for architecture notes.
