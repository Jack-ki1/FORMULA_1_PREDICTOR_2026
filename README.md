# F1MLpredictions2026 — Formula One 2026 Race Outcome Prediction System

## Overview

The goal of this repository is to generate **probabilistic** predictions for Formula One 2026 race outcomes (and related events) rather than single-point forecasts. Instead of answering “who wins?”, it answers questions like:

- What is the probability each driver wins?
- What is the probability each driver finishes on the podium?
- What is the probability each driver finishes in the top 10?
- What is the probability each driver does **not** finish (DNF)?
- How likely is each driver to beat their teammate?

To do that reliably, the project combines:

1. **Driver strength** (ELO-style dynamic ratings)
2. **Constructor strength** (team-level performance baseline)
3. **Recency / recent form** (exponentially- or window-weighted recent results)
4. **Circuit fit** (track-type characteristics matched to driver/team profiles)
5. **Qualifying-to-race conversion** (grid position correlation)
6. **Reliability / DNF modeling** (team- and driver-informed risk)
7. **Weather / wet-race adjustments** (controlled by rain probability)
8. **Safety car logic** (circuit-specific SC likelihood effects)
9. **Teammate comparison** (head-to-head delta)

It also supports **calibration** so that predicted probabilities behave like real probabilities over time.

---

## Why a “probability engine” (and not just a regressor)

Formula One outcomes are inherently noisy because of:

- collisions and incidents
- strategy variation
- reliability variance
- safety car timing
- weather volatility

A Monte Carlo / simulation approach is well-suited to this. By simulating race dynamics many times, the model estimates a full distribution of outcomes. From that distribution we compute probabilities for win/podium/top-10/DNF.

Additionally, this project includes calibration logic so that if a driver is predicted to win with probability 0.25, they actually win about 25% of the time in comparable situations.

---

## Key capabilities

### 1) Predictions
For a given race/circuit (e.g., `canada`) the engine produces per-driver probability outputs:

- **win** probability
- **top-3** probability
- **top-10** probability
- **DNF** probability
- **teammate beat** probability

Depending on the output format, the engine may also return intermediate feature values.

### 2) Calibration
The engine uses probability calibration methods (e.g., Platt scaling and/or isotonic regression) so output probabilities are not merely “relative scores”, but meaningful probabilities.

### 3) HTML reports
A race preview can be generated as a standalone HTML report (Jinja2 + charts). This is designed for human review.

### 4) REST API
A FastAPI server exposes prediction endpoints so other tools (or your own frontend) can query the model.

### 5) Backtesting / evaluation
You can evaluate the model’s predictive performance over time (temporal validation) using prior seasons.

### 6) Season maintenance tooling
Scripts exist to update post-race data (ELO changes, recent form changes, standings snapshot updates, etc.).

---

## Project layout

This repository is organized into the following main folders:

- **`data/`**
  - driver profiles & driver/team statistics (ELO, recent form history, reliability expectations)
  - circuit definitions (track characteristics, safety car probability, rain characteristics)
  - season data snapshots (race results + standings up to a given round)

- **`engine/`**
  - **`feature_engineering.py`**: creates numeric features from the pre-race data
  - **`probability_model.py`**: runs the race simulation and converts outputs into probabilities
  - **`predictor.py`**: orchestrates feature computation + simulation + calibration
  - **`calibration.py`**: calibration utilities / evaluation routines

- **`api/`**
  - **`routes.py`**: FastAPI route handlers
  - **`schemas.py`**: request/response models (Pydantic)

- **`reports/`**
  - HTML report generation (templates + chart rendering)

- **`scripts/`**
  - one-off scripts (race preview, backtests, recalibration, post-race updates)
  - data quality reporting (ensures the data is internally consistent)

- **`tests/`**
  - unit tests for feature engineering and prediction bounds/logic

---

## Installation

### Prerequisites

| Requirement | Recommended | Notes |
|---|---:|---|
| Python | 3.10+ | 3.12 recommended for speed and ecosystem compatibility |
| pip | latest | `pip install --upgrade pip` |
| Git | any | For cloning / CI |

### Setup steps

```bash
# 1) Clone
git clone https://github.com/YOUR_USERNAME/f1-prediction-system.git
cd f1-prediction-system

# 2) Create venv (recommended)
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Optional env file
# (copy .env.example -> .env if present in your repo)
cp .env.example .env
```

---

## Quickstart: run a prediction

### 1) One-shot script (example: Canada)

This is the simplest flow for local experimentation:

```bash
python scripts/run_canada_gp_2026.py
```

Typical behavior:
- prints a Rich-formatted summary table in the terminal
- generates an HTML report under `./output/` (or another configured output folder)

---

## CLI: main entry point

The repository uses `main.py` as the CLI entry point.

### 1) Predict a single circuit

```bash
python main.py predict --circuit canada
```

Important CLI flags:

- `--circuit <id>`
  - circuit id (must exist in `data/circuit_data.py`)
- `--rain-prob <float>`
  - optional override for rain probability (0.0–1.0)
- `--sim-count <int>`
  - number of Monte Carlo simulations (higher is slower but smoother)
- `--seed <int>`
  - deterministic simulations for debugging / reproducibility
- `--output-format {full,summary,intermediate,winner_only}`
  - controls what’s returned
- `--include-intermediate`
  - includes intermediate artifacts in output
- `--save-file <path>`
  - saves detailed JSON results to disk

### 2) Run the API server

```bash
python main.py api
```

After startup, open:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Notes:
- This project uses FastAPI.
- Debug/reload and host/port are configured via CLI and/or environment variables.

### 3) Run data quality report

```bash
python main.py quality-check
```

This runs `scripts/data_quality_report.py` and reports:
- successes (checks passed)
- issues found (data inconsistencies)

---

## API usage (FastAPI)

The API routes are mounted under `/api/v1`.

### Endpoints

#### Full prediction

- **GET** `/api/v1/predict/{race_id}`

Example:

```bash
curl http://localhost:8000/api/v1/predict/canada
```

Optional query parameters:
- `rain_probability` (0.0–1.0)
- `n_simulations`

#### Win probability only

- **GET** `/api/v1/predict/{race_id}/winner`

Example:

```bash
curl http://localhost:8000/api/v1/predict/canada/winner
```

#### DNF risk only

- **GET** `/api/v1/predict/{race_id}/dnf`

Example:

```bash
curl http://localhost:8000/api/v1/predict/canada/dnf
```

#### Standings

- **GET** `/api/v1/standings`

Returns current cached standings snapshots defined in season data.

#### Circuit list

- **GET** `/api/v1/circuits`

Returns all configured circuits with metadata.

#### Custom simulation (advanced)

- **POST** `/api/v1/simulate`

This endpoint allows overriding simulation parameters and caching behavior.

---

## How predictions are computed (high-level)

Even though the exact implementation lives in `engine/` modules, the logical pipeline is:

1. **Validate inputs and select pre-race datasets**
   - circuit definition (track characteristics)
   - driver profiles and pre-race stats
   - season snapshot inputs (standings, form windows)

2. **Feature engineering**
   `engine/feature_engineering.py` computes numeric features such as:
   - driver ELO strength
   - constructor strength baseline
   - recency-form scores
   - circuit type fit (matching driver traits to track type)
   - reliability risk / DNF priors
   - rain/wet adjustment features
   - safety car related parameters
   - teammate comparison delta

3. **Race simulation**
   `engine/probability_model.py` simulates many race realizations using those features.
   The simulation includes random noise (to represent randomness) and structured effects (e.g., safety car impact).

4. **Probability estimation**
   From the outcomes of simulated races, the engine computes:
   - P(win)
   - P(top-3)
   - P(top-10)
   - P(DNF)
   - teammate beat probability

5. **Calibration**
   Calibration adjusts raw simulated frequencies into better-calibrated probabilities.

---

## Anti-leakage rules (important)

A key design principle is preventing the model from using information that would not be available pre-race.

The system should not use:

- any data occurring after `race_start_timestamp`
- post-race steward decisions/penalties
- race-day live weather (only the pre-race forecast / overridden rain probability)
- in-race incident/strategy outcome knowledge

This ensures the probabilities are meaningful for “pre-race preview” usage.

---

## Calibration & evaluation metrics

To evaluate the quality of probability outputs, the project uses metrics such as:

- **Brier score**: squared error of predicted probabilities
- **Log-loss**: penalizes confident wrong predictions
- **Ranked probability score (RPS)**: distribution-wide comparison
- **Calibration curves**: predicted vs observed frequency alignment

Backtesting uses **temporal splits** so the model is evaluated on races “in the future” relative to the data used.

---

## Season maintenance (how to keep data fresh)

The system is only as accurate as its underlying inputs. After each race weekend, you must update the season snapshot so future predictions incorporate:

- new results
- updated driver ELO
- updated recent form
- updated DNF/reliability tendencies
- updated standings totals

### Recommended workflow after a race

1. Add race results into `data/season_2026.py`
2. Update standings snapshots in the same file (driver + constructor)
3. Commit changes so downstream scripts and deployment pipelines can regenerate reports/sites

#### Post-race update shortcut

Use the provided script:

```bash
python scripts/post_race_update.py --round 5 --circuit canada \
  --results "antonelli:1,russell:2,norris:3"
```

This typically handles:
- parsing results
- updating season results
- recomputing derived standings snapshots
- updating ELO and recent form if configured

---

## Adding/updating circuits

Circuit definitions live in `data/circuit_data.py`.

For each upcoming race, add or update:

- `id` / `name`
- location + date
- circuit type tags (used for track fit)
- lap count and distances
- safety car probability
- overtaking difficulty
- rain probability typical
- wall crash probability per lap
- DRS zones / other circuit-specific factors

Example shape (simplified):

```python
"silverstone": {
    "id": "silverstone",
    "name": "Silverstone Circuit",
    "race_date": "2026-07-06",
    "circuit_type": ["balanced"],
    "safety_car_probability": 0.52,
    "rain_probability_typical": 0.45,
    # ...
}
```

---

## Updating driver ELO and recent form

Driver inputs live in `data/driver_data.py`.

### ELO updates
ELO should be recalculated after races based on finishing outcomes vs expectations. The post-race script is designed to handle this automatically if configured.

### Recent form
Recent form is typically stored as a list/window of recent race finish positions. After each race:

- prepend the latest result
- drop the oldest if the window exceeds `RECENCY_WINDOW`

This allows the model to respond to momentum.

---

## Data quality checks

If you update season data manually (or import results), run:

```bash
python scripts/data_quality_report.py
```

or (depending on how your CLI is wired):

```bash
python main.py quality-check
```

Data quality reports catch common issues like:
- missing circuit ids
- drivers present in results but missing from driver roster
- invalid probability bounds
- inconsistent list lengths

---

## Performance and reproducibility

### Monte Carlo simulations

The simulation count (`--sim-count` / `n_simulations`) directly affects:
- stability of the estimated probabilities
- runtime cost

Typical guidance:

- **fast iteration**: 500–5,000 sims
- **better smoothness**: 10,000–25,000 sims

### Deterministic runs

Use `--seed` (or `seed` in the API) to reproduce results exactly.

---

## Deployment (GitHub Pages)

This project is designed to generate a **static** frontend-like site by precomputing predictions and serving them from GitHub Pages.

High-level workflow:

1. GitHub Actions runs on a schedule (e.g., weekly before race weekends) and/or on data changes.
2. The pipeline executes prediction generation.
3. It outputs a folder (commonly `web/`) containing static `index.html` and JSON prediction payloads.
4. GitHub Pages serves that content.

### Manual generation (local preview)

If you have a local `generate_static_site.py` workflow script in your repo setup, it should:
- iterate over all configured circuits
- generate per-circuit JSON
- generate an `index.html`

If your repo includes `scripts/generate_static_site.py`, run:

```bash
python scripts/generate_static_site.py
```

Then preview the output using a local static server.

---

## Backtesting

Backtesting evaluates predictive quality over time.

Example usage (depending on which scripts/CLI options exist):

```bash
python main.py backtest --seasons 2023 2024 2025
```

Backtesting should use only data available before each predicted race.

---

## Tests

Run the unit test suite:

```bash
pytest
```

For verbose output:

```bash
pytest -v
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Circuit ... not found` | circuit id missing in `data/circuit_data.py` | add circuit definition |
| `Driver ... not found` | driver id missing in `data/driver_data.py` | add/update driver roster |
| Probabilities look unstable | too few simulations | increase `--sim-count` |
| API errors on inputs | rain_probability or sim bounds invalid | verify parameter ranges |
| HTML report doesn’t render charts | opening file via `file://` | host with a local server |

---

## Notes for maintainers (what changed often)

Because this is a season-long system, these files are touched frequently:

- `data/season_2026.py` (post-race results + standings snapshot)
- `data/driver_data.py` (ELO, recent form, DNF/reliability priors)
- `data/circuit_data.py` (new circuits + circuit parameter tweaks)
- `config/settings.py` (feature weights, simulation defaults, bounds)

Whenever you update any of the above:
- run `pytest`
- run the data quality report
- regenerate HTML or static site outputs if you publish them

---

## License

Specify your license here (MIT/Apache/etc.) if not already configured in your repo.

