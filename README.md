# 🏎️ F1 Predictor 2026 - Advanced Race Prediction Platform

**Professional-grade Formula 1 prediction engine with web-based dashboard, Monte Carlo simulation, and machine learning optimization.**
---

## 🚀 Quick Start (3 Minutes)

### Step 1: Install Dependencies

```bash
cd c:\Users\PC\Music\FORMULA_1_PREDICTOR_2026
py -m pip install -r requirements.txt
```

**Key packages:** Flask, NumPy, Pandas, Plotly, Optuna, SQLAlchemy, Rich

---

### Step 2: Launch Dashboard

```bash
py -3 main.py dashboard --port 5000
```

**Output:**
```
Starting F1 Predictor Dashboard v3.0
Dashboard: http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

---

### Step 3: Initialize System

1. Open browser: **http://127.0.0.1:5000**
2. Click **Settings** tab (top navigation)
3. Scroll to **"Quick Setup"** section
4. Click **"Initialize Everything"** button
5. Wait for success message (~5 seconds)

✅ Database created  
✅ Driver/team/circuit data migrated  
✅ Quality checks passed  

---

### Step 4: Make Your First Prediction

1. Go to **Dashboard** tab
2. Select circuit: "Canadian GP"
3. Choose session: "Sunday Grand Prix"
4. Keep default simulations: 10,000
5. Click **"Run Prediction"**

**Result:** Interactive charts showing predicted podium, win probabilities, DNF risks!

---

## 📖 Table of Contents

- [Quick Start](#-quick-start-3-minutes)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Installation Guide](#-installation-guide)
- [Dashboard User Guide](#-dashboard-user-guide)
  - [Making Predictions](#1-making-predictions)
  - [H2H Comparisons](#2-head-to-head-driver-comparisons)
  - [Constructor Analysis](#3-constructor-team-analysis)
  - [Post-Race Evaluation](#4-post-race-evaluation)
  - [Model Calibration](#5-probability-calibration)
  - [Weight Optimization](#6-model-weight-optimization)
  - [Historical Backtesting](#7-historical-backtesting)
  - [Report Downloads](#8-downloading-reports)
- [Settings & Configuration](#-settings--configuration)
  - [Database Management](#database-management)
  - [Data Sources](#data-sources)
  - [Quality Checks](#quality-checks)
  - [Performance Benchmarking](#performance-benchmarking)
- [How It Works](#-how-it-works)
  - [Prediction Engine](#prediction-engine-overview)
  - [Feature Engineering](#feature-engineering)
  - [ELO Rating System](#elo-rating-system)
  - [Monte Carlo Simulation](#monte-carlo-simulation)
  - [Weather Modeling](#weather-integration)
- [Accuracy Measurement](#-accuracy-measurement)
  - [Brier Score](#brier-score-metric)
  - [Evaluation Workflow](#evaluation-workflow)
  - [Calibration Process](#calibration-process)
- [Advanced Usage](#-advanced-usage)
  - [Custom Grid Overrides](#custom-grid-overrides)
  - [Rain Probability Adjustment](#rain-probability-adjustment)
  - [Simulation Count Tuning](#simulation-count-tuning)
  - [Vectorized vs Original Engine](#vectorized-vs-original-engine)
- [Live Deployment](#-live-deployment) ⭐ NEW
  - [Hugging Face (Free)](#quick-deploy-to-hugging-face-free---30-minutes)
 
---

## ✨ Key Features

### 🧠 Intelligent Prediction Engine

- **Vectorized Monte Carlo Simulation** - NumPy-optimized, 40x faster than loop-based approach
- **Multi-Dimensional ELO Ratings** - Separate ratings for qualifying, race pace, wet weather, tire management
- **8 Predictive Features** - Form streak, reliability index, circuit fit, team performance, historical results
- **Dynamic Weight Optimization** - Optuna Bayesian optimization finds optimal feature weights
- **Platt Scaling Calibration** - Improves probability accuracy post-hoc

### 🌦️ Real-World Modeling

- **Weather Integration** - Rain probability affects overtaking, DNF risk, strategy variance
- **Safety Car Modeling** - Circuit-specific SC probability based on historical data
- **Tire Degradation** - Compound-dependent performance decay over stint length
- **Grid Penalty Simulation** - Automatic grid position adjustments for penalties

### 📊 Interactive Web Dashboard

- **Single-Page Application** - No page reloads, instant navigation
- **Plotly.js Charts** - Interactive visualizations with hover details
- **Real-Time Updates** - Live prediction progress indicators
- **Responsive Design** - Works on desktop, tablet, mobile
- **Export Capabilities** - Download reports as HTML, JSON, CSV

### 📈 Analytics & Validation

- **Post-Race Evaluation** - Compare predictions vs actual results
- **Brier Score Tracking** - Industry-standard probability accuracy metric
- **Historical Backtesting** - Validate against completed seasons (2024-2025)
- **Calibration Tools** - Platt scaling improves probability reliability
- **Accuracy Reports** - Aggregate metrics across all evaluated races

### 💾 Data Persistence

- **SQLite Database** - Store predictions, evaluations, calibration parameters
- **Automatic Migration** - One-click database initialization
- **FastF1 Integration** - Sync historical lap times, telemetry, session data
- **Quality Assurance** - Automated data validation and integrity checks

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  WEB DASHBOARD                       │
│           (Flask + Plotly.js + HTML/CSS)            │
│  http://127.0.0.1:5000                              │
└──────────────────┬──────────────────────────────────┘
                   │ REST API (JSON)
┌──────────────────▼──────────────────────────────────┐
│              FLASK APPLICATION LAYER                 │
│         dashboard/app.py (25+ endpoints)            │
└──┬────────┬──────────┬───────────┬──────────────────┘
   │        │          │           │
┌──▼──┐ ┌──▼────┐ ┌───▼────┐ ┌───▼──────────┐
│Pred │ │Eval   │ │Optimize│ │Backtest      │
│Engine│ │Tracker│ │(Optuna)│ │Framework     │
└──┬──┘ └──┬────┘ └───┬────┘ └───┬──────────┘
   │       │          │           │
   └───────┴──────────┴───────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              DATA & MODELS LAYER                     │
│  • Vectorized Monte Carlo (NumPy)                   │
│  • Multi-dimensional ELO ratings                    │
│  • Feature engineering pipeline                     │
│  • Weather modeling                                 │
│  • SQLite database (SQLAlchemy ORM)                 │
└─────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5, CSS3, JavaScript | Dashboard UI |
| **Visualization** | Plotly.js | Interactive charts |
| **Backend** | Python 3.10+, Flask | Web server, API |
| **Simulation** | NumPy, Pandas | Vectorized Monte Carlo |
| **Optimization** | Optuna | Bayesian weight tuning |
| **Database** | SQLite, SQLAlchemy | Data persistence |
| **Data Sources** | Ergast API, FastF1 | Historical race data |

---

## 📥 Installation Guide

### Prerequisites

- **Python 3.10 or higher** (tested on Python 3.14)
- **pip** (Python package manager)
- **Git** (optional, for cloning repository)
- **Modern web browser** (Chrome, Firefox, Edge recommended)

### Step-by-Step Installation

#### 1. Clone or Download Project

```bash
# Option A: Clone from Git (if available)
git clone https://github.com/yourusername/F1_PREDICTOR_2026.git
cd F1_PREDICTOR_2026

# Option B: Extract ZIP file
# Download and extract to: c:\Users\PC\Music\FORMULA_1_PREDICTOR_2026
```

#### 2. Create Virtual Environment (Recommended)

```bash
# Windows
py -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

**Expected packages installed:**
- flask, flask-cors, flask-limiter (web framework)
- numpy, pandas (data processing)
- plotly (visualization)
- optuna (optimization)
- sqlalchemy (database ORM)
- rich (CLI formatting)
- requests (API calls)
- python-dotenv (environment variables)

#### 4. Verify Installation

```bash
# Check Python version
py --version
# Should show: Python 3.10.x or higher

# Test imports
py -c "import flask, numpy, pandas, plotly; print('All imports successful!')"
```

#### 5. Initialize Database

```bash
# Method 1: Via Dashboard (Recommended)
py -3 main.py dashboard --port 5000
# Then: Settings → Quick Setup → Initialize Everything

# Method 2: Via CLI (deprecated but still works)
py main.py migrate-db
```

#### 6. Launch Dashboard

```bash
py -3 main.py dashboard --port 5000
```

Visit: **http://127.0.0.1:5000**

---

## 🎯 Dashboard User Guide

### Navigation Overview

The dashboard has **6 main sections** accessible via top navigation bar:

1. **Dashboard** - Make predictions, view results
2. **H2H Comparison** - Compare two drivers head-to-head
3. **Constructors** - Team standings and analysis
4. **Analytics** - Model evaluation & tuning (NEW in v3.1)
5. **Settings** - System configuration (NEW in v3.1)
6. **Download Report** - Export predictions

---

### 1. Making Predictions

**Purpose:** Generate probabilistic race outcome predictions using Monte Carlo simulation.

**Steps:**

1. **Select Circuit**
   - Dropdown menu with all 2026 F1 circuits
   - Examples: Australian GP, Monaco GP, Canadian GP, British GP

2. **Choose Session Type**
   - **Friday Practice** - FP1/FP2/FP3 lap time predictions
   - **Saturday Qualifying** - Q1/Q2/Q3 elimination forecasts
   - **Sunday Grand Prix** - Full race outcome prediction (default)

3. **Set Weather Conditions**
   - **Dry** - 0% rain probability (default)
   - **Mixed** - 30% rain probability
   - **Wet** - 70% rain probability
   - Affects: Overtaking difficulty, DNF risk, strategy variance

4. **Configure Simulations**
   - Default: 10,000 simulations
   - Range: 1,000 - 100,000
   - More simulations = more accurate probabilities (diminishing returns after 20k)

5. **Run Prediction**
   - Click **"Run Prediction"** button
   - Loading spinner appears (5-10 seconds for 10k sims)
   - Results display automatically

**Results Display:**

- **Hero Section** - Predicted podium (🥇🥈🥉), safety car %, rain %, confidence
- **Probability Table** - Win %, Top 3 %, Top 10 %, DNF % for each driver
- **Position Distribution Chart** - Bar chart showing P1-P20 probabilities
- **Circuit Information** - Track length, laps, lap record, characteristics

**Example Output:**
```
Predicted Podium: 🥇 Max Verstappen → 🥈 Lewis Hamilton → 🥉 Charles Leclerc

Driver                Win %   Top 3 %   Top 10 %   DNF %
Max Verstappen        28.5%   62.3%     91.2%      8.4%
Lewis Hamilton        18.2%   48.7%     82.5%      12.1%
Charles Leclerc       12.4%   38.9%     75.3%      15.2%
...
```

**Pro Tips:**

- Use 10,000 sims for quick predictions
- Use 50,000+ sims for high-stakes decisions
- Wet conditions increase prediction uncertainty
- Store predictions before race for later evaluation

---

### 2. Head-to-Head Driver Comparisons

**Purpose:** Directly compare two drivers' expected performance at a specific circuit.

**Steps:**

1. **Select Driver 1**
   - Dropdown with all 2026 drivers
   - Example: Max Verstappen

2. **Select Driver 2**
   - Example: Lewis Hamilton

3. **Choose Circuit**
   - Same circuit list as predictions

4. **Click "Compare Drivers"**

**Results Display:**

- **Side-by-Side Metrics** - ELO ratings, form index, reliability
- **Win Probability Split** - Pie chart showing P(D1 wins) vs P(D2 wins)
- **Finishing Position Comparison** - Expected positions with confidence intervals
- **Qualifying Gap** - Predicted qualifying time difference
- **Race Pace Comparison** - Lap time advantage per stint
- **Scenario Analysis** - How results change in dry/wet conditions

**Use Cases:**

- Betting decisions (who's more likely to finish higher?)
- Fantasy F1 lineup choices
- Understanding driver strengths/weaknesses
- Analyzing teammate battles

---

### 3. Constructor Team Analysis

**Purpose:** View team standings, performance trends, and championship projections.

**Features:**

- **Current Standings Table** - Points, wins, podiums for all 10 teams
- **Performance Trend Charts** - Points accumulation over season
- **Team Comparison Tool** - Select 2-3 teams to compare
- **Championship Simulator** - Project final standings with remaining races
- **Reliability Rankings** - DNF rates by constructor
- **Qualifying vs Race Pace** - Team strengths breakdown

**Interactive Elements:**

- Hover over charts for detailed tooltips
- Click team names to filter views
- Toggle between points/wins/podiums metrics
- Adjust remaining race scenarios

---

### 4. Post-Race Evaluation

**Purpose:** Measure prediction accuracy by comparing against actual race results.

**Prerequisites:** You must have stored predictions for the race before it occurred.

**Workflow:**

#### Step 1: Select Circuit
- Choose the race you want to evaluate
- Example: "Canadian GP"

#### Step 2: Generate Template
- Click **"Generate Template"** button
- Textarea auto-fills with JSON:
  ```json
  {
    "verstappen": 0,
    "hamilton": 0,
    "leclerc": 0,
    ...
  }
  ```

#### Step 3: Enter Actual Results
- Replace `0` values with actual finishing positions (1-20)
- Use numbers >20 for DNFs (Did Not Finish)
- Example:
  ```json
  {
    "verstappen": 1,
    "hamilton": 3,
    "leclerc": 2,
    "russell": 4,
    "norris": 5,
    ...
    "stroll": 21
  }
  ```

#### Step 4: Evaluate
- Click **"Evaluate Race"** button
- System calculates:
  - **Brier Score** - Probability accuracy metric (lower is better)
  - **Position Error** - Average deviation from actual positions
  - **Podium Accuracy** - % of predicted podium finishers who actually finished top 3
  - **Winner Prediction** - Did you predict the actual winner?

**Metrics Explained:**

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Brier Score** | Σ(predicted_prob - actual_outcome)² / N | 0 = perfect, 1 = worst |
| **Position Error** | Mean(|predicted_pos - actual_pos|) | Lower = more accurate |
| **Top 3 Accuracy** | Correct predictions / Total predictions | Higher = better |

**Example Output:**
```
Evaluation Complete

Average Brier Score: 0.2946
Predictions Evaluated: 22 drivers
Podium Accuracy: 66.7% (2 out of 3 correct)
Winner Predicted: ✅ Yes (Verstappen)
```

**Best Practices:**

- Evaluate races within 24 hours while data is fresh
- Double-check finishing positions from official F1 results
- Store predictions BEFORE every race you plan to evaluate
- Aim for Brier scores below 0.30 (good accuracy)

---

### 5. Probability Calibration

**Purpose:** Improve prediction accuracy using Platt scaling (logistic regression on probabilities).

**Prerequisites:** At least 10 evaluated races required.

**Theory:**

Raw model probabilities may be overconfident or underconfident. Platt scaling fits a logistic function:

```
P_calibrated = 1 / (1 + exp(-(A × log_odds + B)))
```

Where A and B are learned from historical prediction errors.

**Steps:**

1. **Select Season**
   - Choose which season's data to use for calibration
   - Options: 2024, 2025, 2026

2. **Run Calibration**
   - Click **"Run Calibration"** button
   - Takes 30-60 seconds
   - Fits Platt parameters for 4 outcome types:
     - WIN probability
     - TOP 3 probability
     - TOP 10 probability
     - DNF probability

3. **Review Results**
   - **Before Calibration** - Raw Brier scores
   - **After Calibration** - Calibrated Brier scores
   - **Improvement %** - Reduction in Brier score
   - **Platt Parameters** - A and B values for each outcome type

**Interpretation:**

- **Improvement > 5%** - Significant benefit, use calibrated probabilities
- **Improvement 0-5%** - Minor benefit, optional to use
- **Improvement < 0%** - Model already well-calibrated, skip calibration

**Example Output:**
```
Calibration Complete

Outcome Type: TOP3
  Samples: 220 predictions
  Platt A: 1.2345, B: -0.1234
  Brier Before: 0.1456
  Brier After:  0.1289
  Improvement:  11.5%

Average Calibration Improvement: 8.7%
Outcome types calibrated: 3/4
[PASS] Calibration provides significant improvement
```

**When to Re-Calibrate:**

- After every 10 new evaluated races
- When changing model features/weights
- At start of new season
- If Brier scores degrade over time

---

### 6. Model Weight Optimization

**Purpose:** Use Bayesian optimization (Optuna) to find optimal feature weights that minimize prediction error.

**Theory:**

The prediction engine uses 8 features with weights:
```
score = w1×elo_quali + w2×elo_race + w3×form + w4×reliability + 
        w5×circuit_fit + w6×team_perf + w7×wet_skill + w8×tire_mgmt
```

Optuna searches for weights that minimize Brier score on historical data.

**Steps:**

1. **Set Trial Count**
   - Slider range: 50 - 500 trials
   - Default: 100 trials
   - More trials = better optimization (but slower)
   - Each trial tests a different weight combination

2. **Start Optimization**
   - Click **"Start Optimization"** button
   - Takes 5-10 minutes (depending on trials)
   - Progress shown in real-time

3. **Review Results**
   - **Optimized Weights** - Best weight set found
   - **Brier Improvement** - Reduction vs default weights
   - **Trial History** - Performance of each trial
   - **Recommendation** - Whether to adopt new weights

**Example Output:**
```
Optimization Complete

Trials Completed: 100
Best Brier Score: 0.2834 (improvement: 6.2%)

Optimized Weights:
  elo_quali:    0.28 (was 0.25)
  elo_race:     0.32 (was 0.30)
  form:         0.15 (was 0.15)
  reliability:  0.10 (was 0.10)
  circuit_fit:  0.08 (was 0.10)
  team_perf:    0.04 (was 0.05)
  wet_skill:    0.02 (was 0.03)
  tire_mgmt:    0.01 (was 0.02)

[RECOMMENDATION] Adopt optimized weights for improved accuracy
```

**Best Practices:**

- Run optimization quarterly, not after every race
- Use at least 100 trials for reliable results
- Validate optimized weights on holdout data
- Don't over-optimize (risk of overfitting)
- Track weight changes over time

---

### 7. Historical Backtesting

**Purpose:** Validate model performance against completed seasons to assess reliability.

**Methodology:**

Temporal cross-validation:
1. Train on races 1-N
2. Predict race N+1
3. Evaluate against actual result
4. Repeat for all races in season

This simulates real-world usage where you only have past data.

**Steps:**

1. **Select Seasons**
   - Checkboxes: 2024, 2025, 2026 (partial)
   - Can test multiple seasons simultaneously

2. **Set Simulations**
   - Sims per race: 1,000 - 50,000
   - Default: 10,000
   - Higher = more accurate but slower

3. **Run Backtest**
   - Click **"Run Backtest"** button
   - Takes 5-30 minutes (depends on seasons/sims)
   - Progress indicator shows current race

4. **Analyze Results**
   - **Per-Race Metrics** - Brier score, position error for each race
   - **Season Aggregates** - Average accuracy across season
   - **Trend Analysis** - Does accuracy improve over season?
   - **Circuit Breakdown** - Which tracks are hardest to predict?

**Example Output:**
```
Backtest Complete

Season: 2025
Races Tested: 22
Average Brier Score: 0.3124
Average Position Error: ±2.3 positions
Podium Accuracy: 58.3%

Best Predicted Race: Monaco GP (Brier: 0.2145)
Worst Predicted Race: Spa-Francorchamps (Brier: 0.4289)

Trend: Accuracy improved 12% from early to late season
```

**Use Cases:**

- Validate model before new season
- Identify weaknesses (specific circuits, conditions)
- Compare different model configurations
- Build confidence in predictions
- Academic/research purposes

---

### 8. Downloading Reports

**Purpose:** Export predictions for offline analysis, sharing, or archival.

**Formats Available:**

#### HTML Report (Recommended)
- **Content:** Full interactive report with charts, tables, analysis
- **Use Case:** Share with colleagues, embed in presentations
- **File Size:** ~500 KB
- **Open:** Any web browser

#### JSON Data
- **Content:** Raw prediction data, all probabilities, metadata
- **Use Case:** Programmatic analysis, custom visualizations
- **File Size:** ~50 KB
- **Open:** Text editor, Python, R, etc.

#### CSV Export
- **Content:** Driver results table (position, probabilities)
- **Use Case:** Excel analysis, spreadsheet modeling
- **File Size:** ~10 KB
- **Open:** Excel, Google Sheets, LibreOffice

**Steps:**

1. **Select Circuit**
   - Choose which race report to download

2. **Choose Format**
   - Click HTML / JSON / CSV option card

3. **Download**
   - Click **"Generate & Download Report"** button
   - File saves to Downloads folder

**HTML Report Contents:**

- Executive summary
- Predicted podium with photos
- Probability distribution charts
- Driver-by-driver analysis
- Circuit information
- Weather impact assessment
- Confidence intervals
- Historical comparison

---

## ⚙️ Settings & Configuration

### Database Management

**Purpose:** Initialize, backup, or reset the SQLite database.

**Actions:**

#### Initialize Database
- Creates all tables (predictions, evaluations, drivers, teams, circuits)
- Migrates static data from JSON files
- Takes ~5 seconds
- **When:** First-time setup only

#### Backup Database
- Exports database to SQL file
- Preserves all predictions and evaluations
- **When:** Before major updates

#### Reset Database
- Deletes all data and recreates tables
- **Warning:** Irreversible! Loses all stored predictions
- **When:** Starting fresh, debugging

**Access:** Settings tab → Database Management section

---

### Data Sources

**Purpose:** Sync historical race data from external APIs.

#### FastF1 Integration

FastF1 is a Python library providing access to official F1 timing data.

**What It Provides:**
- Lap times (sector splits, tire compounds)
- Telemetry (speed, throttle, brake, DRS)
- Session results (qualifying, race classifications)
- Weather data (track temp, air temp, humidity)

**Sync Process:**

1. **Select Seasons**
   - Checkboxes: 2024, 2025
   - Each season takes 2-5 minutes to sync

2. **Click "Sync Data"**
   - Downloads data from FastF1 cache/API
   - Stores in local SQLite database
   - Progress indicator shows status

3. **Verify Sync**
   - Check "Last Sync" timestamp
   - Review record counts

**Use Cases:**
- Backtesting with real lap times
- Driver performance analysis
- Tire degradation modeling
- Weather correlation studies

**Note:** FastF1 requires internet connection. Data cached locally after first sync.

---

### Quality Checks

**Purpose:** Validate data integrity and identify issues.

**Checks Performed:**

1. **Driver Data**
   - All drivers have valid IDs
   - No duplicate entries
   - Required fields present (name, team, number)

2. **Team Data**
   - All constructors listed
   - Valid color codes
   - Correct driver assignments

3. **Circuit Data**
   - All 2026 circuits present
   - Valid coordinates
   - Lap records populated

4. **Prediction Data**
   - Probabilities sum to ~100%
   - No NaN/null values
   - Reasonable ranges (0-100%)

5. **Evaluation Data**
   - Actual positions are valid (1-20)
   - Matches stored predictions
   - Brier scores calculated correctly

**Running Checks:**

1. Go to Settings tab → Quality Checks
2. Click **"Run Quality Check"**
3. Review results (takes ~10 seconds)

**Interpreting Results:**

- ✅ **Passed** - All checks green, data is clean
- ⚠️ **Warnings** - Minor issues (missing optional fields)
- ❌ **Errors** - Critical problems (invalid data, corruption)

**Fixing Issues:**

- Warnings: Usually safe to ignore
- Errors: Re-sync data, re-run migration, or contact support

---

### Performance Benchmarking

**Purpose:** Test simulation speed and compare engine versions.

**What It Measures:**

- **Vectorized Engine Time** - NumPy-optimized simulation speed
- **Original Engine Time** - Loop-based baseline (for comparison)
- **Speedup Factor** - How much faster vectorized is
- **Probability Difference** - Accuracy comparison (should be near-zero)

**Running Benchmark:**

1. **Select Test Circuit**
   - Options: Canada, Monaco, Spain, Britain
   - Different complexities test different aspects

2. **Set Simulations**
   - Default: 5,000
   - Range: 1,000 - 50,000

3. **Click "Run Benchmark"**
   - Takes 10-30 seconds
   - Runs both engines for comparison

**Example Results:**
```
Benchmark Results

Vectorized Time: 245.67 ms
Original Time:   9823.45 ms
Speedup Factor:  40.02x
Max Probability Diff: 0.0012

[EXCELLENT] Vectorized engine is 40x faster with negligible accuracy loss
```

**Interpretation:**

- **Speedup > 20x** - Excellent optimization
- **Speedup 10-20x** - Good optimization
- **Speedup < 10x** - Room for improvement
- **Prob Diff < 0.01** - Accuracy preserved
- **Prob Diff > 0.01** - Investigate numerical differences

**When to Benchmark:**

- After code changes
- When upgrading hardware
- Curiosity about performance
- Troubleshooting slow predictions

---

## 🧠 How It Works

### Prediction Engine Overview

The F1 Predictor uses a **multi-stage pipeline**:

```
Input Data → Feature Engineering → Scoring → Monte Carlo Simulation → Output
```

#### Stage 1: Input Data

**Sources:**
- Driver ELO ratings (qualifying, race, wet)
- Team performance metrics
- Circuit characteristics
- Weather forecasts
- Historical results

**Format:** Structured data in SQLite database

---

#### Stage 2: Feature Engineering

**8 Predictive Features:**

1. **Qualifying ELO** (weight: 0.25)
   - Measures single-lap pace
   - Updated after each qualifying session
   - Circuit-specific adjustments

2. **Race Pace ELO** (weight: 0.30)
   - Measures long-run speed
   - Accounts for tire management
   - Fuel load corrections

3. **Form Index** (weight: 0.15)
   - Recent performance trend (last 5 races)
   - Exponential decay weighting
   - Momentum factor

4. **Reliability Score** (weight: 0.10)
   - Historical DNF rate
   - Mechanical failure frequency
   - Team infrastructure quality

5. **Circuit Fit** (weight: 0.10)
   - Driver's historical performance at track
   - Driving style compatibility
   - Track characteristic match

6. **Team Performance** (weight: 0.05)
   - Constructor championship position
   - Car development trajectory
   - Pit stop efficiency

7. **Wet Weather Skill** (weight: 0.03)
   - Performance in rainy conditions
   - Car control in low grip
   - Strategic decision-making

8. **Tire Management** (weight: 0.02)
   - Degradation rate vs competitors
   - Compound selection effectiveness
   - Stint length optimization

**Normalization:**

All features scaled to 0-1 range using min-max normalization:
```
feature_normalized = (feature - min) / (max - min)
```

---

#### Stage 3: Driver Scoring

**Composite Score Calculation:**

```
driver_score = Σ(weight_i × feature_i) for i in 1..8
```

**Example:**
```
Max Verstappen:
  = 0.25×0.95 + 0.30×0.98 + 0.15×0.92 + 0.10×0.88 + 
    0.10×0.90 + 0.05×0.96 + 0.03×0.85 + 0.02×0.91
  = 0.942

Lewis Hamilton:
  = 0.25×0.88 + 0.30×0.85 + 0.15×0.78 + 0.10×0.92 + 
    0.10×0.75 + 0.05×0.82 + 0.03×0.95 + 0.02×0.88
  = 0.851
```

**Score Interpretation:**
- 0.90+ - Elite performer (championship contender)
- 0.80-0.90 - Strong driver (podium threat)
- 0.70-0.80 - Midfield competitor (points scorer)
- <0.70 - Backmarker (struggling)

---

#### Stage 4: Monte Carlo Simulation

**Algorithm:**

For each simulation (10,000 iterations):

1. **Sample Driver Performance**
   - Draw from normal distribution centered on driver_score
   - Standard deviation reflects uncertainty (higher in wet conditions)

2. **Apply Random Events**
   - Safety car probability (circuit-specific)
   - DNF risk (reliability-based)
   - Weather changes (if mixed conditions)

3. **Simulate Race Progression**
   - Lap-by-lap position updates
   - Overtaking attempts (based on score differences)
   - Pit stop strategies (tire degradation model)

4. **Record Finishing Order**
   - Store final classification
   - Track position changes

**Vectorization:**

Instead of looping 10,000 times, we use NumPy arrays:
```python
# Original (slow): Loop-based
for sim in range(10000):
    result = simulate_race()
    store_result(result)

# Vectorized (fast): Array operations
all_results = np.random.normal(driver_scores, uncertainty, size=(10000, 20))
final_positions = np.argsort(-all_results, axis=1)
```

**Speed Comparison:**
- Loop-based: 10 seconds for 10k sims
- Vectorized: 0.25 seconds for 10k sims
- **Speedup: 40x faster**

---

#### Stage 5: Probability Calculation

**Aggregation:**

After all simulations complete:

```
P(driver wins) = (number of wins) / (total simulations)
P(driver top 3) = (number of top 3 finishes) / (total simulations)
P(driver DNF) = (number of DNFs) / (total simulations)
```

**Confidence Intervals:**

Using binomial proportion confidence interval:
```
CI = p ± z × sqrt(p(1-p)/n)

where:
  p = observed probability
  z = 1.96 (95% confidence)
  n = number of simulations
```

**Example:**
```
Max Verstappen win probability: 28.5% ± 1.4% (95% CI)
Based on 2,850 wins out of 10,000 simulations
```

---

### ELO Rating System

**Concept:**

ELO ratings measure relative skill levels. Originally designed for chess, adapted for F1 with multiple dimensions.

**Rating Update Formula:**

```
R_new = R_old + K × (S_actual - S_expected)

where:
  R_old = current rating
  K = update factor (varies by session importance)
  S_actual = actual result (1 for win, 0.5 for draw, 0 for loss)
  S_expected = expected result based on rating difference
```

**Expected Result Calculation:**

```
S_expected = 1 / (1 + 10^((R_opponent - R_driver) / 400))
```

**Multiple Dimensions:**

We maintain separate ELO ratings for:

1. **Qualifying ELO**
   - Updated after each qualifying session
   - K = 20 (moderate updates)
   - Reflects single-lap pace

2. **Race Pace ELO**
   - Updated after each race
   - K = 15 (conservative updates)
   - Reflects long-run speed

3. **Wet Weather ELO**
   - Updated only in rainy races
   - K = 25 (aggressive updates, less data)
   - Reflects car control in low grip

**Initialization:**

New drivers start at baseline:
- Qualifying ELO: 1500
- Race Pace ELO: 1500
- Wet Weather ELO: 1500

**Rating Interpretation:**

- 1600+ - Elite driver (Verstappen, Hamilton level)
- 1500-1600 - Strong driver (Leclerc, Norris level)
- 1400-1500 - Solid midfield (Albon, Hulkenberg level)
- <1400 - Developing driver (rookies, backmarkers)

---

### Weather Integration

**Impact Modeling:**

Rain affects predictions through multiple mechanisms:

1. **Overtaking Difficulty**
   - Wet conditions reduce grip differential
   - Makes passing harder (or easier, depending on driver skill)
   - Modeled as increased position volatility

2. **DNF Risk Increase**
   - Higher crash probability in wet
   - Mechanical stress from aquaplaning
   - DNF probability multiplied by 1.5-2.0x

3. **Strategy Variance**
   - Tire compound choices matter more
   - Timing of pit stops critical
   - Increases outcome uncertainty

4. **Skill Amplification**
   - Wet weather specialists gain advantage
   - "Wet Weather ELO" feature weighted more heavily
   - Experienced drivers outperform rookies

**Rain Probability Levels:**

| Level | Probability | Impact |
|-------|------------|--------|
| **Dry** | 0% | Baseline predictions |
| **Mixed** | 30% | Moderate uncertainty increase |
| **Wet** | 70% | High volatility, DNF risk doubled |

**User Control:**

Users can manually override rain probability:
- Based on weather forecasts
- Historical circuit rain patterns
- Personal judgment

---

## 📊 Accuracy Measurement

### Brier Score Metric

**Definition:**

The Brier score measures the accuracy of probabilistic predictions. It's the mean squared error between predicted probabilities and actual outcomes.

**Formula:**

```
Brier Score = (1/N) × Σ(p_i - o_i)²

where:
  N = number of predictions
  p_i = predicted probability
  o_i = actual outcome (1 if event occurred, 0 otherwise)
```

**Example Calculation:**

Predicting Top 3 finish for 3 drivers:

```
Driver A: Predicted P(Top 3) = 0.70, Actually finished P2 → o = 1
  Contribution: (0.70 - 1)² = 0.09

Driver B: Predicted P(Top 3) = 0.50, Actually finished P5 → o = 0
  Contribution: (0.50 - 0)² = 0.25

Driver C: Predicted P(Top 3) = 0.80, Actually finished P3 → o = 1
  Contribution: (0.80 - 1)² = 0.04

Brier Score = (0.09 + 0.25 + 0.04) / 3 = 0.127
```

**Interpretation:**

| Brier Score | Quality | Description |
|-------------|---------|-------------|
| 0.00 - 0.10 | Excellent | Near-perfect predictions |
| 0.10 - 0.20 | Very Good | Highly accurate |
| 0.20 - 0.30 | Good | Solid predictive power |
| 0.30 - 0.40 | Fair | Useful but imperfect |
| 0.40 - 0.50 | Poor | Limited accuracy |
| >0.50 | Bad | Worse than random guessing |

**Why Brier Score?**

- Proper scoring rule (encourages honest probabilities)
- Decomposable into reliability, resolution, uncertainty
- Comparable across different prediction tasks
- Industry standard in weather forecasting, finance

---

### Evaluation Workflow

**Complete Process:**

```
1. Store Prediction (before race)
   ↓
2. Race Occurs
   ↓
3. Input Actual Results
   ↓
4. Calculate Brier Score
   ↓
5. Store Evaluation
   ↓
6. Aggregate Across Races
   ↓
7. Calibrate (if 10+ evaluations)
```

**Step-by-Step:**

#### 1. Store Prediction

Before the race starts:
```bash
# Via Dashboard
Dashboard → Make Prediction → Check "Store in Database"

# Via CLI (deprecated)
py main.py predict --race canada --store
```

**Stored Data:**
- Driver probabilities (win, top 3, top 10, DNF)
- Predicted finishing order
- Timestamp
- Weather conditions
- Simulation count

#### 2. Race Occurs

Wait for actual race to complete.

#### 3. Input Actual Results

Via Dashboard:
- Analytics → Post-Race Evaluation
- Select circuit
- Generate template
- Fill in actual positions
- Submit

#### 4. Calculate Brier Score

System automatically computes:
- Per-driver Brier scores
- Average Brier score for race
- Position errors
- Podium accuracy

#### 5. Store Evaluation

Saved to database:
- Brier scores
- Actual vs predicted positions
- Timestamp
- Circuit ID

#### 6. Aggregate Across Races

After multiple evaluations:
- Average Brier score across all races
- Trend analysis (improving/declining)
- Circuit-specific performance
- Condition-specific performance (dry vs wet)

#### 7. Calibrate (if 10+ evaluations)

Once you have 10+ evaluated races:
- Run calibration (Analytics → Calibration)
- Apply Platt scaling
- Save calibrated parameters
- Use for future predictions

---

### Calibration Process

**Goal:** Transform raw probabilities into better-calibrated probabilities.

**Problem:**

ML models often produce overconfident or underconfident probabilities:
- Overconfident: Predicts 80% but event occurs 60% of time
- Underconfident: Predicts 40% but event occurs 60% of time

**Solution: Platt Scaling**

Logistic regression on log-odds:

```
log_odds_raw = log(p / (1 - p))
log_odds_calibrated = A × log_odds_raw + B
p_calibrated = 1 / (1 + exp(-log_odds_calibrated))
```

**Learning A and B:**

Fit logistic regression on historical data:
- Input: Raw predicted probabilities
- Output: Actual outcomes (0 or 1)
- Optimize: Minimize negative log-likelihood

**Implementation:**

```python
from sklearn.linear_model import LogisticRegression

# Prepare data
X = np.array([log(p/(1-p)) for p in raw_probs]).reshape(-1, 1)
y = np.array(outcomes)  # 0 or 1

# Fit model
model = LogisticRegression()
model.fit(X, y)

# Extract parameters
A = model.coef_[0][0]
B = model.intercept_[0]
```

**When to Calibrate:**

- After 10+ evaluated races (minimum sample size)
- When Brier scores plateau
- Before important predictions (championship deciders)
- Quarterly maintenance

**Effectiveness:**

Typical improvements:
- Brier score reduction: 5-15%
- Reliability improvement: Better probability-frequency alignment
- Decision quality: More trustworthy probabilities

---

## 🚀 Advanced Usage

### Custom Grid Overrides

**Purpose:** Manually set starting grid positions (e.g., after penalties).

**Usage:**

```bash
# Via CLI (deprecated)
py main.py predict --race monaco --grid-override "verstappen:5,hamilton:1"

# Via Dashboard
Not currently supported (future feature)
```

**Format:**

```
driver_id:position,driver_id:position
```

**Example:**

Verstappen gets 5-place grid penalty:
```
--grid-override "verstappen:6,russell:1,hamilton:2,..."
```

**Validation:**

- Driver IDs must be valid
- Positions must be 1-20
- No duplicate positions
- All drivers must be assigned

---

### Rain Probability Adjustment

**Purpose:** Override default rain probability based on forecasts.

**Usage:**

```bash
# Via CLI (deprecated)
py main.py predict --race spain --rain 0.45

# Via Dashboard
Dashboard → Weather dropdown → Select Mixed/Wet
```

**Values:**

- 0.0 = Completely dry
- 0.3 = Mixed conditions (default for "Mixed")
- 0.7 = Heavy rain (default for "Wet")
- 1.0 = Monsoon (extreme, rarely used)

**When to Adjust:**

- Weather forecast predicts rain
- Historical circuit rain patterns
- Practice sessions showed wet track
- Personal judgment

**Impact:**

Higher rain probability:
- Increases DNF risk
- Reduces overtaking ease
- Amplifies wet weather skill importance
- Widens confidence intervals

---

### Simulation Count Tuning

**Purpose:** Balance accuracy vs speed.

**Guidelines:**

| Simulations | Time | Accuracy | Use Case |
|-------------|------|----------|----------|
| 1,000 | 0.02s | ±3.2% | Quick checks |
| 10,000 | 0.25s | ±1.0% | Default, good balance |
| 50,000 | 1.2s | ±0.4% | Important predictions |
| 100,000 | 2.5s | ±0.3% | Maximum accuracy |

**Diminishing Returns:**

Accuracy improves as √n:
- 1k → 10k: 3x accuracy improvement
- 10k → 100k: 3x accuracy improvement
- But time increases linearly!

**Recommendation:**

- Daily predictions: 10,000 sims
- Championship-deciding races: 50,000 sims
- Research/analysis: 100,000 sims

---

### Vectorized vs Original Engine

**Comparison:**

| Aspect | Vectorized | Original |
|--------|-----------|----------|
| **Speed** | 0.25s (10k sims) | 10s (10k sims) |
| **Memory** | Higher (arrays) | Lower (scalars) |
| **Accuracy** | Identical (±0.001) | Identical |
| **Code Complexity** | Higher (NumPy) | Lower (loops) |
| **Maintainability** | Moderate | Easy |

**When to Use Each:**

- **Vectorized:** Production use, real-time predictions
- **Original:** Debugging, educational purposes, verification

**Switching Engines:**

Currently hardcoded to vectorized. To use original:
```python
# In engine/predictor.py
USE_VECTORIZED = False  # Change to True/False
```

---

## 🚀 Live Deployment

**Want to share your F1 Predictor dashboard with the world? Deploy it to the cloud!**

### Quick Deploy to Hugging Face (Free - 30 Minutes)

**Step 1: Run Deployment Helper**
```bash
deploy_to_huggingface.bat
```

This script will:
- ✅ Check all required files
- ✅ Initialize Git repository
- ✅ Optionally test with Docker locally
- ✅ Guide you through Hugging Face setup

**Step 2: Create Hugging Face Space**
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Name: `f1-predictor-2026`
3. SDK: **Docker**
4. Click "Create Space"

**Step 3: Push Code**
```bash
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/f1-predictor-2026
git push -u origin main
```

**Step 4: Wait & Access**
- Build time: 5-10 minutes
- Your URL: `https://YOUR_USERNAME-f1-predictor-2026.hf.space`


## 📁 Project Structure

```
FORMULA_1_PREDICTOR_2026/
│
├── main.py                      # CLI entry point (deprecated)
├── requirements.txt             # Python dependencies
├── README.md                    # This file (documentation)
│
├── dashboard/                   # Web dashboard
│   ├── app.py                   # Flask application (25+ API routes)
│   ├── templates/
│   │   └── dashboard.html       # Single-page app (5000+ lines)
│   └── static/
│       ├── analytics.js         # Analytics module (500+ lines)
│       ├── f1_image0.png        # Hero image
│       └── ...                  # Other assets
│
├── engine/                      # Core prediction logic
│   ├── predictor.py             # Main prediction engine
│   ├── vectorized_simulation.py # NumPy-optimized simulator
│   ├── elo_system.py            # Multi-dimensional ELO ratings
│   ├── features.py              # Feature engineering
│   ├── calibration.py           # Platt scaling implementation
│   └── prediction_tracker.py    # Accuracy tracking
│
├── data/                        # Data layer
│   ├── driver_data.py           # Driver profiles, ELO ratings
│   ├── team_data.py             # Constructor information
│   ├── circuit_data.py          # Track characteristics
│   ├── race_mapping.py          # Circuit name mappings
│   └── fastf1_integration.py    # FastF1 data sync
│
├── database/                    # Database layer
│   ├── models.py                # SQLAlchemy ORM models
│   └── migrations.py            # Database migration scripts
│
├── scripts/                     # Utility scripts
│   ├── optimize_weights_v3.py   # Optuna weight optimization
│   ├── backtest_2025_season.py  # Historical backtesting
│   ├── calibrate_probabilities.py # Platt scaling calibration
│   ├── generate_results_template.py # Template generator
│   └── data_quality_report.py   # Quality validation
│
└── examples/                    # Example outputs
    └── README.md                # Example documentation
```

**Key Files:**

| File | Purpose | Lines |
|------|---------|-------|
| `dashboard/app.py` | Flask server, API endpoints | 1,500+ |
| `dashboard/templates/dashboard.html` | Web UI | 5,000+ |
| `dashboard/static/analytics.js` | Frontend logic | 500+ |
| `engine/vectorized_simulation.py` | Monte Carlo engine | 400+ |
| `engine/elo_system.py` | Rating system | 300+ |
| `scripts/optimize_weights_v3.py` | Optimization | 250+ |

**Total Codebase:** ~10,000 lines of Python + HTML/CSS/JS

---

## 💾 Database Schema

### Tables Overview

```sql
-- Drivers table
CREATE TABLE drivers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team TEXT,
    number INTEGER,
    elo_qualifying REAL DEFAULT 1500,
    elo_race REAL DEFAULT 1500,
    elo_wet REAL DEFAULT 1500
);

-- Teams table
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT,
    principal TEXT
);

-- Circuits table
CREATE TABLE circuits (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    length_km REAL,
    laps INTEGER,
    lap_record TEXT
);

-- Predictions table
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    circuit_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_type TEXT DEFAULT 'RACE',
    simulations INTEGER DEFAULT 10000,
    weather TEXT DEFAULT 'DRY',
    driver_probabilities TEXT,  -- JSON blob
    predicted_order TEXT,       -- JSON array
    FOREIGN KEY (circuit_id) REFERENCES circuits(id)
);

-- Evaluations table
CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    actual_results TEXT,        -- JSON blob
    brier_score REAL,
    position_error REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

-- Calibration parameters table
CREATE TABLE calibration_params (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    outcome_type TEXT NOT NULL,  -- 'win', 'top3', 'top10', 'dnf'
    platt_a REAL,
    platt_b REAL,
    brier_before REAL,
    brier_after REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Data Types:**

- **TEXT** - Strings (IDs, names, JSON blobs)
- **INTEGER** - Whole numbers (positions, counts)
- **REAL** - Floating point (probabilities, ELO ratings)
- **DATETIME** - Timestamps (auto-generated)

**Relationships:**

- `predictions.circuit_id` → `circuits.id` (many-to-one)
- `evaluations.prediction_id` → `predictions.id` (one-to-one)

**Indexes:**

```sql
CREATE INDEX idx_predictions_circuit ON predictions(circuit_id);
CREATE INDEX idx_evaluations_prediction ON evaluations(prediction_id);
CREATE INDEX idx_calibration_season ON calibration_params(season);
```
---


### Getting Help

If issues persist:

1. **Check Documentation** - Search this README for keywords
2. **Review Error Messages** - Often self-explanatory
3. **Test Components Individually** - Isolate the problem
4. **Check Logs** - Look for error messages in terminal
5. **GitHub Issues** - Search for similar problems
6. **Contact Support** - Provide error messages, steps to reproduce

---

## 📈 Performance Benchmarks

### Simulation Speed

| Simulations | Vectorized Time | Original Time | Speedup |
|-------------|----------------|---------------|---------|
| 1,000 | 0.02s | 1.0s | 50x |
| 10,000 | 0.25s | 10.0s | 40x |
| 50,000 | 1.2s | 50.0s | 42x |
| 100,000 | 2.5s | 100.0s | 40x |

**Hardware:** Intel i7-10700K, 32GB RAM, Windows 11

**Notes:**
- Linear scaling with simulation count
- Vectorized uses ~2x more memory
- Accuracy identical (±0.001 probability difference)

---

### Dashboard Responsiveness

| Operation | Time | Notes |
|-----------|------|-------|
| Page Load | <1s | Cached assets |
| Prediction (10k sims) | 5-10s | Includes rendering |
| H2H Comparison | 2-3s | Two predictions |
| Template Generation | <1s | JSON creation |
| Race Evaluation | 1-2s | Brier calculation |
| Calibration (10 races) | 30-60s | Platt fitting |
| Optimization (100 trials) | 5-10 min | Bayesian search |
| Backtest (1 season) | 10-30 min | 22 races |

---

<p align="center">
  <strong>Made with ❤️ for F1 fans worldwide</strong><br>
  <em>Last updated: July 6, 2026</em>
</p>

---

## 🏁 Recent Updates - Completed Race Results Feature (July 2026)

### Overview

The F1 Predictor now includes **automatic detection and display of actual race results** for completed races. When users select a race that has already occurred, the system prevents predictions and instead shows official historical results from multiple data sources.

### Key Features Added

#### 1. **Automatic Race Completion Detection**
- System compares race dates with current date to detect completed races
- Blocks Monte Carlo predictions on past races
- Provides clear visual feedback via status banners and button states

#### 2. **Dual Data Source Architecture**
- **Primary**: FastF1 library (detailed timing, telemetry, all sessions)
- **Fallback**: Jolpica API (free, no API key, Race/Qualifying/Sprint results)
- Automatic fallback ensures results always available even without FastF1 installed

#### 3. **Smart UI Behavior**
- Green "Race Complete" button replaces blue "Run Prediction" for completed races
- Click green button to cycle through: Race → Qualifying → Sprint → Practice results
- Automatic session selection based on day (Friday=Practice, Saturday=Qualifying, Sunday+=Race)
- Professional result tables with position badges, times, points, and status indicators

#### 4. **Session-Aware Display**
- Shows most relevant results first based on weekend phase
- Hides prediction panels when showing actual results
- Maintains full historical context across all session types

### Technical Implementation

**Backend:**
- New `_check_race_completed()` function in [`engine/predictor.py`](engine/predictor.py#L158-L304)
- New `/api/check-race-status/<circuit_id>` endpoint in [`dashboard/app.py`](dashboard/app.py)
- Jolpica integration in [`data/jolpica_client.py`](data/jolpica_client.py) for fallback data

**Frontend:**
- Race status checking on page load and race selection change
- Dynamic button state management (green vs blue)
- Session cycling mechanism with click handler
- Results rendering functions for Race, Qualifying, and Practice data

### User Experience

**Completed Race Flow:**
1. Select completed race (e.g., British GP - July 5, 2026)
2. Green button appears: "Race Complete - View Results"
3. Official results display automatically
4. Click button to cycle through different session results
5. Cannot run predictions (prevents confusion)

**Upcoming Race Flow:**
1. Select future race (e.g., Monaco GP - June 7, 2026)
2. Blue button remains: "Run Prediction"
3. Normal Monte Carlo simulation workflow
4. Predictions displayed with probabilities

### Benefits

✅ Prevents user confusion about which races can be predicted  
✅ Provides official historical results without leaving the app  
✅ Enables post-race evaluation and accuracy tracking  
✅ Robust dual-source architecture ensures reliability  
✅ Clear visual distinction between predictions and actual outcomes  

### Testing

```bash
# Start dashboard
py -3 main.py dashboard --port 5000

# Test with completed race
# Select "Australian Grand Prix" or "British Grand Prix"
# Observe green button and automatic results display
# Click green button to cycle through sessions
```

**Note**: For full practice session data (FP1/FP2/FP3), install FastF1:
```bash
pip install fastf1
```

Without FastF1, the system uses Jolpica API and shows Race, Qualifying, and Sprint results.

---

**This feature transforms the F1 Predictor from just a prediction tool into a comprehensive F1 data platform serving users throughout the entire race weekend lifecycle.** 🏎️🏁