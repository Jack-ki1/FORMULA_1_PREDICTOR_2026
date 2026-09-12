# F1 Prediction Platform Architecture

## Current Architecture Overview

The system follows a layered architecture with the following key components:

1. **Data Ingestion Layer**
   - Jolpica API Client: Handles championship standings, race results, and qualifying data
   - OpenF1 API Client: Provides live session and telemetry data
   - FastF1 Integration: Delivers detailed lap-by-lap telemetry for advanced analysis
   - Hugging Face Dataset: Optional historical data source

2. **Data Processing Layer**
   - `session_context.py`: Translates external F1 data into model inputs
   - Feature engineering: Driver strength adjustments based on standings
   - Grid position mapping from qualifying results

3. **Prediction Engine**
   - ML Probability Model: Base prediction engine
   - Monte Carlo Simulations: 1,000 simulations by default
   - Grid Modeling: Qualifying position predictions

4. **Presentation Layer**
   - Flask Dashboard: Web interface for predictions
   - Analytics Settings: User-configurable parameters
   - Leaderboard System: Fantasy pick tracking

## Data Flow

```
API Clients → session_context → Feature Engineering → Prediction Engine → Dashboard
       ↑            ↑                ↑                   ↑
  (Jolpica)  (Strength/Grid)  (Probability Model)  (Visualization)
       |            |                |
  (OpenF1)      (Monte Carlo)    (Grid Model)
       |
  (FastF1)
```

## Technical Debt & Known Issues

1. **Missing API Integration Tests**
   - `test_api_integration.py` does not exist
   - Critical for validating Phase 13 requirements

2. **Probability Validation Gaps**
   - No strict enforcement that winner probabilities sum to exactly 1.0
   - Current code uses renormalization but lacks validation

3. **Hardcoded Configuration**
   - Monte Carlo simulation count (1000) is hardcoded
   - Should be configurable via settings

4. **Logging Deficiencies**
   - Production code uses `print()` statements instead of structured logging
   - Missing error context in production logs

5. **Data Pipeline Limitations**
   - No centralized data normalization layer
   - Fallback strategies are implemented per-client rather than system-wide

## Next Steps for Phase 1

- Complete documentation of all data sources
- Document model parameters and validation requirements
- Formalize API contracts for all endpoints
- Identify deprecated components for Phase 5 replacement