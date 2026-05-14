# Running the F1 Prediction System — Complete Guide

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.12 recommended |
| pip | 23+ | `pip install --upgrade pip` |
| Git | any | For cloning / CI/CD |
| Node.js | optional | Only needed if editing the web frontend |

---

## 1 — Installation

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

## 2 — Running Predictions

### Quickest path — one command

```bash
python scripts/run_canada_gp_2026.py
```
This prints a full Rich-formatted table + saves an HTML report to `./output/`.

---

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

---

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

## 3 — Running Tests

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

## 4 — Generating the Static Site (GitHub Pages)

```bash
# Generates predictions for ALL known circuits and builds web/
python scripts/generate_static_site.py

# Then preview locally
cd web && python -m http.server 8080
# Open http://localhost:8080
```

---

## 5 — Backtesting

```bash
# Run the backtest demo (synthetic data if no historical data present)
python scripts/backtest_2025_season.py

# With historical data in data/historical/2025/
# See data/historical/README.md for the expected file format
python main.py backtest --seasons 2025
```

---

## 6 — Post-Race Updates (After each race weekend)

```bash
# Add this race's results to the system
python scripts/post_race_update.py \
  --round 5 \
  --circuit canada \
  --results "antonelli:1,russell:2,norris:3,piastri:4,verstappen:5"

# Verify the update was applied
python main.py predict --race monaco
```

See `SEASON_MAINTENANCE.md` for the full seasonal update workflow.

---

## 7 — Environment Variables Reference

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

## 8 — Project Layout Quick Reference

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

## 9 — Common Issues

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Make sure venv is activated and `pip install -r requirements.txt` was run |
| `KeyError: 'canada'` | Ensure the circuit is in `data/circuit_data.py` |
| `KeyError: 'antonelli'` | Ensure the driver is in `data/driver_data.py` |
| Slow predictions | Reduce `--sims` to 1000 for quick checks |
| API port already in use | `python main.py api --port 9000` |
| HTML report not opening | Open from a web server, not `file://` (Chart.js CDN needed) |

---

## 10 — Performance Tips

- **Fast mode:** `--sims 500` for instant results (less accurate)
- **Precision mode:** `--sims 25000` for publication-quality probabilities
- **Batch predictions:** Loop over circuits in a shell script
  ```bash
  for race in canada monaco silverstone; do
    python main.py predict --race $race --json-out >> predictions_batch.jsonl
  done
  ```
