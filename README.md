# 🏁 F1MLpredictions2026
### A Probabilistic Formula One Race Outcome Prediction System

> **Built for:** Data scientists, F1 fans, developers, and anyone curious about how probability and data science can predict the unpredictable world of Formula 1 racing.

---

## 📖 Table of Contents

1. [What Is This Project?](#-what-is-this-project)
2. [Who Is This For?](#-who-is-this-for)
3. [How Does It Work? (Plain English)](#-how-does-it-work-plain-english)
4. [Understanding Probabilities vs. Certainties](#-understanding-probabilities-vs-certainties)
5. [Quick Start Guide](#-quick-start-guide)
6. [Installation (Step by Step)](#-installation-step-by-step)
7. [How to Use It](#-how-to-use-it)
8. [Understanding the Output](#-understanding-the-output)
9. [REST API Guide](#-rest-api-guide)
10. [Available Circuits (2026 Season)](#-available-circuits-2026-season)
11. [Project Structure Explained](#-project-structure-explained)
12. [Keeping the Model Up-to-Date](#-keeping-the-model-up-to-date)
13. [Model Accuracy & Calibration](#-model-accuracy--calibration)
14. [Troubleshooting](#-troubleshooting)
15. [Performance Guide](#-performance-guide)
16. [2026 Season Context](#-2026-season-context)
17. [Technology Stack](#-technology-stack)
18. [Glossary for Beginners](#-glossary-for-beginners)
19. [Contributing](#-contributing)
20. [License](#-license)

---

## 📖 What Is This Project?

**F1MLpredictions2026** is a sophisticated prediction system that forecasts Formula One race outcomes **before the race starts**. Unlike traditional prediction methods that simply guess "who will win," this system provides **probabilistic predictions** — honest, data-driven estimates of what might happen.

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
- Learning FastAPI, Python, or REST API development
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
composite_score = (0.20 × elo_score) 
                + (0.20 × constructor_strength) 
                + (0.15 × recent_form) 
                + (0.12 × track_type_fit)
                + (0.12 × grid_position_score) 
                + (0.10 × reliability_score) 
                + (0.07 × weather_adjustment) 
                + (0.04 × safety_car_upside)
```

**Key points:**
- Weights sum to 1.0 (100%)
- ELO and Constructor are most important (20% each)
- Weather and Safety Car are smaller factors (7% and 4%)
- Drivers with higher composite scores are expected to finish better

**You can adjust these weights** in `config/settings.py` if you want to experiment!

### Layer 3 — Monte Carlo Simulation (Modeling Chaos)

Here's where it gets interesting. The system doesn't just rank drivers by their composite score. Instead, it runs **5,000 simulated races**.

#### Why Simulate?

F1 races are chaotic. Even if Antonelli has the highest composite score, he might:
- Have a bad start
- Get stuck behind slower cars
- Suffer a mechanical failure
- Make a mistake in wet conditions
- Benefit from a perfectly-timed safety car

A single ranking can't capture this uncertainty. But 5,000 simulations can.

#### How Simulation Works

For each of the 5,000 simulated races:
1. Take each driver's composite score
2. Add random "noise" (representing chaos/luck)
3. Rank drivers based on noisy scores
4. Record finishing positions
5. Check for DNFs (based on reliability probabilities)
6. Apply safety car effects randomly

After 5,000 simulations, we count:
- **Win probability**: How many times did each driver finish P1?
- **Podium probability**: How many times did they finish P1-P3?
- **Points probability**: How many times did they finish P1-P10?
- **DNF probability**: How many times did they retire?

**Example result:**
If Antonelli wins 2,400 out of 5,000 simulations → Win probability = 48%

### Layer 4 — Platt Calibration (Making Probabilities Honest)

Raw simulation probabilities aren't always perfectly calibrated. If the model says "30% chance," it might actually happen 25% or 35% of the time.

**Platt scaling** is a mathematical technique that adjusts raw probabilities to make them better calibrated. It uses historical data to learn:
- When the model is overconfident (says 60%, happens 45%)
- When the model is underconfident (says 40%, happens 55%)

After calibration:
- "30% probability" actually happens ~30% of the time
- "70% probability" actually happens ~70% of the time
- The model becomes trustworthy for decision-making

**Technical detail:** Platt scaling uses a sigmoid function with learned parameters (PLATT_A_WIN, PLATT_B_WIN) defined in `engine/probability_model.py`.

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

### Common Misconceptions

❌ **"The model predicted Verstappen would win, but he finished 5th. The model is wrong!"**

✅ **Reality**: If Verstappen had a 40% win probability, that means he loses 60% of the time. Finishing 5th is within the realm of possibility. One race doesn't invalidate the model.

❌ **"Norris has 12% win probability and Piastri has 8%. Norris is 50% more likely to win."**

✅ **Reality**: Yes, but both are unlikely to win. The more meaningful comparison is their podium probabilities or expected finishing positions.

❌ **"The model said 82% podium probability, so Russell should definitely be on the podium."**

✅ **Reality**: 82% means he misses the podium 18% of the time (about 1 in 5 races). That's not rare at all.

---

## 🚀 Quick Start Guide

**Want to see predictions right now?** Follow these 5 steps:

### Step 1: Install Python
Download from [python.org](https://python.org) (version 3.10 or higher)

### Step 2: Download This Project
```bash
git clone https://github.com/YOUR_USERNAME/f1-prediction-system.git
cd f1-prediction-system
```

Or download the ZIP file from GitHub and unzip it.

### Step 3: Set Up Virtual Environment
```bash
# Windows (PowerShell)
py -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

You'll see `(.venv)` at the start of your command line — that means it's active.

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs all necessary packages (FastAPI, NumPy, Rich, etc.).

### Step 5: Run Your First Prediction
```bash
py scripts/run_canada_gp_2026.py
```

Wait about 10 seconds, and you'll see a beautiful prediction table showing win probabilities, podium chances, and DNF risks for all 22 drivers!

**That's it!** You've just run your first F1 race prediction.

---

## 🛠️ Installation (Step by Step)

### Prerequisites

**Required:**
- Python 3.10 or higher ([download here](https://python.org))
- Git (optional, but recommended for cloning)
- A terminal/command prompt (Command Prompt, PowerShell, Terminal, etc.)

**Optional:**
- Visual Studio Code or any code editor
- OpenWeatherMap API key (only if you want live weather data)

### Detailed Installation Steps

#### Step 1 — Verify Python Installation

Open your terminal and type:
```bash
py --version
```

You should see something like:
```
Python 3.10.11
```

If you get an error or a version lower than 3.10, download Python from [python.org](https://python.org) and install it.

**Windows users**: During installation, check the box that says "Add Python to PATH".

#### Step 2 — Download the Project

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/YOUR_USERNAME/f1-prediction-system.git
cd f1-prediction-system
```

**Option B: Download ZIP**
1. Go to the GitHub repository
2. Click the green "Code" button
3. Select "Download ZIP"
4. Unzip the file to a folder
5. Open terminal in that folder

#### Step 3 — Create a Virtual Environment

**What is a virtual environment?**
Think of it as a clean, isolated workspace just for this project. It keeps the project's packages separate from your system Python, preventing conflicts with other projects.

**Create it:**
```bash
# Windows (PowerShell)
py -m venv .venv

# Mac/Linux
python3 -m venv .venv
```

This creates a `.venv` folder in your project directory.

**Activate it:**
```bash
# Windows (PowerShell)
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

**How do I know it's activated?**
You'll see `(.venv)` at the start of your command line:
```
(.venv) C:\Users\PC\Music\F1MLpredictions2>
```

**Important**: You must activate the virtual environment **every time** you open a new terminal window to work on this project.

#### Step 4 — Install Dependencies

With the virtual environment activated, run:
```bash
pip install -r requirements.txt
```

This installs all required packages:
- **FastAPI**: Web framework for the API
- **NumPy**: Numerical computing (for simulations)
- **SciPy**: Scientific computing (for calibration)
- **scikit-learn**: Machine learning library (Platt scaling)
- **Rich**: Beautiful terminal output
- **Jinja2**: HTML template engine
- **Click**: Command-line interface framework
- **Pydantic**: Data validation
- **pytest**: Testing framework

This might take 1-2 minutes. You'll see lots of text scrolling by — that's normal!

#### Step 5 — Verify Installation

Run a test prediction:
```bash
py scripts/run_canada_gp_2026.py --no-report
```

If everything is installed correctly, you'll see a prediction table appear in about 10 seconds.

**Congratulations!** Your setup is complete.

---

## 🎮 How to Use It

You have **four ways** to interact with the prediction system:

### Option 1 — One-Command Prediction (Easiest)

Perfect for quick predictions without any configuration.

```bash
# Predict the Canadian GP with default settings
py scripts/run_canada_gp_2026.py

# Predict with custom rain probability (0.0 = dry, 1.0 = definitely wet)
py scripts/run_canada_gp_2026.py --rain 0.80

# More accurate but slower (20,000 simulations instead of 5,000)
py scripts/run_canada_gp_2026.py --sims 20000

# Skip HTML report generation (faster)
py scripts/run_canada_gp_2026.py --no-report
```

**When to use this:**
- Quick pre-race analysis
- Comparing different weather scenarios
- Sharing predictions with friends

### Option 2 — CLI for Any Race (Flexible)

Use the main command-line interface to predict any circuit.

```bash
# Predict any circuit by ID
py main.py predict --race canada
py main.py predict --race monaco
py main.py predict --race britain        # Silverstone

# Override rain probability
py main.py predict --race brazil --rain 0.70

# Use exact grid positions after Saturday qualifying
py main.py predict --race canada --grid-override "antonelli:1,russell:3,norris:2"

# Get raw JSON output (useful for scripting)
py main.py predict --race canada --json-out

# Generate prediction AND automatically create HTML report
py main.py predict --race canada --auto-report

# Save an HTML report separately
py main.py report --race canada --output ./my_canada_report.html

# Custom number of simulations
py main.py predict --race monaco --sims 10000
```

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

**Viewing reports:**
HTML reports use Chart.js from CDN, so you need an internet connection. For best results, serve them locally:
```bash
# Start a local web server
py -m http.server 8080 --directory output

# Open in browser
http://localhost:8080/canada_prediction_report.html
```

⚠️ **Important**: Don't open HTML files directly with `file://` protocol - charts may not load due to browser security restrictions.

**Grid Override Format:**
After Saturday qualifying, you know the actual starting positions. Use them for maximum accuracy:
```bash
--grid-override "driver_id:position,driver_id:position,..."
```

Example:
```bash
--grid-override "leclerc:1,russell:2,antonelli:3,norris:4,piastri:5"
```

**When to use this:**
- Predicting different circuits throughout the season
- Post-qualifying predictions with actual grid
- Generating reports for specific races

### Option 3 — REST API (For Developers)

Start a web server that other applications can query.

**Start the API server:**
```bash
py main.py api
```

By default, it runs on port 8000. You can specify a different port:
```bash
py main.py api --port 8002
```

**Access the interactive documentation:**
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

**Important**: Use `localhost` or `127.0.0.1`, NOT `0.0.0.0`. The server displays `0.0.0.0` to indicate it's listening on all interfaces, but browsers need `localhost` to connect.

**Test the API with curl:**
```bash
# Full prediction for Canadian GP
curl http://localhost:8002/api/v1/predict/canada

# Just win probabilities (faster response)
curl http://localhost:8002/api/v1/predict/canada/winner

# DNF risk per driver
curl http://localhost:8002/api/v1/predict/canada/dnf

# Wet race scenario (65% rain probability)
curl "http://localhost:8002/api/v1/predict/canada?rain_probability=0.65"

# Current driver standings
curl http://localhost:8002/api/v1/standings/drivers

# All available circuits
curl http://localhost:8002/api/v1/circuits

# Health check (is the API running?)
curl http://localhost:8002/api/v1/health
```

**Query Parameters:**
- `rain_probability` (float 0.0–1.0): Override default rain chance
- `n_simulations` (int 100–50000): Number of simulations (default 5000)
- `seed` (int): Make results reproducible (same seed = same results)

**POST endpoint for custom simulations:**
```bash
curl -X POST http://localhost:8002/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "circuit_id": "canada",
    "rain_probability": 0.5,
    "n_simulations": 5000,
    "grid_overrides": {
      "antonelli": 1,
      "russell": 2,
      "norris": 3
    }
  }'
```

**When to use this:**
- Building your own F1 app or website
- Integrating predictions into fantasy F1 tools
- Automated analysis scripts
- Mobile app backends

### Option 4 — Data Quality Checks

Before trusting predictions, verify the data is consistent.

```bash
py main.py quality-check
```

This checks:
- All 22 drivers are present and have valid data
- All 24 circuits are defined correctly
- Championship standings add up properly
- No missing ELO ratings or stats
- Driver-team assignments are consistent

**Run this:**
- After updating season data
- Before important predictions
- When troubleshooting unexpected results

---

## 📊 Understanding the Output

When you run a prediction, you get a table like this:

```
🏁 Canadian Grand Prix 2026 — Race Predictions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P   Driver              Team            Win%   Top3%  Top10%  DNF%   Confidence
─────────────────────────────────────────────────────────────────────────────
🥇  Kimi Antonelli      Mercedes        48.2   82.1   96.0    4.0    High
🥈  George Russell      Mercedes        18.1   65.3   94.0    5.0    High
🥉  Lando Norris        McLaren         12.3   52.4   88.0    6.0    Medium
4   Max Verstappen      Red Bull        8.1    38.2   80.0    9.0    Medium
5   Charles Leclerc     Ferrari         6.5    32.1   75.0    11.0   Medium
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
| **Confidence** | Model's confidence level | High/Medium/Low uncertainty |

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

**Confidence Levels**
- **High**: Clear favorite, stable conditions
- **Medium**: Competitive field, some uncertainty
- **Low**: Wet race, new circuit, major upgrades

### Reading Between the Lines

**Example Analysis:**
```
Antonelli: Win 48%, Top3 82%, DNF 4%
```

This tells us:
- He's the clear favorite (48% is very high in F1)
- He's very likely to podium (82%)
- He's very reliable (only 4% DNF risk)
- But he still loses more than half the time (52%)

**Compare two drivers:**
```
Norris:  Win 12%, Top3 52%, DNF 6%
Piastri: Win 8%,  Top3 45%, DNF 7%
```

Insights:
- Norris is favored over his teammate
- Both have similar reliability
- The gap is small — could easily go either way
- Neither is a serious win contender (both <15%)

---

## 🌐 REST API Guide

### Getting Started

**1. Start the API server:**
```bash
py main.py api --port 8002
```

**2. Open your browser:**
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

**3. Explore the endpoints interactively**

The Swagger UI lets you:
- See all available endpoints
- Test them directly in your browser
- See request/response formats
- Try different parameters

### Available Endpoints

#### Prediction Endpoints

**GET `/api/v1/predict/{circuit_id}`**
Full race prediction with all probabilities.

Parameters:
- `circuit_id` (path): Circuit identifier (e.g., "canada", "monaco")
- `rain_probability` (query, optional): 0.0 to 1.0
- `n_simulations` (query, optional): 100 to 50000
- `seed` (query, optional): Integer for reproducibility

Example:
```
http://localhost:8002/api/v1/predict/canada?rain_probability=0.6&n_simulations=10000
```

Response:
```json
{
  "circuit_id": "canada",
  "rain_probability": 0.6,
  "n_simulations": 10000,
  "predictions": [
    {
      "driver_id": "antonelli",
      "driver_name": "Kimi Antonelli",
      "team": "mercedes",
      "championship_points": 100,
      "predicted_position": 1,
      "expected_position_float": 1.45,
      "win_probability": 0.482,
      "top3_probability": 0.821,
      "top10_probability": 0.960,
      "dnf_probability": 0.040,
      "teammate_beat_prob": 0.72,
      "composite_score": 0.856,
      "features": {...},
      "position_distribution": {...}
    },
    ...
  ]
}
```

**GET `/api/v1/predict/{circuit_id}/winner`**
Win probabilities only (faster response).

Same parameters as above, but returns only win probabilities:
```json
{
  "circuit_id": "canada",
  "predictions": [
    {"driver_id": "antonelli", "win_probability": 0.482},
    {"driver_id": "russell", "win_probability": 0.181},
    ...
  ]
}
```

**GET `/api/v1/predict/{circuit_id}/dnf`**
DNF (retirement) risk per driver.

Returns DNF probabilities for all drivers.

**POST `/api/v1/simulate`**
Custom simulation with grid overrides.

Request body:
```json
{
  "circuit_id": "canada",
  "rain_probability": 0.5,
  "n_simulations": 5000,
  "grid_overrides": {
    "antonelli": 1,
    "russell": 3,
    "norris": 2
  }
}
```

#### Data Endpoints

**GET `/api/v1/standings/drivers`**
Current driver championship standings.

Response:
```json
[
  {"position": 1, "driver": "antonelli", "points": 100},
  {"position": 2, "driver": "russell", "points": 80},
  ...
]
```

**GET `/api/v1/standings/constructors`**
Current constructor championship standings.

**GET `/api/v1/circuits`**
All 24 circuits in the 2026 season.

**GET `/api/v1/circuits/{id}`**
Details for a specific circuit.

Example: `http://localhost:8002/api/v1/circuits/canada`

**GET `/api/v1/drivers`**
All 22 drivers with their profiles.

**GET `/api/v1/drivers/{id}`**
Profile for a specific driver.

Example: `http://localhost:8002/api/v1/drivers/antonelli`

**GET `/api/v1/health`**
Health check — confirms the API is running.

Response:
```json
{"status": "healthy", "version": "2.0"}
```

### Using the API in Your Own Code

**Python example:**
```python
import requests

# Get prediction for Canadian GP
response = requests.get(
    "http://localhost:8002/api/v1/predict/canada",
    params={"rain_probability": 0.6}
)

data = response.json()

# Print top 5 drivers
for pred in data["predictions"][:5]:
    print(f"{pred['driver_name']}: {pred['win_probability']*100:.1f}% win chance")
```

**JavaScript example:**
```javascript
fetch('http://localhost:8002/api/v1/predict/canada')
  .then(response => response.json())
  .then(data => {
    console.log(`${data.predictions[0].driver_name} is favored to win`);
  });
```

### API Best Practices

1. **Use appropriate simulation counts**:
   - Quick checks: 1000 simulations
   - Standard use: 5000 simulations
   - Publication quality: 20000+ simulations

2. **Cache responses**:
   - Predictions don't change unless data updates
   - Cache for the duration of a race weekend

3. **Handle errors gracefully**:
   ```python
   try:
       response = requests.get(url)
       response.raise_for_status()
       data = response.json()
   except requests.exceptions.RequestException as e:
       print(f"API error: {e}")
   ```

4. **Rate limiting**:
   - The API has no built-in rate limits
   - But be respectful — don't hammer it with thousands of requests

---

## 🗺️ Available Circuits (2026 Season)

The 2026 F1 season features **24 races** across 5 continents. Use these circuit IDs with `--race` or in API calls:

| ID | Circuit | Country | Round | Sprint? |
|----|---------|---------|-------|---------|
| `australia` | Albert Park | Australia | R1 | No |
| `china` | Shanghai International | China | R2 | ⚡ Yes |
| `japan` | Suzuka | Japan | R3 | No |
| `bahrain` | Bahrain International | Bahrain | R4 | No |
| `saudi_arabia` | Jeddah Corniche | Saudi Arabia | R5 | ⚡ Yes |
| `miami` | Miami Autodrome | USA | R6 | ⚡ Yes |
| `canada` | Gilles-Villeneuve | Canada | R7 | ⚡ Yes |
| `monaco` | Circuit de Monaco | Monaco | R8 | No |
| `spain` | Circuit de Barcelona-Catalunya | Spain | R9 | No |
| `austria` | Red Bull Ring | Austria | R10 | ⚡ Yes |
| `britain` | Silverstone | United Kingdom | R11 | ⚡ Yes |
| `hungary` | Hungaroring | Hungary | R12 | No |
| `belgium` | Spa-Francorchamps | Belgium | R13 | No |
| `netherlands` | Zandvoort | Netherlands | R14 | ⚡ Yes |
| `italy` | Monza | Italy | R15 | No |
| `madrid` | Madrid Street Circuit | Spain | R16 | No |
| `azerbaijan` | Baku City Circuit | Azerbaijan | R17 | No |
| `singapore` | Marina Bay | Singapore | R18 | ⚡ Yes |
| `usa` | Circuit of the Americas | USA | R19 | No |
| `mexico` | Autódromo Hermanos Rodríguez | Mexico | R20 | No |
| `brazil` | Interlagos | Brazil | R21 | ⚡ Yes |
| `las_vegas` | Las Vegas Strip | USA | R22 | No |
| `qatar` | Lusail International | Qatar | R23 | ⚡ Yes |
| `uae` | Yas Marina | Abu Dhabi | R24 | No |

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

Here's what every folder and file does:

```
F1MLpredictions2026/
│
├── 📄 main.py                     ← Main entry point (CLI and API)
│                                    Run this for predictions, API, reports
│
├── 📄 requirements.txt            ← Python package dependencies
│                                    Install with: pip install -r requirements.txt
│
├── 📁 config/                     ← Configuration files
│   └── settings.py                ← All tunable parameters
│                                    FEATURE_WEIGHTS, thresholds, defaults
│
├── 📁 data/                       ← All F1 data (the knowledge base)
│   ├── __init__.py                ← Makes this a Python package
│   ├── driver_data.py             ← 22 driver profiles
│   │                               Elo ratings, skills, stats, recent form
│   ├── circuit_data.py            ← 24 circuit descriptions
│   │                               Track characteristics, type, layout
│   ├── season_2026.py             ← 2026 season results & standings
│   │                               Updated after each race
│   ├── calendar_2026.py           ← Full 2026 race schedule
│   │                               Dates, sprint weekends, status
│   └── historical/                ← Archived past seasons
│       └── README.md              ← Instructions for adding historical data
│
├── 📁 engine/                     ← The prediction brain (core logic)
│   ├── __init__.py                ← Makes this a Python package
│   ├── feature_engineering.py     ← Calculates 8 signals per driver
│   │                               ELO, constructor strength, form, etc.
│   ├── probability_model.py       ← Monte Carlo simulation engine
│   │                               Runs 5,000+ simulated races
│   ├── predictor.py               ← Orchestrates the prediction pipeline
│   │                               Ties features + simulation + calibration
│   └── calibration.py             ← Platt scaling implementation
│                                   Measures and improves calibration
│
├── 📁 api/                        ← REST API layer
│   ├── __init__.py                ← Makes this a Python package
│   ├── routes.py                  ← URL endpoints and handlers
│   │                               Defines /predict, /standings, etc.
│   └── schemas.py                 ← Data validation models
│                                   Pydantic schemas for request/response
│
├── 📁 reports/                    ← Report generation
│   ├── __init__.py                ← Makes this a Python package
│   ├── html_report.py             ← Creates standalone HTML files
│   │                               Charts, tables, visualizations
│   └── templates/
│       └── report.html            ← Jinja2 template for HTML reports
│
├── 📁 scripts/                    ← Standalone utility scripts
│   ├── __init__.py                ← Makes this a Python package
│   ├── post_race_update.py        ← Add race results after each GP
│   ├── recalibrate_model.py       ← Check model accuracy & calibration
│   ├── generate_static_site.py    ← Build GitHub Pages website
│   ├── backtest_2025_season.py    ← Test model against 2025 data
│   ├── archive_season.py          ← Archive end-of-season data
│   ├── data_quality_report.py     ← Validate data consistency
│   └── ingest_f1_data.py          ← Auto-sync from F1 APIs (FastF1, Jolpica)
│
├── 📁 tests/                      ← Automated tests
│   ├── __init__.py                ← Makes this a Python package
│   ├── test_predictor.py          ← Tests prediction output correctness
│   │                               Probabilities sum to 100%, etc.
│   └── test_feature_engineering.py← Tests individual feature calculations
│                                   ELO scores, constructor strength, etc.
│
├── 📄 README.md                   ← This file (comprehensive guide)
├── 📄 RUNNING.md                  ← Quick reference for common commands
├── 📄 DEPLOYMENT.md               ← GitHub Pages deployment guide
├── 📄 SEASON_MAINTENANCE.md       ← How to update data during the season
└── 📄 analysis_results.md         ← Model performance metrics
```

### Key Files to Know

**For F1 Fans:**
- `main.py` — All-purpose CLI tool
- `data/driver_data.py` — Driver profiles (fun to read!)

**For Developers:**
- `engine/probability_model.py` — Core simulation logic
- `api/routes.py` — API endpoint definitions
- `config/settings.py` — Tunable parameters

**For Data Scientists:**
- `engine/feature_engineering.py` — Feature calculation
- `engine/calibration.py` — Platt scaling
- `tests/` — Test suite for validation

---

## 🔧 Keeping the Model Up-to-Date

F1 is dynamic — cars evolve, drivers improve, teams upgrade. Here's how to keep predictions accurate.

### After Each Race (5 Minutes)

**Step 1: Add Race Results**

Use the helper script:
```bash
py scripts/post_race_update.py \
  --round 5 \
  --circuit canada \
  --results "antonelli:1,russell:2,norris:3,piastri:4,verstappen:5,hamilton:6,bearman:7,leclerc:DNF"
```

This script:
- Calculates ELO changes for each driver
- Shows you the exact Python code to add to `data/season_2026.py`
- Displays championship standings updates

**Step 2: Update Season Data**

Copy the code from the script output and paste it into `data/season_2026.py`:
```python
{
    "round": 5,
    "circuit": "canada",
    "name": "Canadian Grand Prix",
    "date": "2026-05-24",
    "sprint": True,
    "results": [
        {"driver": "antonelli", "position": 1, "grid": 1, "points": 25, ...},
        {"driver": "russell", "position": 2, "grid": 2, "points": 18, ...},
        ...
    ],
}
```

Also update:
- `DRIVER_STANDINGS_AFTER_R5` — Updated points totals
- `CONSTRUCTOR_STANDINGS_AFTER_R5` — Team points

**Step 3: Predict Next Race**
```bash
py main.py predict --race monaco
```

### Before Each Race Weekend (2 Minutes)

**Thursday: Data Quality Check**
```bash
py main.py quality-check
```

Ensure all data is consistent before making predictions.

**Friday: Initial Prediction**
```bash
# Use weather forecast for rain probability
py main.py predict --race monaco --rain 0.35
```

Check weather forecasts (AccuWeather, Weather.com) for race day rain probability.

**Saturday After Qualifying: Grid-Adjusted Prediction**

Once you know actual starting positions:
```bash
py main.py predict --race monaco \
  --grid-override "leclerc:1,russell:2,antonelli:3,norris:4,piastri:5"
```

This is the **most accurate** prediction you can make — it uses real qualifying results.

### Every ~6 Races: Model Health Check

**Run Recalibration:**
```bash
py scripts/recalibrate_model.py
```

This shows:
- **Brier Score**: Prediction accuracy (lower is better)
- **Log-Loss**: Penalty for confident wrong predictions
- **RPS**: Ranked Probability Score (full distribution accuracy)
- **Calibration curves**: Are probabilities honest?

**If accuracy is declining:**
1. Check if FEATURE_WEIGHTS need adjustment
2. Look for teams with major upgrades (adjust constructor strength)
3. Consider if driver form has changed significantly

**Auto-update calibration:**
```bash
py scripts/recalibrate_model.py --fit-platt
```

This automatically adjusts Platt scaling parameters based on recent race outcomes.

### Automated Data Sync (Advanced)

Use the ingestion script to auto-fetch data from official F1 APIs:
```bash
py scripts/ingest_f1_data.py
```

This pulls data from:
- **Jolpica-F1 API**: Official race results, standings, calendars
- **FastF1**: Lap times, telemetry, weather data
- **OpenF1**: Real-time session data

Creates automatic backups in `data/historical/snapshots_[timestamp]/`.

---

## 📐 Model Accuracy & Calibration

### How Good Are the Predictions?

We measure accuracy using three industry-standard metrics:

#### 1. Brier Score
**What it measures**: Average squared error of probability predictions.

**Formula**: `(predicted_probability - actual_outcome)²` averaged across all predictions.

**Scale**: 0.0 (perfect) to 0.25 (random guessing for binary outcomes)

**Target**: < 0.040 for win predictions

**Example**:
- Predict 60% win probability, driver wins → Error = (0.60 - 1.0)² = 0.16
- Predict 60% win probability, driver loses → Error = (0.60 - 0.0)² = 0.36
- Lower is better!

#### 2. Log-Loss (Cross-Entropy Loss)
**What it measures**: Penalty for confident but wrong predictions.

**Why it matters**: Punishes being very confident and very wrong more than being slightly wrong.

**Scale**: 0.0 (perfect) to ~0.69 (random for binary)

**Target**: < 0.15 for win predictions

**Example**:
- Predict 90% and driver loses → Huge penalty
- Predict 55% and driver loses → Small penalty
- Encourages honest, calibrated probabilities

#### 3. RPS (Ranked Probability Score)
**What it measures**: Accuracy of the entire finishing order distribution (P1 through P22).

**Why it matters**: Not just about who wins, but the full predicted distribution.

**Scale**: 0.0 (perfect) to ~0.33 (random)

**Target**: < 0.25

### Baseline Comparisons

To understand if our model is good, compare against baselines:

| Method | Brier Score | Description |
|--------|-------------|-------------|
| **Random** | ~0.048 | Pick winner randomly |
| **Grid-only** | ~0.042 | Winner = pole sitter |
| **Championship leader** | ~0.041 | Winner = points leader |
| **Our model** | < 0.040 | Multi-factor probabilistic |
| **Perfect** | 0.000 | Impossible ideal |

### Calibration Quality

**Well-calibrated model**:
- Events predicted at 30% happen ~30% of the time
- Events predicted at 70% happen ~70% of the time
- Reliability diagram shows diagonal line

**Poorly calibrated model**:
- Says 60% but happens 45% of the time (overconfident)
- Says 40% but happens 55% of the time (underconfident)

**Platt scaling fixes this** by learning correction factors from historical data.

### Improving Accuracy

**Short-term fixes:**
1. Adjust FEATURE_WEIGHTS in `config/settings.py`
2. Update constructor strengths after major upgrades
3. Refine driver track-type fit ratings

**Long-term improvements:**
1. Add more historical seasons for better backtesting
2. Include qualifying pace data (lap time deltas)
3. Model tire degradation and pit stop strategies
4. Add practice session performance
5. Incorporate betting market odds as a feature

---

## ❓ Troubleshooting

### Common Issues

#### Problem: `ModuleNotFoundError: No module named 'fastapi'`

**Cause**: Virtual environment not activated or dependencies not installed.

**Fix**:
```bash
# Activate virtual environment
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### Problem: `KeyError: 'canada'` or `KeyError: 'antonelli'`

**Cause**: Circuit or driver not found in database.

**Fix**:
- Check spelling: Use `canada` not `Can
```

```

```

```
"# FORMULA_1_PREDICTOR_2026" 
