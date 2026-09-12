# F1 Predictor 2026

A comprehensive Formula 1 race prediction system for the 2026 season, featuring ML-based predictions, live data integration, and interactive dashboards.

## Features

- **ML-Powered Predictions**: Gradient boosting models with ensemble methods for race winner, podium, points, and qualifying predictions
- **Live Data Integration**: Real-time data from Jolpica, OpenF1, and FastF1 APIs
- **Interactive Dashboard**: Flask-based web interface with multiple views (Dashboard, Standings, H2H, Constructors, Analytics, Reports)
- **Tunable Model Parameters**: Adjustable chaos level, wet-weather influence, reliability factors, and strategy aggressiveness
- **Grid Position Modeling**: Real qualifying results with manual override capabilities
- **Fantasy Scoring**: Real F1 Fantasy rules implementation
- **Championship Tracking**: Driver and constructor standings with historical progression
- **Export Reports**: CSV, JSON, PDF, and shareable summary cards

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip or poetry for package management

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd FORMULA_1_PREDICTOR_2026_2027_V2
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python scripts/migrate_db.py
python scripts/seed_2026_calendar.py
```

6. Run the application:
```bash
python main.py
```

The dashboard will be available at `http://localhost:5000`

## Project Structure

```
f1_predictor_2026/
├── main.py                          # Application entry point
├── config/                          # Configuration modules
├── dashboard/                       # Flask application and templates
├── data/                            # Data sources and API clients
├── engine/                          # ML models and prediction logic
├── database/                        # Database models and migrations
├── reports/                         # Report generation
├── scripts/                         # Utility scripts
├── tests/                           # Test suite
└── cache/                           # Cached data and models
```

## Configuration

Key configuration files:

- `.env` - Environment variables and API settings
- `config/settings.py` - Application settings
- `config/feature_weights.py` - Model parameter defaults
- `config/constants.py` - Team colors, points system, target definitions

## Model Architecture

The prediction system uses an ensemble of ML models:

- **Gradient Boosting (XGBoost/LightGBM)**: Primary tabular predictor
- **Random Forest**: Secondary model for diversity
- **Logistic Regression**: Interpretable baseline
- **Elo Rating System**: Driver skill tracking
- **Monte Carlo Simulation**: Race outcome simulation
- **Grid Model**: Qualifying-to-race conversion with empirical pole-to-win weighting

## Data Sources

- **Jolpica**: Historical standings, race results, qualifying data
- **OpenF1**: Live session timing and telemetry
- **FastF1**: Lap-by-lap telemetry and practice/qualifying data
- **Hugging Face**: Historical race data archive (tracinginsights/RaceData)

## Dashboard Views

- **Dashboard**: Main prediction interface with session-specific forecasts
- **Standings**: Live driver and constructor championship standings
- **H2H Comparison**: Head-to-head driver comparisons
- **Constructors**: Team performance analysis
- **Analytics & Settings**: Model accuracy metrics and parameter tuning
- **Reports**: Export predictions in various formats

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black .
flake8 .
```

### Database Migrations

```bash
python scripts/migrate_db.py
```

## Docker Deployment

```bash
docker build -t f1-predictor-2026 .
docker run -p 5000:5000 f1-predictor-2026
```

## License

[Your License Here]

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## Support

For issues and questions, please open an issue on the repository or contact support@f1predictor.com


## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Current system architecture and technical debt
- [DATA_SOURCES.md](docs/DATA_SOURCES.md) - All data sources, their roles, and fallback strategies
- [MODEL_OVERVIEW.md](docs/MODEL_OVERVIEW.md) - Current ML models, parameters, and validation requirements
- [API_CONTRACTS.md](docs/API_CONTRACTS.md) - API contracts, endpoints, and validation requirements
- [DATA_PIPELINE.md](docs/DATA_PIPELINE.md) - Centralized data pipeline architecture and implementation
- [MODEL_VALIDATION.md](docs/MODEL_VALIDATION.md) - Model validation, probability enforcement, and drift detection
- [AI_PROVIDERS.md](docs/AI_PROVIDERS.md) - AI provider integration and fallback strategies
- [DASHBOARD_ENHANCEMENTS.md](docs/DASHBOARD_ENHANCEMENTS.md) - Dashboard enhancements and real-time visualization
- [TESTING_AND_VALIDATION.md](docs/TESTING_AND_VALIDATION.md) - Comprehensive testing framework and validation
- [SECURITY_ENHANCEMENTS.md](docs/SECURITY_ENHANCEMENTS.md) - Security enhancements and protection measures
- [MONITORING.md](docs/MONITORING.md) - Monitoring and observability system
- [PERFORMANCE_OPTIMIZATION.md](docs/PERFORMANCE_OPTIMIZATION.md) - Performance optimization measures
- [API_INTEGRATION_TESTS.md](docs/API_INTEGRATION_TESTS.md) - Comprehensive API integration tests
- [FINAL_HANDOFF.md](docs/FINAL_HANDOFF.md) - Final handoff guide and deployment documentation

## Architecture Audit Summary

The current F1 prediction platform follows a layered architecture with three primary data sources (Jolpica, OpenF1, FastF1), a session context processing layer, and a prediction engine using both ML models and Monte Carlo simulations.

A full, verified audit of this codebase — including what's actually wired
into the running app versus what exists as unused code — lives in
[`AUDIT.md`](AUDIT.md). The summary below was previously inaccurate about
several items' real status; it's corrected here.

### Key Technical Debt Items (verified status)

- **Missing API Integration Tests**: `test_api_integration.py` still does not exist. Not addressed.
- **Probability Validation Gaps**: `engine/probability_model.py::enforce_probability_sum` normalises winner probabilities to sum to 1.0 — addressed, and covered by `tests/test_predictor.py`.
- **Hardcoded Configuration**: Monte Carlo simulation count is configurable via the `simulation_count` parameter on `generate_prediction()` (see `engine/predictor.py`) — addressed.
- **Logging Deficiencies**: Most library code (`engine/`, `data/`, `database/`) uses `logging`; the Flask blueprint route handlers and CLI scripts still use `print()` — partially addressed, tracked as a nit in `AUDIT.md`.
- **Data Pipeline Limitations**: `data/pipeline.py` / `pipeline_utils.py` / `pipeline_config.py` provide a shared normalization layer — addressed.
- **Database Configuration**: Configurable via `DATABASE_URL` in `config/settings.py` — addressed, though see `AUDIT.md` M-3 for a caveat (two separate connection-pooling implementations exist).
- **AI Provider Integration**: `engine/ai_client.py` / `ai/provider.py` integrate Gemini, OpenAI, Anthropic, Groq, Mistral, Cohere, HuggingFace, and local Ollama — addressed.
- **Dashboard Enhancements**: Multi-view Flask dashboard exists — addressed.
- **Comprehensive Testing**: 12 tests exist and pass, but large parts of the codebase (most of `engine/`, all of `security/`, `data/api_client.py`, `reports/`) remain untested — partially addressed. See `AUDIT.md` T-1.
- **Security Enhancements**: `security/auth.py` and `security/middleware.py` implement real JWT auth, security headers, and input validation — **but neither module is imported by any route the running app actually registers** (`dashboard/app.py`). The only blueprints that used them (`dashboard.py`, `health.py`) are not wired into the app, and there is no login endpoint anywhere to issue a token even if they were. **Not actually addressed in the running application** — see `AUDIT.md` B-6.
- **Monitoring and Observability**: `monitoring/blueprint.py` implements a real Prometheus `/metrics` endpoint, but it is never registered by `dashboard/app.py` or `main.py`. **Not actually addressed in the running application** — see `AUDIT.md` m-3.
- **Performance Optimization**: Response caching (`cache/redis.py`) and DB connection pooling exist — addressed.
- **API Integration Tests**: Same as above — still just the 3 existing test files, no dedicated API integration suite.
- **Final Documentation and Handoff**: This section itself was the main inaccuracy found; corrected as part of the repo audit (see `AUDIT.md`).

> **Note on the sections below:** these "Phase N Implementation Summary"
> write-ups predate this audit and describe intended/aspirational state
> rather than verified fact — e.g. Phase 13 below claims "Full Coverage:
> All Jolpica, OpenF1, and FastF1 endpoints tested," but `tests/` contains
> only `test_ai_client.py`, `test_dashboard_blueprints.py`, and
> `test_predictor.py` — none of which test `jolpica_client.py`,
> `openf1_client.py`, or `fastf1_integration.py` at all. Similarly, Phase
> 11's monitoring claim is real code (`monitoring/blueprint.py`) that is
> never registered by the running app (see `AUDIT.md` m-3). Treat the
> sections below as a roadmap/wishlist, not a changelog, until each claim
> has been re-verified.

### Phase 11 Implementation Summary

Monitoring and observability has been implemented with:

- **Prometheus Metrics**: Comprehensive application, prediction, database, and AI provider metrics
- **Grafana Integration**: Ready for dashboard creation
- **Alerting System**: Email and Slack alerting configuration
- **Log Aggregation**: Centralized logging with retention policies

### Phase 12 Implementation Summary

Performance optimization has been implemented with:

- **Redis Caching**: Distributed caching layer for predictions and database queries
- **Database Optimization**: Connection pooling, query optimization, and indexing
- **Response Optimization**: Compression and cache headers for API responses
- **Cache Invalidation**: Automatic cache invalidation on data changes

### Phase 13 Implementation Summary

Comprehensive API integration tests have been implemented with:

- **Full Coverage**: All Jolpica, OpenF1, and FastF1 endpoints tested
- **Error Handling**: Comprehensive testing of all HTTP error codes
- **End-to-End Testing**: Full prediction flow testing
- **Fallback Testing**: Testing of fallback strategies when primary sources fail

### Phase 14 Implementation Summary

Final documentation and handoff has been implemented with:

- **Deployment Guide**: Step-by-step installation and configuration instructions
- **Maintenance Guide**: Database, monitoring, and security maintenance procedures
- **Future Roadmap**: Short-term, medium-term, and long-term development plans
- **Technical Debt Summary**: Comprehensive summary of remaining technical debt
- **Contact Information**: Project ownership and support contact details

### Next Steps

1. Complete Phase 14 documentation (FINAL_HANDOFF.md created above)
2. Conduct final code review and quality assurance
3. Prepare for production deployment
4. Begin post-deployment monitoring and optimization
