# F1 Prediction Platform Data Sources

## API Integrations

### Jolpica API
- **Role**: Primary source for championship standings, race results, and qualifying data
- **Endpoints**:
  - `/f1/{season}/driverStandings.json` - Driver championship standings
  - `/f1/{season}/constructorStandings.json` - Constructor championship standings
  - `/f1/{season}/{round}/results.json` - Race results
  - `/f1/{season}/{round}/qualifying.json` - Qualifying results
  - `/f1/{season}.json` - Race schedule
- **Fallback Strategy**: Simulated data from `season_2026.py` and `team_driver_lineup_2026.py`
- **Data Provenance**: Real-time data with timestamped caching (1 hour TTL)

### OpenF1 API
- **Role**: Live session and telemetry data for real-time predictions
- **Endpoints**:
  - `/v1/sessions` - Available sessions for a meeting
  - `/v1/drivers` - Driver list for a session
  - `/v1/position` - Live position data
  - `/v1/car_data` - Car telemetry data
  - `/v1/team_radio` - Team radio messages
  - `/v1/race_control` - Race control messages
- **Fallback Strategy**: Static driver roster and empty data arrays
- **Data Provenance**: Real-time streaming data (no caching for live endpoints)

### FastF1 Integration
- **Role**: Detailed lap-by-lap telemetry and practice/qualifying data
- **Capabilities**:
  - Lap times with sector breakdowns
  - Telemetry data (speed, throttle, brake, gear, RPM)
  - Weather conditions
  - Session results
- **Fallback Strategy**: Simulated lap times based on driver strength
- **Data Provenance**: Historical data with FastF1 caching enabled

### Hugging Face Dataset
- **Role**: Optional historical race data for model training
- **Dataset**: `tracinginsights/RaceData`
- **Fallback Strategy**: Disabled by default; requires explicit enablement
- **Data Provenance**: Community-maintained historical dataset

## Configuration & Settings

### API Configuration
- Rate limiting: Jolpica (100/min), OpenF1 (60/min), FastF1 (30/min)
- Retry logic: Exponential backoff (2s, 4s, 8s) with 3 retries
- Cache TTL: Default (5m), Long (1h), Short (1m)

### Data Pipeline
- **Normalization**: Currently handled in `session_context.py` per-API basis
- **Centralized Processing**: Missing - no unified data normalization layer
- **Validation**: Basic type checking but no comprehensive data validation

## Technical Debt

1. **Missing Fallback Documentation**: Current fallback strategies are implemented but not documented
2. **Cache Inconsistency**: Different cache TTLs across APIs without unified cache management
3. **Data Provenance Gaps**: No standardized metadata tracking for data lineage
4. **API Key Management**: Hardcoded base URLs without environment-specific configuration
5. **Error Handling**: Inconsistent error response formats across API clients