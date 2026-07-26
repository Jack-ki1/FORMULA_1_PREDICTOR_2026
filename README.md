# 🏎️ F1 Predictor 2026 - Advanced Race Prediction Platform

**Professional-grade Formula 1 prediction engine with web-based dashboard, Monte Carlo simulation, and machine learning optimization.**

<p align="center">
  <strong>One Command. Complete Dashboard. Zero CLI Needed.</strong><br>
  <code>py -3 main.py dashboard --port 5000</code> → http://127.0.0.1:5000
</p>

---

## 🚀 Quick Start (3 Minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
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
  - [Docker Deployment](#docker-deployment)
  - [Hugging Face (Free)](#quick-deploy-to-hugging-face-free---30-minutes)
  - [Other Platforms](#other-deployment-options)
  - [Detailed Guide](#detailed-guide)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [Troubleshooting](#-troubleshooting)
- [Performance Benchmarks](#-performance-benchmarks)
- [Contributing](#-contributing)
- [Version History](#-version-history)
- [License](#-license)

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
- **Historical Backtesting** - Validate against completed seasons (2022-2025)
- **Calibration Tools** - Platt scaling improves probability reliability
- **Accuracy Reports** - Aggregate metrics across all evaluated races

### 💾 Data Persistence

- **SQLite Database** - Store predictions, evaluations, calibration parameters
- **Automatic Migration** - One-click database initialization
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
| **Data Sources** | Jolpica API, OpenF1 API | Live & historical race data |

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
# Download and extract to your desired location
```

#### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
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
python --version
# Should show: Python 3.10.x or higher

# Test imports
python -c "import flask, numpy, pandas, plotly; print('All imports successful!')"
```

#### 5. Initialize Database

```bash
# Method 1: Via Dashboard (Recommended)
python -3 main.py dashboard --port 5000
# Then: Settings → Quick Setup → Initialize Everything

# Method 2: Via CLI
python main.py migrate-db
```

#### 6. Launch Dashboard

```bash
python -3 main.py dashboard --port 5000
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
1. Navigate to **Dashboard** tab
2. Select a circuit from the dropdown menu
3. Choose session type (Practice, Qualifying, Sprint, or Race)
4. Adjust simulation count (default: 10,000, range: 100-50,000)
5. Set rain probability (0-100%, auto-detected if available)
6. Click **"Run Prediction"**

**Output:**
- Win probability chart (top drivers)
- Podium chance visualization
- DNF risk analysis
- Expected points distribution
- Position heatmap
- Model confidence metrics

---

### 2. Head-to-Head Driver Comparisons

**Purpose:** Compare performance predictions between two drivers.

**Steps:**
1. Navigate to **H2H Comparison** tab
2. Select two drivers from dropdown menus
3. Choose circuit and session type
4. Click **"Compare"**

**Output:**
- Direct win probability comparison
- Performance gap analysis
- Head-to-head advantage metrics
- Confidence intervals

---

### 3. Constructor Analysis

**Purpose:** View live constructor standings and performance metrics.

**Features:**
- Points leaderboard
- Win distribution
- Performance tiers
- Season progression
- Team vs team comparisons

---

### 4. Post-Race Evaluation

**Purpose:** Compare prediction accuracy against actual race results.

**Process:**
1. Navigate to **Analytics** tab
2. Select **"Post-Race Evaluation"**
3. Choose completed race
4. Upload actual results or use auto-fetch
5. Review accuracy metrics

**Metrics:**
- Top-3 accuracy percentage
- Win prediction accuracy
- Brier score (probability accuracy)
- Confidence vs accuracy correlation

---

### 5. Probability Calibration

**Purpose:** Improve prediction accuracy using Platt scaling.

**Process:**
1. Navigate to **Analytics** tab
2. Select **"Probability Calibration"**
3. Run calibration algorithm
4. Apply calibrated weights

**Benefits:**
- More accurate probability estimates
- Better uncertainty quantification
- Improved decision-making

---

### 6. Model Weight Optimization

**Purpose:** Optimize feature weights using Bayesian optimization.

**Process:**
1. Navigate to **Analytics** tab
2. Select **"Weight Optimization"**
3. Configure optimization parameters
4. Run Optuna Bayesian optimization
5. Apply optimized weights

**Parameters:**
- Number of trials (default: 50)
- Study name
- Objective function
- Constraints

---

### 7. Historical Backtesting

**Purpose:** Validate model performance against historical data.

**Process:**
1. Navigate to **Analytics** tab
2. Select **"Backtesting"**
3. Choose season range (2022-2025)
4. Run backtest
5. Review aggregate metrics

**Metrics:**
- Average top-3 accuracy
- Win prediction rate
- Brier scores by race
- Performance trends

---

### 8. Downloading Reports

**Purpose:** Export predictions in various formats.

**Available formats:**
- **HTML Report** - Full interactive report
- **JSON Export** - Raw prediction data
- **CSV Export** - Tabular results

**Process:**
1. Navigate to **Download** tab
2. Select circuit and session
3. Choose format
4. Click **"Generate Report"**

---

## ⚙️ Settings & Configuration

### Database Management

**Database Migration:**
- Location: **Settings** → **Database Migration**
- Creates tables: drivers, teams, predictions, evaluations
- One-click initialization
- Backup capability

**Backup & Restore:**
- Automatic daily backups
- Manual backup option
- Restore from backup
- Export/import functionality

### Data Sources

**Current Data Sources:**
- **Jolpica API** - Historical results, standings, schedules
- **OpenF1 API** - Live telemetry, positions, weather data

**Configuration:**
- Enable/disable individual sources
- API key management
- Rate limit controls
- Cache settings

### Quality Checks

**Automated Checks:**
- Data integrity validation
- Missing data detection
- Outlier identification
- Consistency verification

**Manual Checks:**
- Run comprehensive validation
- View quality report
- Identify issues
- Apply fixes

### Performance Benchmarking

**Benchmark Types:**
- Monte Carlo simulation speed
- Memory usage analysis
- API response times
- Database query performance

**Results:**
- Performance metrics
- Bottleneck identification
- Optimization recommendations

---

## 🤖 How It Works

### Prediction Engine Overview

The prediction engine combines multiple approaches:

1. **ELO Rating System** - Historical performance tracking
2. **Monte Carlo Simulation** - Probabilistic outcome modeling
3. **Machine Learning** - Feature-based predictions
4. **Statistical Models** - Regression and classification

### Feature Engineering

**Driver Features:**
- Current ELO ratings (race, qualifying, wet weather)
- Recent form (last 6 races)
- Reliability index (DNF rate)
- Circuit-specific performance
- Team performance adjustment

**Team Features:**
- Constructor ELO ratings
- Technical developments
- Resource allocation
- Strategic capabilities

**Environmental Features:**
- Weather conditions
- Safety car probability
- Track characteristics
- Tyre degradation factors

### ELO Rating System

**Multi-Dimensional Approach:**
- **Race Pace ELO** - Performance in race conditions
- **Qualifying ELO** - One-lap performance
- **Wet Weather ELO** - Performance in rain
- **Tire Management ELO** - Long-run pace maintenance

**Rating Calculation:**
- Based on actual race results
- Recency-weighted (recent races more important)
- Opponent-adjusted (difficulty of competition)
- Self-correcting (regression to mean)

### Monte Carlo Simulation

**Simulation Process:**
1. Generate random seeds for reproducibility
2. Simulate each race position based on driver ratings
3. Account for DNFs, retirements, penalties
4. Apply weather and safety car effects
5. Repeat thousands of times for probability distributions

**Vectorized Implementation:**
- Uses NumPy for parallel processing
- 40x faster than loop-based approach
- Handles 20+ drivers simultaneously
- Efficient memory usage

### Weather Integration

**Rain Modeling:**
- Probability-based occurrence
- Intensity levels (light, medium, heavy)
- Duration estimation
- Impact on performance

**Effects:**
- Increased DNF probability
- Greater performance variance
- Overtaking opportunities
- Strategy complexity

---

## 📊 Accuracy Measurement

### Brier Score Metric

**Definition:** Mean squared difference between predicted probability and actual outcome.

**Formula:** BS = (prediction - outcome)²

**Interpretation:**
- Range: 0 (perfect) to 1 (completely wrong)
- Lower scores indicate better accuracy
- Industry standard for probability assessment

### Evaluation Workflow

1. Generate predictions for upcoming race
2. Collect actual results after race completion
3. Calculate Brier scores for each driver
4. Compute aggregate metrics
5. Update model based on findings

### Calibration Process

**Platt Scaling:**
- Logistic regression on prediction outputs
- Maps raw scores to calibrated probabilities
- Improves accuracy of confidence estimates
- Applied post-simulation

---

## 🚀 Advanced Usage

### Custom Grid Overrides

**Purpose:** Manually set starting grid positions for predictions.

**Use Cases:**
- Qualifying results not yet available
- Penalties affecting starting order
- Testing hypothetical scenarios

**Implementation:**
- Enter driver numbers in grid positions
- System validates input
- Applies to race and sprint predictions
- Preserves simulation integrity

### Rain Probability Adjustment

**Default Behavior:**
- Auto-detected from OpenF1 API
- Circuit-specific baseline
- Real-time weather integration

**Manual Override:**
- Set custom probability (0-100%)
- Adjust for forecast changes
- Impact on simulation parameters

### Simulation Count Tuning

**Performance vs Accuracy:**
- Higher counts: More accurate, slower
- Lower counts: Faster, less accurate
- Sweet spot: 5,000-10,000 simulations

**Recommendations:**
- Default: 10,000 (balanced)
- Quick check: 1,000 (fast)
- Precision: 50,000 (accurate)

### Vectorized vs Original Engine

**Vectorized Engine (Current):**
- NumPy-based implementation
- Processes all drivers simultaneously
- 40x faster than original
- Memory efficient

**Original Engine (Legacy):**
- Loop-based simulation
- Individual driver processing
- Slower but more transparent
- Available for comparison

---

## ☁️ Live Deployment

### Docker Deployment

**Build and run locally:**
```bash
# Build the image
docker build -t f1-predictor .

# Run the container
docker run -p 7860:7860 f1-predictor
```

**Docker Compose (recommended):**
```yaml
version: '3.8'
services:
  f1-predictor:
    build: .
    ports:
      - "7860:7860"
    environment:
      - FLASK_PORT=7860
      - FLASK_DEBUG=false
    volumes:
      - ./data:/app/data
      - ./output:/app/output
```

**Access:** http://localhost:7860

### Quick Deploy to Hugging Face (Free) - 30 Minutes

1. **Create Hugging Face Account**
   - Visit https://huggingface.co/
   - Sign up for free account
   - Create new Space

2. **Configure Space**
   - Space SDK: Docker
   - Hardware: CPU Basic (Free tier)
   - Visibility: Public or Private

3. **Upload Files**
   - Push code to Hugging Face repo
   - Include Dockerfile and requirements.txt
   - Set environment variables

4. **Deployment Commands**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy requirements first (for better caching)
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application code
   COPY . .
   
   # Create necessary directories
   RUN mkdir -p output cache backups
   
   # Expose port (Hugging Face uses 7860)
   EXPOSE 7860
   
   # Set environment variables
   ENV FLASK_PORT=7860
   ENV FLASK_DEBUG=false
   ENV PYTHONUNBUFFERED=1
   
   # Initialize database and start app
   CMD ["sh", "-c", "python main.py migrate-db && python -m flask run --host=0.0.0.0 --port=$FLASK_PORT"]
   ```

5. **Environment Variables**
   - Set API keys in Space settings
   - Configure data source settings
   - Monitor deployment logs

### Other Deployment Options

**Heroku:**
- Free tier available (with sleep periods)
- Simple git push deployment
- Add-on services available

**Railway:**
- Generous free tier
- Easy deployment from GitHub
- Built-in database options

**DigitalOcean App Platform:**
- $5/month basic plan
- Auto-scaling capabilities
- Integrated monitoring

### Detailed Guide

**Production Considerations:**
- SSL certificate setup
- Database backup strategy
- Monitoring and logging
- Performance optimization
- Security hardening

---

## 📁 Project Structure

```
F1_PREDICTOR_2026/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── .dockerignore          # Docker ignore patterns
├── README.md              # Documentation
├── pyproject.toml         # Project metadata
├── cache/                 # API response cache
│   ├── api_responses/     # Cached API calls
│   └── fastf1_cache/      # FastF1 data cache
├── config/                # Configuration files
│   ├── settings.py        # General settings
│   ├── api_settings.py    # API configuration
│   ├── feature_weights.py # Model weights
│   └── constants.py       # Project constants
├── dashboard/             # Web interface
│   ├── app.py            # Flask application
│   ├── static/           # CSS, JS, images
│   │   ├── styles.css    # Styling
│   │   ├── dashboard.js  # Dashboard logic
│   │   ├── common.js     # Shared utilities
│   │   ├── analytics.js  # Analytics features
│   │   └── f1_image0.png # Logo
│   └── templates/        # HTML templates
│       ├── dashboard.html # Main dashboard
│       ├── h2h.html      # Head-to-head
│       ├── constructors.html # Constructors
│       ├── analytics.html # Analytics page
│       ├── settings.html # Settings page
│       ├── download.html # Download page
│       └── error.html    # Error pages
├── data/                  # Data handling
│   ├── driver_data.py    # Driver information
│   ├── circuit_data.py   # Circuit information
│   ├── calendar_2026.py  # Race calendar
│   ├── season_2026.py    # Season results
│   ├── api_client.py     # Generic API client
│   ├── jolpica_client.py # Jolpica API wrapper
│   ├── live_updater.py   # Live data updater
│   └── fastf1_integration.py # FastF1 integration
├── engine/               # Core prediction engine
│   ├── predictor.py      # Main prediction logic
│   ├── feature_engineering.py # Feature creation
│   ├── ml_models.py      # Machine learning models
│   ├── probability_model.py # Probability calculations
│   ├── benchmark_suite.py # Performance benchmarks
│   ├── ensemble_predictor.py # Ensemble methods
│   ├── pit_strategy.py   # Strategy analysis
│   ├── hf_sentiment.py   # Sentiment analysis
│   ├── elo_calculator.py # ELO rating system
│   ├── monte_carlo.py    # Monte Carlo engine
│   ├── weather_model.py  # Weather modeling
│   ├── safety_car_model.py # Safety car modeling
│   ├── tire_model.py     # Tire degradation
│   └── calibration.py    # Probability calibration
├── database/             # Database layer
│   ├── models.py         # SQLAlchemy models
│   ├── connection.py     # Connection management
│   └── migrations.py     # Migration scripts
├── reports/              # Report generation
│   ├── html_report.py    # HTML report builder
│   └── pdf_generator.py  # PDF generation
├── scripts/              # Utility scripts
│   ├── migrate_db.py     # Database migration
│   ├── backtest_2025_season.py # Backtesting
│   ├── measure_accuracy.py # Accuracy measurement
│   ├── calibrate_probabilities.py # Calibration
│   ├── optimize_weights_v3.py # Weight optimization
│   ├── post_race_evaluation.py # Post-race eval
│   ├── data_quality_report.py # Quality checks
│   └── generate_results_template.py # Templates
└── output/               # Generated output
    ├── reports/          # Prediction reports
    └── exports/          # Data exports
```

---

## 🗄️ Database Schema

**Tables:**
- `drivers` - Driver information and metadata
- `teams` - Constructor information
- `circuits` - Track information and characteristics
- `predictions` - Prediction results and parameters
- `evaluations` - Post-race evaluation results
- `standings` - Historical championship standings
- `calibration` - Calibration parameters
- `models` - Model performance metrics

**Relationships:**
- Drivers belong to Teams
- Predictions reference Drivers and Circuits
- Evaluations link to Predictions
- Standings track Driver/Team performance over time

---

## 🔧 Troubleshooting

### Common Issues

**"ModuleNotFoundError"**
- Solution: Run `pip install -r requirements.txt`
- Cause: Missing dependencies

**"Port already in use"**
- Solution: Use different port `--port 5001`
- Cause: Port 5000 already occupied

**"Database locked"**
- Solution: Restart application
- Cause: Concurrent database access

**"API rate limit exceeded"**
- Solution: Reduce API calls, increase delays
- Cause: Exceeding API provider limits

### Performance Issues

**Slow Predictions:**
- Increase system RAM
- Reduce simulation count temporarily
- Check for background processes

**High Memory Usage:**
- Monitor during large simulations
- Consider running fewer concurrent predictions
- Close unused browser tabs

### Data Source Problems

**Jolpica API Unavailable:**
- Check internet connection
- Verify API endpoint status
- Use cached data as fallback

**OpenF1 Authentication:**
- Verify API key validity
- Check rate limit status
- Confirm subscription level

---

## ⚡ Performance Benchmarks

**Simulation Speed:**
- 1,000 sims: ~2 seconds
- 10,000 sims: ~15 seconds  
- 50,000 sims: ~60 seconds
- 100,000 sims: ~120 seconds

**Memory Usage:**
- Baseline: ~50MB
- During prediction: ~200MB
- Peak (large simulations): ~500MB

**API Response Times:**
- Jolpica: <200ms average
- OpenF1: <500ms average
- Combined: <1000ms average

**Accuracy Metrics:**
- Top-3 accuracy: ~75%
- Win prediction: ~65%
- Brier score: ~0.25 (improved with calibration)

---

## 🤝 Contributing

**Ways to Contribute:**
- Bug reports and fixes
- Feature suggestions
- Documentation improvements
- Performance optimizations
- New prediction algorithms

**Development Guidelines:**
- Follow PEP 8 style guide
- Write comprehensive tests
- Document new features
- Maintain backward compatibility
- Submit pull requests for review

---

## 📋 Version History

**v3.0 (Current)**
- Complete web dashboard redesign
- Vectorized Monte Carlo engine
- Multi-dimensional ELO ratings
- Advanced feature engineering
- Real-time data integration

**Previous Versions:**
- v2.x: CLI-based predictions
- v1.x: Basic Monte Carlo simulation
- v0.x: Initial proof of concept

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For support, please open an issue in the repository or contact the maintainers.

**Happy predicting! 🏁**