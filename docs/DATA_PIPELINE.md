# F1 Prediction Platform Data Pipeline Documentation

## Overview

The centralized data pipeline provides a unified framework for processing, validating, and normalizing data from multiple F1 data sources. It replaces the ad-hoc processing in `session_context.py` with a structured, maintainable architecture.

## Architecture

```
Data Sources → Validation → Normalization → Provenance Tracking → Output
     ↓           ↓            ↓                ↓
Jolpica    Standings     Driver Standings   DataProvenanceTracker
OpenF1      Grid          Grid Positions   PipelineConfig
FastF1      Weather       Weather Data     PipelineUtils
```

## Key Components

### Pipeline Steps

- **Validation Steps**: Ensure data integrity before processing
- **Normalization Steps**: Convert diverse source formats into standardized structures
- **Provenance Tracking**: Record data lineage and source information

### Configuration

- **PipelineConfig**: Centralized configuration for validation levels, normalization strategies, and provenance tracking
- **PipelineUtils**: Utility functions for pipeline statistics and event logging

## Data Flow

1. **Input**: Raw data from API clients (Jolpica, OpenF1, FastF1)
2. **Validation**: DataValidator checks structure and content
3. **Normalization**: Pipeline steps convert to standard format
4. **Provenance**: DataProvenanceTracker records source and timestamp
5. **Output**: Standardized data with provenance metadata

## Validation Rules

| Data Type | Validation Level | Rules |
|-----------|----------------|-------|
| Standings | Strict | Position must be integer 1-20, points must be numeric |
| Grid | Strict | Positions must be integers 1-20 |
| Weather | Medium | Temperature values must be reasonable (0-60°C) |
| Lap Times | Medium | Lap times must be positive numbers |
| Session Results | Strict | Position must be integer 1-20 |

## Provenance Tracking

The pipeline tracks:
- **Source**: Which API provided the data
- **Cache Status**: Whether data came from cache or live request
- **Timestamp**: When data was processed
- **Error Information**: If validation failed

## Testing

Comprehensive unit tests are available in `tests/test_data_pipeline.py` covering:
- Jolpica and OpenF1 standings normalization
- Grid position validation
- Weather data normalization
- Error handling scenarios

## Technical Debt

- [ ] Add comprehensive test coverage for fallback strategies
- [ ] Implement automated performance monitoring
- [ ] Add integration tests with real API responses
- [ ] Document pipeline metrics and monitoring
- [ ] Implement pipeline health dashboard