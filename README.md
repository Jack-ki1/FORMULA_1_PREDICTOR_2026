# F1 Race Outcome Prediction System

A probabilistic, calibrated Formula One race outcome prediction engine using historical data, constructor form, circuit characteristics, and driver-specific metrics.

---

## Features

- **Per-driver probability outputs** — win, top-3, top-10, DNF, teammate-beat
- **Feature engineering pipeline** — recency-weighted form, track-type fit, reliability risk, weather adjustments
- **Calibration module** — Platt scaling and isotonic regression for well-calibrated probabilities
- **REST API** — FastAPI endpoints for race prediction and season-level queries
- **HTML report generator** — full race preview report with charts (Jinja2 + Chart.js)
- **Backtesting harness** — temporal cross-validation across seasons
- **2026 season data pre-loaded** — standings, driver profiles, circuit guide

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Quickstart](#quickstart)
3. [API Endpoints](#api-endpoints)
4. [Prediction Logic](#prediction-logic)
5. [Installation](#installation)
6. [Running Predictions](#running-predictions)
7. [Deployment](#deployment)
8. [Season Maintenance](#season-maintenance)
9. [Backtesting](#backtesting)
10. [Testing](#testing)
11. [Performance Tips](#performance-tips)
12. [Common Issues](#common-issues)
13. [License](#license)

---

## Project Structure

```
f1-prediction-system/
├── README.md
├── requirements.txt
├── .env.example
├── main.py                        ← CLI entrypoint (predict, report, backtest)
├── config/
│   └── settings.py                ← All config constants
├── data/
│   ├── __init__.py
│   ├── driver_data.py             ← 2026 driver profiles + season stats
│   ├── circuit_data.py            ← Circuit characteristics + historical SC rates
│   └── season_2026.py             ← Race-by-race 2026 results so far
├── engine/
│   ├── __init__.py
│   ├── predictor.py               ← Main prediction orchestrator
│   ├── feature_engineering.py     ← Feature computation (form, track-fit, etc.)
│   ├── probability_model.py       ← Logistic model + ELO ratings
│   └── calibration.py             ← Calibration + temporal cross-validation
├── api/
│   ├── __init__.py
│   ├── routes.py                  ← FastAPI route handlers
│   └── schemas.py                 ← Pydantic request/response models
├── reports/
│   ├── __init__.py
│   ├── html_report.py             ← Report generator
│   └── templates/
│       └── report.html            ← Jinja2 HTML template
├── tests/
│   ├── __init__.py
│   ├── test_predictor.py
│   └── test_feature_engineering.py
└── scripts/
    ├── run_canada_gp_2026.py      ← One-shot Canadian GP prediction script
    └── backtest_2025_season.py    ← Full 2025 season backtest
```

---

## Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Predict a race
```bash
python main.py predict --race canada_2026
#or
py main.py predict --race canada_2026
```

### 3. Generate HTML report
```bash
python main.py report --race canada_2026 --output ./canada_gp_report.html
#or
py main.py report --race canada_2026 --output ./canada_gp_report.html
```

### 4. Start the API server
```bash
python main.py api
#or
py main.py api
# → http://localhost:8000/docs
```

### 5. Run backtests
```bash
python main.py backtest --seasons 2023 2024 2025
#or
py main.py backtest --seasons 2023 2024 2025
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
|--------|----------|-------------|
| GET | `/predict/{race_id}` | Full race prediction |
| GET | `/predict/{race_id}/winner` | Win probabilities only |
| GET | `/predict/{race_id}/dnf` | DNF risk per driver |
| GET | `/standings` | Current championship standings |
| GET | `/circuits` | Circuit guide with characteristics |
| POST | `/simulate` | Custom simulation with override params |

---

## Prediction Logic

1. **Baseline** — ELO-style driver ratings + constructor strength index
2. **Track fit** — circuit-type score per driver/team (power, technical, street)
3. **Recent form** — exponentially weighted last-N-races performance
4. **Qualifying** — grid-position-to-finish conversion model
5. **Reliability** — team-specific DNF rate, component failure priors
6. **Weather** — rain probability adjustment on driver wet-weather record
7. **Safety car** — circuit-specific SC frequency boosts mid-grid chances
8. **Teammate comparison** — head-to-head qualifying and race delta

---

## Anti-Leakage Rules

The predictor strictly refuses to use:
- Any data after `race_start_timestamp`
- Post-race penalties or steward decisions
- Race-day weather updates (only pre-race forecast)
- In-race incidents or strategy pivots

---

## Calibration & Evaluation

- Temporal cross-validation only (no random shuffle)
- Brier score, log-loss, and ranked probability score (RPS)
- Calibration curves per probability bucket
- Feature importance via permutation testing

---

## Installation

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.12 recommended |
| pip | 23+ | `pip install --upgrade pip` |
| Git | any | For cloning / CI/CD |
| Node.js | optional | Only needed if editing the web frontend |

### Setup Process

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/f1-prediction-system.git
cd f1-prediction-system

# Create and activate a virtual environment (strongly recommended)
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows PowerShell

# Install all dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your values if needed (optional for basic use)
```

---

## Running Predictions

### Quickest path — one command

```bash
python scripts/run_canada_gp_2026.py
```
This prints a full Rich-formatted table + saves an HTML report to `./output/`.

### CLI — full options

```bash
# Basic prediction (dry conditions assumed)
python main.py predict --race canada

# Wet race scenario (55% rain probability)
python main.py predict --race canada --rain 0.55

# More simulations for higher precision (slower)
python main.py predict --race canada --sims 20000

# Output raw JSON (pipe to jq, save to file, etc.)
python main.py predict --race canada --json-out

# Generate standalone HTML report
python main.py report --race canada
python main.py report --race canada --output ./my_canada_report.html

# Available circuit IDs (2026 season)
# canada  australia  china  monaco  (add more in data/circuit_data.py)
```

### REST API

```bash
# Start the server
python main.py api

# With hot-reload (development)
python main.py api --reload

# Custom host/port
python main.py api --host 127.0.0.1 --port 9000
```

Then open:
- **Interactive docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Key API calls:
```bash
# Full prediction
curl http://localhost:8000/api/v1/predict/canada

# Win probabilities only (fast)
curl http://localhost:8000/api/v1/predict/canada/winner

# DNF risk
curl http://localhost:8000/api/v1/predict/canada/dnf

# With rain override
curl "http://localhost:8000/api/v1/predict/canada?rain_probability=0.60"

# Driver standings
curl http://localhost:8000/api/v1/standings/drivers

# Constructor standings
curl http://localhost:8000/api/v1/standings/constructors
```

---

## Deployment

### Deploying to GitHub Pages

#### Architecture Overview

```
GitHub Repository
│
├── data/ + engine/        ← Python prediction system
│
└── .github/workflows/
    └── deploy.yml          ← Runs every Thursday + on data changes
            │
            ▼
    Python runs prediction engine
            │
            ▼
    Generates web/ (static HTML + JSON)
            │
            ▼
    GitHub Pages serves web/
            │
            ▼
    https://YOUR_USERNAME.github.io/f1-prediction-system/
```

The workflow generates a **fully static site** — no server required.
Chart.js is loaded from CDN. Predictions are pre-computed JSON files.

### Step 1 — Create the GitHub Repository

```bash
# If you haven't already initialised git
cd f1-prediction-system
git init
git add .
git commit -m "Initial commit — F1 Prediction System"

# Create repo on GitHub (use GitHub CLI or website)
gh repo create f1-prediction-system --public
# or: create manually at https://github.com/new

# Push
git remote add origin https://github.com/YOUR_USERNAME/f1-prediction-system.git
git branch -M main
git push -u origin main
```

### Step 2 — Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (left sidebar)
3. Under **Source**, select **GitHub Actions**
4. Save

That's it. The `deploy.yml` workflow will now deploy to Pages automatically.

### Step 3 — Trigger the First Deployment

Option A — automatic:
- Push any change to `main` that touches a file in `data/` or `engine/`

Option B — manual trigger:
1. Go to **Actions** tab in your repository
2. Click **"Deploy F1 Predictions to GitHub Pages"**
3. Click **"Run workflow"**
4. Fill in optional parameters and click **"Run workflow"**

The deployment takes about 2–3 minutes. Your site will be live at:
```
https://YOUR_USERNAME.github.io/f1-prediction-system/
```

### Step 4 — Verify the Deployment

After the workflow completes:
- ✅ Green checkmark in Actions tab
- Visit your GitHub Pages URL
- You should see the prediction dashboard with:
  - Next race card with predicted podium
  - Driver standings table
  - Win probability chart
  - Full calendar

### Workflow Triggers

The deploy workflow runs automatically when:

| Trigger | When |
|---------|------|
| **Scheduled** | Every Thursday at 09:00 UTC (before most race weekends) |
| **Push to main** | Whenever `data/`, `engine/`, or `config/` files change |
| **Manual dispatch** | Anytime from Actions tab with custom parameters |

### Manual Deployment with Custom Parameters

From the Actions tab → "Deploy F1 Predictions to GitHub Pages" → "Run workflow":

| Parameter | Description | Example |
|-----------|-------------|---------|
| `rain_probability` | Override rain chance | `0.65` for wet Monaco |
| `simulations` | Monte Carlo runs | `10000` for high precision |

This is useful for race-weekend previews with updated weather forecasts.

### Customising the Published Site

#### Change the site title / branding

Edit the `<title>` and `<header>` in `scripts/generate_static_site.py`:
```python
# In write_index_html():
html = f"""...
<title>F1 2026 — My Prediction Model</title>
...
<H1>🏁 My F1 2026 Picks</H1>
...
"""
```

#### Add a custom domain

1. Buy a domain (e.g. `f1picks.com`)
2. In repo Settings → Pages → Custom domain: enter your domain
3. Add these DNS records at your registrar:
   ```
   CNAME  www   YOUR_USERNAME.github.io
   A      @     185.199.108.153
   A      @     185.199.109.153
   A      @     185.199.110.153
   A      @     185.199.111.153
   ```
4. Check "Enforce HTTPS" in Pages settings
5. Create `web/CNAME` file containing your domain:
   ```
   www.f1picks.com
   ```

### File Structure After Deployment

```
web/                            ← Published as GitHub Pages root
├── index.html                  ← Main dashboard
├── predictions/
│   ├── canada.json
│   ├── monaco.json
│   └── ... (one per circuit)
└── assets/
    └── data.json               ← Full aggregate data for custom integrations
```

JSON files are publicly accessible:
```
https://YOUR_USERNAME.github.io/f1-prediction-system/assets/data.json
https://YOUR_USERNAME.github.io/f1-prediction-system/predictions/canada.json
```

This makes the system usable as a free public API.

### On-Demand Race Reports (PDF/HTML download)

The `predict.yml` workflow lets anyone with repo access generate a report:

1. Go to **Actions** → **"On-Demand Race Prediction"**
2. Click **"Run workflow"**
3. Enter circuit ID, rain probability, simulation count
4. After completion, download the HTML report from **Artifacts**

The artifact includes:
- `prediction_CIRCUIT.json` — raw prediction data
- `CIRCUIT_report.html` — styled standalone report

### Keeping the Deployed Site Fresh

The site auto-updates on Thursdays. For race weekends:

1. After qualifying (Saturday):
   ```bash
   # Update any grid position overrides if needed
   # Push changes to main → auto-deploys
   git add data/season_2026.py
   git commit -m "Update: Canada qualifying grid"
   git push
   ```

2. After the race (Sunday):
   ```bash
   python scripts/post_race_update.py --round 5 --circuit canada \
     --results "antonelli:1,russell:2,norris:3,..."
   git add data/season_2026.py
   git commit -m "Results: Canadian GP R5"
   git push
   # → Auto-deploys updated site within ~3 minutes
   ```

### Secrets & Environment Variables

For optional features (weather API, live data sync), add secrets in:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Description |
|-------------|-------------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key for weather forecasts |
| `ERGAST_API_BASE` | Override default Ergast endpoint |

Reference in workflows:
```yaml
env:
  OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
```

### Monitoring & Alerts

Set up email notifications for failed deployments:
1. **Settings → Notifications → Actions**
2. Enable "Send notifications for failed workflows"

You'll get an email if the Thursday deploy fails (e.g. due to a Python error
after a data update).

---

## Season Maintenance

### The Maintenance Cycle

```
BEFORE EACH RACE WEEKEND          DURING WEEKEND          AFTER RACE
────────────────────────────      ──────────────────────  ─────────────────────
□ Verify circuit is in DB         □ Run final prediction  □ Add race results
□ Check driver lineup changes     □ Note weather update   □ Update ELO ratings
□ Apply any car upgrade flags     □ (no model changes)    □ Save historical snapshot
□ Update qualifying data (Sat)                            □ Re-run next-race preview
□ Run final pre-race prediction
```

### 1 — After Every Race: Add Results to `data/season_2026.py`

Open `data/season_2026.py` and append a new entry to `SEASON_RESULTS_2026`:

```python
{
    "round": 5,
    "circuit": "canada",
    "name": "Canadian Grand Prix",
    "date": "2026-05-24",
    "sprint": True,
    "results": [
        {"driver": "antonelli", "position": 1, "grid": 1, "points": 25, "dnf": False, "fastest_lap": True},
        {"driver": "russell",   "position": 2, "grid": 2, "points": 18, "dnf": False, "fastest_lap": False},
        # ... all drivers
        {"driver": "leclerc",   "position": None, "grid": 3, "points": 0, "dnf": True, "fastest_lap": False,
         "note": "DNF — Wall of Champions"},
    ],
},
```

Then update `DRIVER_STANDINGS_AFTER_R4` → rename to `DRIVER_STANDINGS_AFTER_R5` and
update every driver's points total. Similarly update `CONSTRUCTOR_STANDINGS_AFTER_R4`.

> **Shortcut:** use the post-race update script:
> ```bash
> python scripts/post_race_update.py --round 5 --circuit canada \
>   --results "antonelli:1,russell:2,norris:3"
> ```

### 2 — Update Driver ELO Ratings

ELO should be recalculated after each race based on finishing order vs. expected order.

In `data/driver_data.py`, update the `"elo"` field for each driver.

**Formula used:**

```
expected_score  = 1 / (1 + 10^((opponent_elo - driver_elo) / 400))
actual_score    = 1 if beat opponent else 0
new_elo         = old_elo + K * (actual_score - expected_score)
K = 32 (configurable in config/settings.py)
```

The post-race script computes this automatically:
```bash
python scripts/post_race_update.py --round 5 --update-elo
```

### 3 — Update Recent Form Scores

`driver["recent_form"]` is a list of finishing positions, most recent first.
After each race, **prepend** the new result and **drop the oldest** if the list
exceeds `RECENCY_WINDOW` (default 8):

```python
# Before Canada (R5):
"recent_form": [1, 1, 1, 2]    # Miami, Japan, China, Australia

# After Canada (assuming P1):
"recent_form": [1, 1, 1, 1, 2] # Canada, Miami, Japan, China, Australia
```

### 4 — Mid-Season Driver/Team Changes

#### Driver substitution (injury, replacement, etc.)
1. Mark the original driver as inactive (add `"active": False`)
2. Add the replacement driver entry to `data/driver_data.py`
3. Set replacement's `experience_races` and `elo` appropriately
4. Add team-mate notes

#### Car upgrades
When a team announces a confirmed upgrade package:
1. Increase their `_CONSTRUCTOR_STRENGTH` value in `engine/feature_engineering.py`
2. Add a note with the round number

```python
_CONSTRUCTOR_STRENGTH: dict = {
    "mercedes": 0.96,
    "mclaren":  0.85,  # ← Updated after R6 upgrade package (Monaco)
    ...
}
```

#### Power unit changes / grid penalties
These are handled per-race via grid position overrides in the prediction CLI:
```bash
# Verstappen takes 5-place grid penalty → start P8 instead of P3
python main.py predict --race monaco --grid-override "verstappen:8"
```

### 5 — Add New Circuits Each Round

For each upcoming race, add a circuit entry to `data/circuit_data.py`:

```python
"silverstone": {
    "id": "silverstone",
    "name": "Silverstone Circuit",
    "city": "Silverstone",
    "country": "United Kingdom",
    "round_2026": 10,
    "race_date": "2026-07-06",
    "sprint_weekend": False,
    "circuit_type": ["balanced"],
    "lap_count": 52,
    "lap_distance_km": 5.891,
    "total_distance_km": 306.198,
    "safety_car_probability": 0.52,
    "overtaking_difficulty": 5,
    "power_unit_demand": 7.5,
    "brake_demand": 7.0,
    "tire_deg_rate": 8.5,
    "active_aero_demand": 7.5,
    "rain_probability_typical": 0.45,
    "wall_crash_probability_per_lap": 0.002,
    "drs_zones": 2,
    "team_historical_wins_since_2010": {
        "mercedes": 11, "red_bull": 5, "ferrari": 2, "mclaren": 3
    },
}
```

> **Tip:** Copy the closest circuit type as a template and adjust values.
> The 2026 full calendar is in `data/calendar_2026.py`.

### 6 — Quarterly Model Recalibration

Every ~6 races, run the calibration check:

```bash
python scripts/recalibrate_model.py
```

This will:
- Compare predicted probabilities vs. actual outcomes for all completed races
- Output Brier scores, log-loss, and calibration curve data
- Suggest updated Platt scaling parameters
- Recommend feature weight adjustments

Apply the suggested changes to:
- `config/settings.py` → `FEATURE_WEIGHTS`
- `engine/probability_model.py` → `PLATT_A_WIN`, `PLATT_B_WIN`

### 7 — End of Season: Archive and Prepare for 2027

#### Step 1 — Archive 2026 data
```bash
python scripts/archive_season.py --season 2026
# Creates data/historical/2026/ with all race snapshots
```

#### Step 2 — Create 2027 season files
```bash
cp data/season_2026.py data/season_2027.py
# Empty the SEASON_RESULTS and reset standings to 0
```

#### Step 3 — Update driver roster
For 2027, typical changes to handle:
- Driver seat changes (announced ~September of current year)
- New rookie entries
- Retirement declarations
- Team name changes

Update `data/driver_data.py`:
```python
# Mark retired drivers
"hamilton": {
    ...
    "active_2027": False,  # Add this flag
}

# Add new drivers
"new_rookie": {
    "id": "new_rookie",
    "name": "New Rookie",
    "elo": 1480,           # Start at below-average ELO
    "experience_races": 0,
    # ... fill in profile from F2/junior data
}
```

#### Step 4 — Reset ELO with decay
Apply a 10% decay toward the mean (1500) to prevent over-anchoring:
```bash
python scripts/reset_elo_new_season.py --decay 0.10
```

#### Step 5 — Refit calibration on full 2026 data
```bash
python scripts/recalibrate_model.py --season 2026 --fit-platt
# Updates PLATT_A_WIN, PLATT_B_WIN, PLATT_A_TOP3 in probability_model.py
```

### 8 — Data Sources to Monitor

| Source | What to watch | Update frequency |
|--------|--------------|------------------|
| Formula1.com | Official results, grid penalties | After each session |
| Ergast API | Machine-readable results (free) | ~2hrs after race |
| Autosport / RaceFans | Upgrade confirmations | Weekly |
| FIA documents | Post-race steward decisions | Race weekend |
| Team social media | Driver changes, car livery updates | As announced |
| AccuWeather / Meteoblue | Pre-race weather forecasts | Thursday–Sunday |

#### Ergast API integration (optional but powerful)

Set `ERGAST_API_BASE` in `.env` and run:
```bash
python scripts/sync_from_ergast.py --round 5
# Auto-populates results from the official API after each race
```

### 9 — Feature Tuning Cheatsheet

| Signal weakening? | Action |
|-------------------|--------|
| Grid position not predicting well | Reduce `grid_position` weight, increase `recent_form` |
| Rookie form underestimated | Increase `elo_rating` weight for drivers with <10 races |
| Safety car races breaking predictions | Increase `safety_car_upside` weight |
| Wet races unpredictable | Increase `weather_adjustment` weight, raise `wet_skill` precision |
| DNF rates outdated | Update `dnf_rate_recent` from last 6 races |

### 10 — Season Timeline Checklist

```
March     □ Season launch — verify all 20 drivers + 24 circuits loaded
          □ Reset ELO from 2025 final values
          □ Set constructor strength baselines

April–May □ After R1-R4: validate model calibration, adjust if Brier > 0.06
          □ Mid-season upgrade tracker active

June–Aug  □ Quarterly recalibration run
          □ Summer break: prepare remaining calendar circuits

Sept–Oct  □ Final standings verification
          □ Archive season data
          □ Begin 2027 roster updates

November  □ End-of-season ELO decay
          □ Refit Platt scaling on full season
          □ Update README with 2027 instructions
```

---

## Backtesting

### Running Backtests

```bash
# Run the backtest demo (synthetic data if no historical data present)
python scripts/backtest_2025_season.py

# With historical data in data/historical/2025/
# See data/historical/README.md for the expected file format
python main.py backtest --seasons 2025
```

### Historical Data Format

This directory stores pre-race prediction snapshots and post-race outcomes
for backtesting and model calibration.

#### Directory Structure

```
data/historical/
├── README.md          ← This file
├── 2025/
│   ├── round_01_bahrain_predictions.json
│   ├── round_01_bahrain_outcomes.json
│   ├── round_02_jeddah_predictions.json
│   ├── round_02_jeddah_predictions.json
│   └── ...
└── 2026/
    ├── round_01_australia_predictions.json
    ├── round_01_australia_outcomes.json
    └── ...
```

#### File Formats

##### `*_predictions.json`
```json
[
  {
    "round": 1,
    "driver_id": "antonelli",
    "win_prob": 0.42,
    "top3_prob": 0.78,
    "top10_prob": 0.94
  },
  ...
]
```

##### `*_outcomes.json`
```json
[
  {
    "round": 1,
    "driver_id": "antonelli",
    "position": 1
  },
  {
    "round": 1,
    "driver_id": "russell",
    "position": 2
  },
  ...
]
```

#### Generating Snapshots Automatically

After each race, the post_race_update.py script auto-generates outcome files:
```bash
python scripts/post_race_update.py --round 1 --circuit australia --results "antonelli:1,russell:2,..."
# Creates: data/historical/2026/round_01_australia_outcomes.json
```

For prediction snapshots (pre-race), run the predictor on Thursday and save:
```bash
python main.py predict --race australia --json-out > \
  data/historical/2026/round_01_australia_predictions.json
```

#### Using for Backtesting
```python
from engine.calibration import temporal_cross_validate
# See scripts/backtest_2025_season.py for full usage
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# Run a specific test file
pytest tests/test_predictor.py -v

# Run with coverage report
pip install pytest-cov
pytest --cov=engine --cov-report=term-missing
```

---

## Performance Tips

- **Fast mode:** `--sims 500` for instant results (less accurate)
- **Precision mode:** `--sims 25000` for publication-quality probabilities
- **Batch predictions:** Loop over circuits in a shell script
  ```bash
  for race in canada monaco silverstone; do
    python main.py predict --race $race --json-out >> predictions_batch.jsonl
  done
  ```

---

## Common Issues

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Make sure venv is activated and `pip install -r requirements.txt` was run |
| `KeyError: 'canada'` | Ensure the circuit is in `data/circuit_data.py` |
| `KeyError: 'antonelli'` | Ensure the driver is in `data/driver_data.py` |
| Slow predictions | Reduce `--sims` to 1000 for quick checks |
| API port already in use | `python main.py api --port 9000` |
| HTML report not opening | Open from a web server, not `file://` (Chart.js CDN needed) |

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `8000` | API bind port |
| `API_DEBUG` | `false` | Enable debug mode |
| `MODEL_RECENCY_WINDOW` | `8` | Last N races weighted in form |
| `MODEL_ELO_K_FACTOR` | `32` | ELO update magnitude |
| `MODEL_DNF_SMOOTHING` | `0.1` | Laplace smoothing for rare DNFs |
| `REPORT_OUTPUT_DIR` | `./output` | Where HTML reports are saved |
| `ERGAST_API_BASE` | Ergast URL | Live F1 data API (optional) |
| `OPENWEATHER_API_KEY` | — | Weather forecast (optional) |

---

## Project Layout Quick Reference

```
f1-prediction-system/
├── main.py                    ← START HERE for CLI
├── config/settings.py         ← Tune weights and constants here
├── data/
│   ├── driver_data.py         ← Update after driver changes
│   ├── circuit_data.py        ← Add circuits for upcoming rounds
│   └── season_2026.py         ← Add race results after each round
├── engine/
│   ├── feature_engineering.py ← Core feature computation
│   ├── probability_model.py   ← Monte Carlo simulation
│   ├── predictor.py           ← Orchestrator
│   └── calibration.py        ← Backtesting & calibration
├── scripts/
│   ├── run_canada_gp_2026.py  ← One-shot race prediction
│   ├── post_race_update.py    ← Add results after each race
│   └── generate_static_site.py← Build GitHub Pages site
├── web/                       ← GitHub Pages static site
└── .github/workflows/         ← CI/CD automation
```

---

## License

MIT