# F1 Prediction Platform Model Overview

## Current Models

### Probability Model (`engine/probability_model.py`)
- **Type**: Ensemble of heuristic and ML-based probability shaping
- **Input Features**:
  - Driver championship standings
  - Qualifying grid positions
  - Circuit characteristics (overtaking rating, DRS zones)
  - Driver wet skill and reliability metrics
- **Output**: Probability distribution for driver outcomes (winner, podium, points)
- **Validation Requirements**:
  - Winner probabilities must sum to exactly 1.0
  - Podium probabilities must be mathematically consistent with winner probabilities
  - All probabilities must be in range [0.0, 1.0]

### Monte Carlo Simulation (`engine/monte_carlo.py`)
- **Type**: Stochastic simulation engine
- **Configuration**:
  - Default simulations: 1000 (hardcoded)
  - Simulation count range: Not configurable
- **Input**: Probability model outputs and circuit data
- **Output**: Distribution of possible race outcomes
- **Validation Requirements**:
  - Simulation results must be statistically significant
  - Confidence intervals must be calculated and reported
  - Edge cases (DNF, safety car deployments) must be modeled

### Grid Modeling (`engine/grid_model.py`)
- **Type**: Qualifying position prediction model
- **Input Features**:
  - Driver strength metrics
  - Circuit characteristics
  - Recent qualifying performance
- **Output**: Predicted grid positions for qualifying sessions
- **Validation Requirements**:
  - Grid predictions must be integer positions 1-20
  - Must handle driver substitutions and team changes
  - Must be consistent with race predictions

## Model Configuration

### Current Settings
- `MONTE_CARLO_SIMULATIONS`: 1000 (in `config/settings.py`)
- `DEFAULT_MODEL_VERSION`: 'v1.0' (in `config/settings.py`)
- `ENABLE_ENSEMBLE`: True (in `config/settings.py`)

### Required Enhancements (Phase 2)
- Add `SIMULATION_MIN_COUNT` and `SIMULATION_MAX_COUNT` to settings
- Implement model versioning with automatic fallback
- Add configuration for AI provider selection (OpenAI, Anthropic, etc.)
- Add request validation for all model inputs

## Technical Debt

1. **Probability Sum Enforcement**: Current code uses renormalization but lacks strict validation
2. **Hardcoded Simulation Count**: Should be configurable per-session type
3. **Missing Model Versioning**: No mechanism to track model versions in database
4. **Inconsistent Input Validation**: Different validation logic across models
5. **No Confidence Intervals**: Monte Carlo results lack statistical confidence reporting