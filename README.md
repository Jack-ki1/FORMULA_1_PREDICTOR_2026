# 🏁 F1 Predictor 2026 v3.0
### A Probabilistic Formula One Race Outcome Prediction System

> **Built for:** Data scientists, F1 fans, developers, students, and anyone curious about how probability, machine learning, and data science can predict the unpredictable world of Formula 1 racing.

> **Version 3.0 Highlights:** SQLite database integration, Fast-F1 data sync, interactive web dashboard, vectorized Monte Carlo simulations (40x faster), Optuna weight optimization, H2H driver comparison, constructor predictions, championship simulator, and real-time weather API integration.

---

## 📖 Table of Contents

1. [What Is This Project?](#-what-is-this-project)
2. [Who Is This For?](#-who-is-this-for)
3. [What's New in v3.0?](#-whats-new-in-v30)
4. [How Does It Work? (Plain English)](#-how-does-it-work-plain-english)
5. [Understanding Probabilities vs. Certainties](#-understanding-probabilities-vs-certainties)
6. [Quick Start Guide](#-quick-start-guide)
7. [Installation (Step by Step)](#-installation-step-by-step)
8. [How to Use It](#-how-to-use-it)
9. [Available Circuits (2026 Season)](#-available-circuits-2026-season)
10. [Project Structure Explained](#-project-structure-explained)
11. [Database & Data Management](#-database--data-management)
12. [Model Accuracy & Calibration](#-model-accuracy--calibration)
13. [Performance Optimization](#-performance-optimization)
14. [Troubleshooting](#-troubleshooting)
15. [2026 Season Context](#-2026-season-context)
16. [Technology Stack](#-technology-stack)
17. [Glossary for Beginners](#-glossary-for-beginners)
18. [Contributing](#-contributing)
19. [License](#-license)

---

## 📖 What Is This Project?

**F1 Predictor 2026** is a sophisticated prediction system that forecasts Formula One race outcomes **before the race starts**. Unlike traditional prediction methods that simply guess "who will win," this system provides **probabilistic predictions** — honest, data-driven estimates of what might happen.

### The Problem with Traditional Predictions

Most sports predictions say things like:
- ❌ "Max Verstappen will win"
- ❌ "Lewis Hamilton will finish 3rd"
- ❌ "Ferrari will dominate"

These are **deterministic predictions** — they claim certainty in an inherently uncertain sport. F1 races involve strategy calls, mechanical failures, weather changes, safety cars, driver errors, and pure luck. No one can predict the future with 100% accuracy.

### Our Approach: Probabilistic Predictions

Instead, our system says:
- ✅ "Antonelli has a **48% chance** of winning"
- ✅ "Russell has an **82% chance** of finishing on the podium (P1-P3)"
- ✅ "Verstappen has a **9% chance** of retiring (DNF)"
- ✅ "Piastri has a **94% chance** of scoring points (finishing P1-P10)"

This approach is:
- **More honest**: Acknowledges uncertainty
- **More useful**: Helps you understand risk and opportunity
- **More accurate**: Can be verified and improved over time
- **More educational**: Teaches you about the factors that influence race outcomes

### Key Principles

1. **Anti-Leakage**: We only use information available **before** the race starts. Never use race results to predict themselves.
2. **Transparency**: Every prediction comes with explanations of why (8 different signals).
3. **Calibration**: If we say "30% chance," it should actually happen ~30% of the time across many races.
4. **Interpretability**: You can see exactly which factors drive each prediction.

---

## 👥 Who Is This For?

### 🎯 F1 Fans (No Technical Background Required)
- Want to understand who might win before watching the race
- Curious about why certain drivers perform better at specific circuits
- Interested in learning about data science through F1
- Want to make informed discussions with friends about race predictions

### 📊 Data Scientists & Analysts
- Looking for a real-world probabilistic modeling project
- Want to study Monte Carlo simulation techniques
- Interested in calibration methods (Platt scaling)
- Need examples of feature engineering in sports analytics

### 💻 Developers
- Building F1-related applications or websites
- Want to integrate race predictions into your own projects
- Learning Flask, Python, or REST API development
- Interested in open-source sports analytics projects

### 🎓 Students & Educators
- Teaching probability and statistics through engaging examples
- Demonstrating Monte Carlo methods in action
- Showing how data science applies to real-world problems
- Creating classroom projects around sports analytics

### 🏎️ Fantasy F1 Players
- Need data-driven insights for team selection
- Want to understand driver reliability and consistency
- Looking for edge cases (weather specialists, track experts)
- Making informed decisions about transfers and captain choices

---

## ✨ What's New in v3.0?

Version 3.0 represents a major architectural overhaul with significant new capabilities:

### 🔥 Major Features

#### 1. **SQLite Database Integration**
- All predictions, race results, and driver statistics stored in `f1_predictor.db`
- Automatic historical accuracy tracking with Brier scores
- No more manual data file editing
- Query past predictions and compare against actual results

#### 2. **Fast-F1 Data Synchronization**
- Auto-sync real F1 data from official APIs
- Import historical seasons (2024-2025) automatically
- Lap times, telemetry, weather data integration
- Command: `py main.py migrate-db`

#### 3. **Interactive Web Dashboard**
- Beautiful Flask-based web interface at http://127.0.0.1:5000
- Real-time prediction visualization with Plotly charts
- H2H driver comparison tool
- Constructor championship predictions
- Championship simulator for remaining races
- Historical accuracy tracking dashboard
- No separate API server needed - direct integration!

#### 4. **Vectorized Monte Carlo Simulations**
- NumPy vectorization makes simulations **40x faster**
- 10,000 simulations complete in under 0.1 seconds
- Process all 20+ drivers simultaneously
- Previously: ~2 seconds for 5,000 sims → Now: ~0.05 seconds

#### 5. **Optuna Weight Optimization**
- Bayesian optimization automatically finds optimal feature weights
- Replaces hardcoded FEATURE_WEIGHTS in config/settings.py
- Runs cross-validation across multiple circuits
- Command: `py main.py optimize-weights --trials 100`
- Typically takes 5-15 minutes for full optimization

#### 6. **H2H Driver Comparison**
- Direct head-to-head probability calculations
- "What's the chance Verstappen beats Hamilton at Monaco?"
- Position distribution analysis
- Command: `py main.py h2h --driver1 verstappen --driver2 hamilton --race monaco`

#### 7. **Constructor Predictions**
- Team-level win and podium probabilities
- Aggregated from individual driver predictions
- Useful for constructor championship betting
- Available via dashboard and CLI

#### 8. **Championship Simulator**
- Simulate remaining races to predict final standings
- Monte Carlo approach accounts for uncertainty
- Shows probable driver and constructor champions
- Command: `py main.py championship-sim --remaining 10`

#### 9. **Real-Time Weather API Integration**
- OpenWeatherMap API integration for live forecasts
- Temperature affects tire degradation rates
- Rain probability influences safety car likelihood
- Tire strategy modeling based on conditions
- Automatically falls back to defaults if API unavailable

#### 10. **Enhanced Prediction Tracking**
- Store every prediction with timestamp and parameters
- Post-race evaluation with automatic Brier score calculation
- Track model performance over time
- Identify which circuits/drivers are harder to predict
- Command: `py main.py accuracy-report`

### 🚀 Performance Improvements

| Metric | v2.x | v3.0 | Improvement |
|--------|------|------|-------------|
| Simulation speed | ~2,500 sims/sec | ~100,000 sims/sec | **40x faster** |
| Memory usage | High (Python loops) | Low (NumPy arrays) | **60% reduction** |
| Prediction storage | Manual JSON files | SQLite database | **Automated** |
| Data updates | Manual Python edits | Fast-F1 auto-sync | **Zero effort** |
| Weight tuning | Hardcoded constants | Optuna optimization | **Data-driven** |

---

## 🧠 How Does It Work? (Plain English)

Think of the prediction system as a **four-layer pipeline**. Each layer adds more sophistication until we get final probabilities.

### Layer 1 — Feature Engineering (The 8 Signals)

For every driver in the race, the system calculates **8 numerical "signals"** that capture different aspects of their chances:

#### 1. **ELO Rating** (Driver Skill)
- **What it measures**: Overall driver ability, updated after every race
- **Where it comes from**: Borrowed from chess rating systems
- **Example**: Antonelli = 1642 (very high), Perez = 1575 (experienced)
- **Why it matters**: Better drivers extract more performance from their cars

#### 2. **Constructor Strength** (Car Performance)
- **What it measures**: How good the car is at this specific circuit
- **Circuit-specific**: Mercedes might be strong in Canada but weak in Monaco
- **Example**: Mercedes at Canada = 0.96 (excellent), Cadillac = 0.10 (new team)
- **Why it matters**: In F1, the car is often more important than the driver

#### 3. **Recent Form** (Momentum)
- **What it measures**: How well the driver finished in recent races
- **Weighting**: More recent races count more heavily
- **Example**: Antonelli's last 4 races: [1, 1, 1, 2] = dominant form
- **Why it matters**: Drivers in good form tend to stay in good form

#### 4. **Track Type Fit** (Style Match)
- **What it measures**: Does the driver's style suit this circuit type?
- **Circuit types**: Power circuits, technical circuits, street circuits, etc.
- **Example**: Verstappen excels at power circuits (Red Bull Ring, Monza)
- **Why it matters**: Some drivers prefer high-speed tracks, others prefer technical ones

#### 5. **Grid Position** (Starting Spot)
- **What it measures**: Where the driver starts the race
- **Prediction method**: Based on championship position + qualifying pace
- **Override option**: After Saturday qualifying, you can input actual grid positions
- **Why it matters**: Starting P1 gives a huge advantage; starting P20 is very difficult

#### 6. **Reliability** (DNF Risk)
- **What it measures**: How often does this driver/team retire from races?
- **Data source**: Historical DNF (Did Not Finish) rates
- **Example**: Gasly has 15% recent DNF rate (higher risk)
- **Why it matters**: Finishing the race is step one to scoring points

#### 7. **Weather Adjustment** (Rain Specialist Bonus)
- **What it measures**: Wet skill × probability of rain
- **Wet skill scale**: 0-10 (Hamilton = 9.8, legendary in wet conditions)
- **Example**: If rain_probability = 0.70, Hamilton gets a big bonus
- **Why it matters**: Rain levels the playing field and rewards skill over car

#### 8. **Safety Car Upside** (Chaos Benefit)
- **What it measures**: Will this driver benefit if there's a safety car?
- **Pattern**: Mid-field drivers gain more from safety cars than leaders
- **Why it matters**: Safety cars bunch up the field and create opportunities

### Layer 2 — Composite Score (Combining the Signals)

Each signal is multiplied by a **weight** (how important that signal is) and added together:

```python
composite_score = (0.25 × elo_rating) 
                + (0.20 × constructor_strength) 
                + (0.15 × recent_form) 
                + (0.15 × grid_position)
                + (0.08 × weather_adjustment) 
                + (0.07 × reliability) 
                + (0.05 × safety_car_upside) 
                + (0.05 × track_type_fit)
```

**Key points:**
- Weights sum to 1.0 (100%)
- ELO is most important (25%)
- Constructor strength and recent form are significant (20% and 15%)
- Grid position matters greatly (15%)
- Weather and specialized factors are smaller but impactful

**You can adjust these weights** in `config/settings.py` if you want to experiment!

### Layer 3 — Monte Carlo Simulation (Modeling Chaos)

Here's where it gets interesting. The system doesn't just rank drivers by their composite score. Instead, it runs **10,000 simulated races** (default).

#### Why Simulate?

F1 races are chaotic. Even if Antonelli has the highest composite score, he might:
- Have a bad start
- Get stuck behind slower cars
- Suffer a mechanical failure
- Make a mistake in wet conditions
- Benefit from a perfectly-timed safety car

A single ranking can't capture this uncertainty. But 10,000 simulations can.

#### How Simulation Works

For each of the 10,000 simulated races:
1. Take each driver's composite score
2. Add random "noise" (representing chaos/luck)
3. Rank drivers based on noisy scores
4. Record finishing positions
5. Check for DNFs (based on reliability probabilities)
6. Apply safety car effects randomly

After 10,000 simulations, we count:
- **Win probability**: How many times did each driver finish P1?
- **Podium probability**: How many times did they finish P1-P3?
- **Points probability**: How many times did they finish P1-P10?
- **DNF probability**: How many times did they retire?

**Example result:**
If Antonelli wins 4,800 out of 10,000 simulations → Win probability = 48%

### Layer 4 — Platt Calibration (Making Probabilities Honest)

Raw simulation probabilities aren't always perfectly calibrated. If the model says "30% chance," it might actually happen 25% or 35% of the time.

**Platt scaling** is a mathematical technique that adjusts raw probabilities to make them better calibrated. It uses historical data to learn:
- When the model is overconfident (says 60%, happens 45%)
- When the model is underconfident (says 40%, happens 55%)

After calibration:
- "30% probability" actually happens ~30% of the time
- "70% probability" actually happens ~70% of the time
- The model becomes trustworthy for decision-making

**IMPORTANT NOTE:** As of v3.0, Platt calibration parameters are set to near-identity values (A≈1.0, B≈0.0) because we're building the historical dataset. This means calibration currently has minimal effect on raw probabilities. 

**The architecture supports proper Platt calibration**, which will be fitted once sufficient historical race data is available (typically after 12+ races). Until then, predictions rely primarily on well-calibrated Monte Carlo simulation with realistic noise levels (σ=0.15-0.23).

To fit proper calibration parameters after more races:
```bash
py scripts/recalibrate_model.py --fit-platt
```

This will use actual race outcomes to learn optimal A/B parameters for each outcome type (win/top3/top10/dnf).

---

## 🎲 Understanding Probabilities vs. Certainties

This is the **most important concept** to understand when using this system.

### What Does "48% Win Probability" Mean?

It does **NOT** mean:
- ❌ "Antonelli will definitely win"
- ❌ "There's a 48% chance he wins THIS specific race"
- ❌ "He's almost certain to win"

It **DOES** mean:
- ✅ "If we ran this exact same race 100 times, Antonelli would win about 48 of them"
- ✅ "Out of many similar races, he wins roughly half"
- ✅ "He's the favorite, but far from guaranteed"

### Why This Matters

Imagine you're planning a picnic and the forecast says "30% chance of rain."

- Do you cancel the picnic? Probably not.
- Do you bring an umbrella? Maybe.
- Are you surprised if it rains? No — 30% means it happens sometimes.

Similarly with F1 predictions:
- A driver with 10% win probability **will** win occasionally
- A driver with 90% win probability **will** lose sometimes
- The probabilities describe long-term patterns, not individual outcomes

### Confidence Levels

The system also provides a **Confidence** rating:

| Confidence | What It Means | Example |
|------------|---------------|---------|
| **High** | Model is very sure about this prediction | Favorite with clear advantage |
| **Medium** | Moderate uncertainty | Competitive midfield battle |
| **Low** | High uncertainty | Unpredictable conditions (wet race, new circuit) |

**High confidence** doesn't mean the driver will win — it means the model is confident in its probability estimate.

---

## 🚀 Quick Start Guide

**Want to see predictions right now?** Follow these steps:

### Step 1: Install Python
Download from [python.org](https://python.org) (version 3.10 or higher)

### Step 2: Download This Project
Download the project files to your computer.

### Step 3: Set Up Virtual Environment
```bat
py -m venv .venv
.venv\Scripts\activate
```

You'll see `(.venv)` at the start of your command line — that means it's active.

### Step 4: Install Dependencies
```bat
pip install -r requirements.txt
```

This installs all necessary packages (Flask, NumPy, Rich, FastF1, SQLAlchemy, etc.).

### Step 5: Initialize Database
```bat
py main.py migrate-db
```

### Step 6: Run Your First Prediction
```bat
py main.py predict --race canada --sims 10000
```

### Step 7: Launch the Dashboard
```bat
py main.py dashboard
```

Open your browser to: **http://127.0.0.1:5000**

---

## 🛠️ Installation (Step by Step)

### Prerequisites

**Required:**
- Python 3.10 or higher ([download here](https://python.org))
- A terminal/command prompt (Command Prompt, PowerShell, Terminal, etc.)

**Optional:**
- Visual Studio Code or any code editor
- OpenWeatherMap API key (only if you want live weather data)

### Detailed Installation Steps

#### Step 1 — Verify Python Installation

Open your terminal and type:
```bat
py --version
```

You should see something like:
```
Python 3.10.11
```

If you get an error or a version lower than 3.10, download Python from [python.org](https://python.org) and install it.

**Windows users**: During installation, check the box that says "Add Python to PATH".

#### Step 2 — Create a Virtual Environment

**What is a virtual environment?**
Think of it as a clean, isolated workspace just for this project. It keeps the project's packages separate from your system Python, preventing conflicts with other projects.

**Create it:**
```bat
py -m venv .venv
```

This creates a `.venv` folder in your project directory.

**Activate it:**
```bat
.venv\Scripts\activate
```

**How do I know it's activated?**
You'll see `(.venv)` at the start of your command line:
```
(.venv) C:\Users\PC\Music\FORMULA_1_PREDICTOR_2026>
```

**Important**: You must activate the virtual environment **every time** you open a new terminal window to work on this project.

#### Step 3 — Install Dependencies

With the virtual environment activated, run:
```bat
pip install -r requirements.txt
```

This installs all required packages:
- **Flask**: Web framework for the dashboard
- **NumPy**: Numerical computing (for simulations)
- **SciPy**: Scientific computing (for calibration)
- **scikit-learn**: Machine learning library (Platt scaling)
- **Rich**: Beautiful terminal output
- **Jinja2**: HTML template engine
- **Click**: Command-line interface framework
- **Pydantic**: Data validation
- **pytest**: Testing framework
- **SQLAlchemy**: Database ORM
- **FastF1**: Official F1 data library
- **Plotly**: Interactive charting
- **Optuna**: Bayesian optimization

This might take 2-3 minutes. You'll see lots of text scrolling by — that's normal!

#### Step 4 — Initialize Database

```bat
py main.py migrate-db
```

This creates the SQLite database (`f1_predictor.db`) with all necessary tables.

---

## 🎮 How to Use It

You have **three main ways** to interact with the prediction system:

### Option 1 — CLI for Any Race (Flexible)

Use the main command-line interface to predict any circuit.

```bat
:: Predict any circuit by ID
py main.py predict --race canada
py main.py predict --race monaco
py main.py predict --race britain

:: Override rain probability
py main.py predict --race brazil --rain 0.70

:: Use exact grid positions after Saturday qualifying
py main.py predict --race canada --grid-override "antonelli:1,hamilton:3,norris:2"

:: Get raw JSON output (useful for scripting)
py main.py predict --race canada --json-out

:: Generate prediction AND automatically create HTML report
py main.py predict --race canada --auto-report

:: Save predictions to file
py main.py predict --race canada --export predictions.json
py main.py predict --race canada --export predictions.csv

:: Custom number of simulations
py main.py predict --race monaco --sims 10000

:: Store prediction in database for accuracy tracking
py main.py predict --race canada --store
```

**Optional flags:**
- `--rain <0.0-1.0>`: override rain probability
- `--seed <int>`: reproducible randomness
- `--grid-override "driver_id:pos,driver_id:pos"`
- `--json-out`: raw JSON
- `--auto-report`: generates HTML under `output/`
- `--store`: stores prediction in SQLite (accuracy tracking)
- `--export <file.json|file.csv>`: exports predictions
- `--vectorized`: use fast NumPy simulation (default: True)

### Enhanced HTML Reports

The system generates beautiful, interactive HTML reports with **6 visualization charts**:

**What's included in each report:**
- 🏁 Complete race details (name, circuit, city, date, round number)
- 📊 Win & Podium Probabilities (bar chart)
- ⚠️ DNF Risk Analysis (line chart)
- 🎯 Top 10 Finish Probability (bar chart)
- 👥 Teammate Battle Probability (color-coded bar chart)
- ⭐ Composite Performance Score (radar chart)
- 📈 Position Distribution Heatmap (stacked bar chart for top 5 drivers)
- 🏎️ Driver Circuit History (historical wins, podiums, poles, confidence ratings)
- Full prediction table with all probabilities
- Predicted podium display

**Generate a report:**
```bat
py main.py report --race canada --output ./my_canada_report.html
```

**Viewing reports:**
HTML reports use Chart.js from CDN, so you need an internet connection. For best results, serve them locally:
```bat
:: Start a local web server
py -m http.server 8080 --directory output
```

Then open: http://localhost:8080/canada_prediction_report.html

⚠️ **Important**: Don't open HTML files directly with `file://` protocol - charts may not load due to browser security restrictions.

### Option 2 — Web Dashboard

```bat
py main.py dashboard --port 5000
```

Then open your browser to: **http://127.0.0.1:5000**

See the [Web Dashboard section](#-web-dashboard) for full feature details.

### Option 3 — Head-to-Head Comparison

Compare two drivers directly:

```bat
py main.py h2h --driver1 antonelli --driver2 russell --race canada
py main.py h2h --driver1 verstappen --driver2 hamilton --race monaco
```

Shows:
- Probability each driver finishes ahead
- Average predicted positions
- Position distribution comparison
- Perfect for rivalry analysis

### Other Useful Commands

```bat
:: List all available circuit IDs
py main.py circuits

:: Optimize model weights (takes 5-15 minutes)
py main.py optimize-weights --trials 100

:: View historical prediction accuracy
py main.py accuracy-report

:: Simulate championship with remaining races
py main.py championship-sim --remaining 10

:: Run data quality checks
py main.py quality-check

:: Benchmark simulation performance
py main.py benchmark --circuit canada --sims 10000
```

---

## 📊 Understanding the Output

When you run a prediction, you get a table like this:

```
🏁 Canadian Grand Prix 2026 — Race Predictions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P   Driver              Team            Win%   Top3%  Top10%  DNF%   T/M%  Conf
───────────────────────────────────────────────────────────────────────────────────
🥇  Kimi Antonelli      Mercedes        48.2   82.1   96.0    4.0    95%   High
🥈  George Russell      Mercedes        18.1   65.3   94.0    5.0    5%    High
🥉  Lando Norris        McLaren         12.3   52.4   88.0    6.0    88%   Medium
4   Max Verstappen      Red Bull        8.1    38.2   80.0    9.0    72%   Medium
5   Charles Leclerc     Ferrari         6.5    32.1   75.0    11.0   68%   Medium
...
```

### Column Definitions

| Column | Meaning | How to Interpret |
|--------|---------|------------------|
| **P** | Predicted finishing position | Expected rank based on simulations |
| **Driver** | Driver name | Self-explanatory |
| **Team** | Constructor | Which team they drive for |
| **Win%** | Probability of winning (P1) | "If we ran this race 100 times, they'd win X times" |
| **Top3%** | Probability of podium (P1-P3) | Chance of finishing on the podium |
| **Top10%** | Probability of scoring points (P1-P10) | Chance of finishing in the points |
| **DNF%** | Probability of retiring | Chance of Did Not Finish (mechanical, crash, etc.) |
| **T/M%** | Teammate beat % | Probability of beating their teammate |
| **Conf** | Model's confidence level | High/Medium/Low uncertainty |

### Key Insights

**Probabilities Sum to ~100%**
If you add up all drivers' win probabilities, you get approximately 100% (might be 99.8% or 100.2% due to rounding).

**Top3% ≥ Win%**
A driver's podium probability is always greater than or equal to their win probability (you can't finish P2 without finishing P1-P3).

**Top10% ≥ Top3%**
Similarly, points probability is always ≥ podium probability.

**DNF% Varies Widely**
- Reliable teams (Mercedes, Red Bull): 4-8%
- Mid-field teams: 10-15%
- New/unreliable teams: 20-30%


## HTML Report

<img src="sc1.png" alt="HTML Report" width="600"/>
---

## 🌐 Web Dashboard Features (NEW in v3.0)

The interactive web dashboard provides a beautiful, user-friendly interface for all prediction features without requiring command-line usage.

### Dashboard Features

#### 1. **Race Prediction Interface**
- Select any circuit from dropdown menu
- Adjust rain probability slider (0-100%)
- Set number of simulations (1,000 - 50,000)
- View predictions in interactive table
- Beautiful Plotly bar charts showing win probabilities
- Color-coded confidence indicators

#### 2. **Head-to-Head Comparison Tool**
- Compare any two drivers directly
- See probability of each driver finishing ahead
- Average position predictions
- Position distribution visualization
- Perfect for rivalry analysis

#### 3. **Constructor Predictions**
- Team-level win and podium probabilities
- Aggregated from individual driver performance
- Constructor championship implications
- Useful for team-focused betting strategies

#### 4. **Championship Simulator**
- Simulate remaining races (select how many)
- Monte Carlo approach shows probable outcomes
- Driver championship standings projection
- Constructor championship standings projection
- Accounts for uncertainty in future races

#### 5. **Historical Accuracy Tracking**
- View Brier scores for past predictions
- Calibration curves showing model honesty
- Per-circuit accuracy breakdown
- Identify which predictions are most reliable
- Track model improvement over time

### Technical Details

- **Framework**: Flask with Jinja2 templates
- **Charts**: Plotly.js for interactive visualizations
- **Styling**: Modern CSS with gradient backgrounds
- **Integration**: Direct calls to prediction engine (no separate API needed)
- **Performance**: Predictions complete in <1 second for standard simulations
- **Responsive**: Works on desktop and mobile browsers

---

## 🗺️ Available Circuits (2026 Season)

The 2026 F1 season features **24 races** across 5 continents. Use these circuit IDs with `--race` or in API calls:

To see all circuit IDs:
```bat
py main.py circuits
```

| ID | Circuit | Country | Round | Sprint? |
|----|---------|---------|-------|---------|
| `australia` | Albert Park | Australia | R1 | No |
| `china` | Shanghai International | China | R2 | ⚡ Yes |
| `japan` | Suzuka | Japan | R3 | No |
| `bahrain` | Bahrain International | Bahrain | R4 | No |
| `saudi_arabia` | Jeddah Corniche | Saudi Arabia | R5 | ⚡ Yes |
| `miami` | Miami Autodrome | USA | R6 | ⚡ Yes |
| `canada` | Gilles-Villeneuve | Canada | R7 | No |
| `spain` | Barcelona-Catalunya | Spain | R9 | No |
| `monaco` | Circuit de Monaco | Monaco | R8 | No |
| `britain` | Silverstone | UK | R10 | No |

⚡ = Sprint weekend (shorter race on Saturday)

### New for 2026

**Madrid Street Circuit (Round 16)**
- Brand new street circuit in Spain's capital
- Located around IFEMA exhibition center
- 5.474 km length, 20 corners
- Replaces Imola (Emilia-Romagna GP removed)

**Spain Now Has Two Races**
- Barcelona (Round 9): Traditional Spanish GP
- Madrid (Round 16): New Spanish GP (street circuit)

**24-Race Calendar**
- Longest season in F1 history
- Three triple-headers (three races in three weeks)
- Optimized logistics to reduce travel

---

## 📂 Project Structure Explained

```
FORMULA_1_PREDICTOR_2026/
│
├── 📄 main.py                     ← Main entry point (CLI commands)
│                                    All commands: predict, h2h, dashboard, etc.
│
├── 📁 config/                     ← Configuration files
│   └── settings.py                ← All tunable parameters
│                                    FEATURE_WEIGHTS, thresholds, defaults
│
├── 📁 data/                       ← All F1 data (the knowledge base)
│   ├── driver_data.py             ← 22 driver profiles
│   ├── circuit_data.py            ← 24 circuit descriptions
│   ├── season_2026.py             ← 2026 season results & standings
│   ├── calendar_2026.py           ← Full 2026 race schedule
│   ├── driver_traits_database.py  ← Historical driver performance data
│   └── fastf1_integration.py      ← Fast-F1 data sync
│
├── 📁 engine/                     ← The prediction brain (core logic)
│   ├── feature_engineering.py     ← Calculates 8 signals per driver
│   ├── probability_model.py       ← Monte Carlo simulation engine
│   ├── predictor.py               ← Orchestrates the prediction pipeline
│   ├── vectorized_simulation.py   ← NumPy vectorized simulations (40x faster)
│   ├── calibration.py             ← Platt scaling implementation
│   ├── weather_model_v3.py        ← Weather API integration
│   ├── tire_strategy.py           ← Tire degradation modeling
│   ├── multi_dimensional_elo.py   ← Advanced ELO rating system
│   └── optimized_simulation.py    ← Alternative simulation methods
│
├── 📁 database/                   ← SQLite database layer
│   ├── models.py                  ← SQLAlchemy ORM models
│   └── __init__.py
│
├── 📁 dashboard/                  ← Web dashboard
│   ├── app.py                     ← Flask application
│   └── templates/dashboard.html   ← Web interface
│
├── 📁 reports/                    ← Report generation
│   └── html_report.py             ← Creates standalone HTML files
│
├── 📁 scripts/                    ← Standalone utility scripts
│   ├── recalibrate_model.py       ← Check model accuracy & calibration
│   ├── optimize_weights_v3.py     ← Optuna Bayesian optimization
│   ├── backtest_2025_season.py    ← Test model against 2025 data
│   ├── post_race_evaluation.py    ← Analyze prediction accuracy
│   ├── data_quality_report.py     ← Validate data integrity
│   └── ingest_f1_data.py          ← Import external F1 data
│
├── 📁 tests/                      ← Unit and integration tests
│   ├── test_feature_engineering.py
│   └── test_integration.py
│
├── 📄 requirements.txt            ← Python dependencies
├── 📄 README.md                   ← This file
└── 📄 cleanup_and_test.bat        ← Windows batch script for testing
```

---

## 🗄️ Database & Data Management

### SQLite Database

The system uses SQLite for persistent storage:

**What's stored:**
- All race predictions with timestamps
- Actual race results for comparison
- Driver and constructor championship standings
- Historical accuracy metrics (Brier scores)
- Calibration parameters

**Database location:** `f1_predictor.db` (created automatically)

**Initialize database:**
```bat
py main.py migrate-db
```

### Fast-F1 Integration

**Sync real F1 data:**
```bat
py main.py migrate-db
```

This pulls:
- Historical race results
- Qualifying data
- Lap times and telemetry
- Weather conditions
- Driver and constructor information

### Data Quality Checks

Validate data integrity:
```bat
py main.py quality-check
```

Checks:
- All 22 drivers present with valid data
- All 24 circuits defined correctly
- Championship standings add up properly
- No missing ELO ratings or stats
- Driver-team assignments consistent

---

## 📈 Model Accuracy & Calibration

### Tracking Accuracy

Store predictions and track accuracy:
```bat
py main.py predict --race canada --store
```

View accuracy report:
```bat
py main.py accuracy-report
```

**Metrics tracked:**
- **Brier Score**: Measures probability calibration (lower is better)
- **Calibration Curve**: Shows if predicted probabilities match reality
- **Per-circuit accuracy**: Identify which tracks are harder to predict
- **Driver-specific accuracy**: Some drivers are more predictable than others

### Recalibrating the Model

After several races, recalibrate:
```bat
py scripts/recalibrate_model.py --fit-platt
```

This learns optimal Platt scaling parameters from actual race outcomes.

### Backtesting

Test model against historical data:
```bat
py main.py backtest --seasons 2025
```

Or run the comprehensive backtest:
```bat
py scripts/backtest_2025_season.py
```

---

## ⚡ Performance Optimization

### Vectorized Simulations

The default simulation mode uses NumPy vectorization for maximum speed:

**Benchmark performance:**
```bat
py main.py benchmark --circuit canada --sims 10000
```

Typical results:
- Vectorized: ~0.05 seconds for 10,000 simulations
- Original (Python loops): ~2 seconds for 5,000 simulations
- **Speedup: 40x faster**

### Optuna Weight Optimization

Find optimal feature weights automatically:
```bat
py main.py optimize-weights --trials 100
```

This:
- Tests different weight combinations
- Uses cross-validation across multiple circuits
- Finds weights that minimize prediction error
- Takes 5-15 minutes depending on trial count

**Save optimized weights:**
```bat
py main.py optimize-weights --trials 100 --output optimized_weights.json
```

Then update `config/settings.py` with the optimized values.

---

## 🔧 Troubleshooting

### Common Issues

#### 1. **"Module not found" errors**
```bat
:: Make sure virtual environment is activated
.venv\Scripts\activate

:: Reinstall dependencies
pip install -r requirements.txt
```

#### 2. **Database errors**
```bat
:: Delete and recreate database
del f1_predictor.db
py main.py migrate-db
```

#### 3. **Circuit not found**
```bat
:: List all available circuit IDs
py main.py circuits
```

#### 4. **HTML charts not loading**
- Don't open HTML files directly with `file://` protocol
- Use a local web server instead:
```bat
py -m http.server 8080 --directory output
```

#### 5. **Slow predictions**
- Ensure `--vectorized` flag is used (it's default)
- Reduce simulation count: `--sims 5000` instead of 10000
- Close other CPU-intensive applications

#### 6. **Dashboard won't start**
```bat
:: Check if port is already in use
netstat -ano | findstr :5000

:: Try a different port
py main.py dashboard --port 5001
```

### Getting Help

If you encounter issues:
1. Run quality checks: `py main.py quality-check`
2. Check terminal output for error messages
3. Verify Python version: `py --version` (must be 3.10+)
4. Ensure all dependencies installed: `pip list`

---

## 🏎️ 2026 Season Context

### Key Changes for 2026

**New Teams:**
- **Cadillac**: New American team entering F1
- Drivers: Sergio Perez, Valtteri Bottas

**Driver Movements:**
- Kimi Antonelli promoted to Mercedes (replacing Hamilton)
- Lewis Hamilton moved to Ferrari
- Various midfield shuffles

**Calendar Changes:**
- 24 races (longest season ever)
- Madrid street circuit added (Round 16)
- Imola removed
- Spain now hosts two races (Barcelona + Madrid)

**Technical Regulations:**
- New aerodynamic rules
- Updated power unit specifications
- Revised tire compounds

### Current Standings (After Round 4)

**Driver Championship:**
1. Kimi Antonelli (Mercedes) - Leading
2. George Russell (Mercedes)
3. Lando Norris (McLaren)
4. Max Verstappen (Red Bull)
5. Oscar Piastri (McLaren)

**Constructor Championship:**
1. Mercedes - Dominant early season
2. McLaren - Strong challenger
3. Red Bull - Adjusting to new regulations
4. Ferrari - Building momentum
5. Others

*Note: These are example standings. Update with actual 2026 data as season progresses.*

---

## 💻 Technology Stack

### Core Technologies

**Language:** Python 3.10+

**Data Science:**
- **NumPy**: Numerical computing and array operations
- **pandas**: Data manipulation and analysis
- **scikit-learn**: Machine learning (Platt calibration)
- **SciPy**: Scientific computing

**Database:**
- **SQLite**: Lightweight relational database
- **SQLAlchemy**: Object-relational mapping (ORM)

**Web Framework:**
- **Flask**: Web server and routing
- **Flask-CORS**: Cross-origin resource sharing
- **Jinja2**: HTML template rendering
- **Plotly**: Interactive data visualization

**Optimization:**
- **Optuna**: Bayesian hyperparameter optimization

**Data Sources:**
- **FastF1**: Official F1 data library
- **OpenWeatherMap**: Weather API (optional)

**CLI & UI:**
- **Click**: Command-line interface framework
- **Rich**: Beautiful terminal output

**Testing:**
- **pytest**: Unit and integration testing

### Architecture

**Design Patterns:**
- Factory pattern for predictor instances
- Strategy pattern for feature calculations
- MVC pattern for report generation
- Observer pattern for prediction tracking

**Layers:**
1. **Data Layer**: Static data modules + SQLite database
2. **Engine Layer**: Prediction algorithms and simulations
3. **Interface Layer**: CLI commands and web dashboard
4. **Application Layer**: Scripts and utilities

---

## 📚 Glossary for Beginners

### F1 Terms

| Term | Definition |
|------|------------|
| **P1/P2/P3** | Position 1/2/3 (winner, 2nd place, 3rd place) |
| **Podium** | Finishing in P1, P2, or P3 |
| **Points** | Scoring positions P1-P10 (25, 18, 15, 12, 10, 8, 6, 4, 2, 1 points) |
| **DNF** | Did Not Finish (retired from race) |
| **Grid Position** | Starting position for the race |
| **Qualifying** | Saturday session that determines grid positions |
| **Safety Car (SC)** | Car deployed during incidents, bunches up field |
| **Sprint Weekend** | Format with shorter Saturday race |
| **Constructor** | F1 term for "team" (e.g., Mercedes, Ferrari) |
| **Teammate** | Other driver on same team |

### Data Science Terms

| Term | Definition |
|------|------------|
| **Probability** | Likelihood of an event (0% = impossible, 100% = certain) |
| **Monte Carlo Simulation** | Running thousands of simulated scenarios |
| **Calibration** | Ensuring predicted probabilities match reality |
| **Feature Engineering** | Creating meaningful inputs for prediction models |
| **ELO Rating** | Skill rating system borrowed from chess |
| **Brier Score** | Measure of prediction accuracy (lower is better) |
| **Vectorization** | Using NumPy arrays for fast parallel computation |
| **Bayesian Optimization** | Smart search for optimal parameters |
| **Cross-Validation** | Testing model on multiple datasets |
| **Overfitting** | Model works on training data but fails on new data |

### Technical Terms

| Term | Definition |
|------|------------|
| **CLI** | Command-Line Interface (text-based commands) |
| **API** | Application Programming Interface (how programs talk) |
| **ORM** | Object-Relational Mapping (database abstraction) |
| **Virtual Environment** | Isolated Python workspace |
| **Dependencies** | External libraries your code needs |
| **Repository** | Project folder with all files |
| **Commit** | Saved change in version control |

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

1. **Report Bugs**: Found something broken? Let us know!
2. **Suggest Features**: Have ideas for improvements? Share them!
3. **Improve Documentation**: Help make explanations clearer
4. **Add Tests**: Increase test coverage
5. **Optimize Code**: Make things faster or cleaner
6. **Update Data**: Keep driver stats and circuit info current

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** your changes thoroughly
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Code Standards

- Follow PEP 8 Python style guide
- Write docstrings for all functions
- Add type hints where helpful
- Include tests for new features
- Update documentation as needed

### Running Tests

```bat
py -m pytest tests/ -v
```

### Before Submitting

- [ ] Code follows project style
- [ ] Tests pass successfully
- [ ] Documentation updated
- [ ] No sensitive data committed
- [ ] Changes are focused and minimal

---

## 📄 License

This project is open-source and available for educational and non-commercial use.

### Usage Guidelines

✅ **You can:**
- Use for personal predictions and analysis
- Learn from the code and algorithms
- Modify and experiment with the model
- Share insights and results
- Contribute improvements

❌ **You cannot:**
- Use for commercial betting services
- Sell predictions as a service
- Claim the code as your own
- Remove attribution

### Disclaimer

**This is a hobby project for educational purposes.**

- Predictions are probabilistic estimates, not guarantees
- Past performance does not guarantee future results
- Always gamble responsibly if using for betting
- The authors are not responsible for any losses
- F1 trademarks belong to their respective owners

---

## 🙏 Acknowledgments

### Inspiration

- Chess ELO rating system (Arpad Elo)
- FiveThirtyEight's sports forecasting
- Formula 1's official data and statistics
- The F1 community's passion for data analysis

### Libraries & Tools

Thanks to the maintainers of:
- NumPy, pandas, scikit-learn
- Flask, Click, Rich
- FastF1, SQLAlchemy, Plotly
- Optuna, pytest

### Community

Special thanks to:
- F1 fans who provided feedback
- Data scientists who shared techniques
- Developers who contributed code
- Everyone who reported bugs and suggestions

---

## 📞 Contact & Support

### Questions?

- Check this README first
- Review the troubleshooting section
- Look at example commands above
- Run `py main.py --help` for CLI options

### Updates

Stay updated with:
- Version releases
- New features
- Model improvements
- Season data updates

### Feedback

We love hearing from users! Share:
- Your predictions and results
- Feature requests
- Bug reports
- Success stories

---

## 🎯 Final Thoughts

**Remember:** This system provides **probabilities**, not certainties. The beauty of F1 is its unpredictability. Even with sophisticated models, surprises happen every race.

**Use this tool to:**
- Enhance your understanding of F1
- Make more informed predictions
- Learn about probability and data science
- Have fun analyzing races

**Don't use this to:**
- Guarantee outcomes
- Replace watching the actual race
- Bet irresponsibly
- Assume certainty where none exists

Enjoy the 2026 F1 season, and may the probabilities be ever in your favor! 🏁

---

*Last updated: June 2026 | Version 3.0*
