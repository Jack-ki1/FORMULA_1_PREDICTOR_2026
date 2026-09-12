# F1 Prediction Platform API Contracts

## Dashboard API Endpoints

### Prediction Endpoint (`/api/predict`)
- **Method**: POST
- **Request Body**:
  ```json
  {
    "race_id": "2026-bahrain",
    "session_type": "race",
    "target": "winner",
    "drivers": ["VER", "HAM", "LEC"]
  }
  ```
- **Response Schema**:
  ```json
  {
    "predictions": [
      {"driver": "VER", "probability": 0.45, "confidence": 0.92},
      {"driver": "HAM", "probability": 0.32, "confidence": 0.87},
      {"driver": "LEC", "probability": 0.23, "confidence": 0.81}
    ],
    "data_sources": ["jolpica", "openf1"],
    "model_version": "v1.0",
    "timestamp": "2026-03-02T14:30:00Z"
  }
  ```
- **Validation Requirements**:
  - `race_id` must be a valid race identifier
  - `session_type` must be one of: "race", "qualifying", "practice"
  - `target` must be one of: "winner", "podium", "points", "q3"
  - Driver list must contain 3-20 drivers

### Analytics Settings Endpoint (`/api/analytics/settings`)
- **Method**: GET/POST
- **GET Response**:
  ```json
  {
    "simulation_count": 1000,
    "confidence_threshold": 0.85,
    "display_uncertainty": true,
    "scenario_controls": {"safety_car": true, "rain": false}
  }
  ```
- **POST Request Body**:
  ```json
  {
    "simulation_count": 2000,
    "confidence_threshold": 0.90
  }
  ```
- **Validation Requirements**:
  - `simulation_count` must be between 100 and 10000
  - `confidence_threshold` must be between 0.5 and 0.99

## External API Contracts

### Jolpica API Contract
- **Base URL**: `https://api.jolpica.f1`
- **Rate Limit**: 100 requests/minute
- **Authentication**: None (public API)
- **Data Format**: JSON with consistent MRData structure

### OpenF1 API Contract
- **Base URL**: `https://api.openf1.org`
- **Rate Limit**: 60 requests/minute
- **Authentication**: None (public API)
- **Data Format**: JSON with session_key-based identifiers

### FastF1 Integration Contract
- **Data Format**: Pandas DataFrames with standardized column names
- **Telemetry Schema**: Speed, Throttle, Brake, Gear, RPM, Distance
- **Lap Time Schema**: LapNumber, LapTime, Sector1Time, Sector2Time, Sector3Time

## Validation Requirements

1. **Input Validation**: All API endpoints must validate request parameters
2. **Output Validation**: All responses must conform to documented schemas
3. **Error Handling**: Consistent error response format across all endpoints
4. **Rate Limiting**: Enforce rate limits at the API gateway level
5. **Caching**: Implement appropriate cache headers for all endpoints

## Technical Debt

1. **Missing Schema Validation**: No Pydantic models for request/response validation
2. **Inconsistent Error Responses**: Different error formats across endpoints
3. **No Rate Limit Documentation**: Current rate limits not documented in API contracts
4. **Missing Authentication Contracts**: No specification for future authentication requirements
5. **Incomplete Scenario Controls**: Safety car and rain scenarios not fully implemented