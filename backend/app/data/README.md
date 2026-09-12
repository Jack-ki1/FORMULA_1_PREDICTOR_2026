# Data layer preserved
Real data clients at ../../data/ (calendar_2026, jolpica_client, openf1_client, fastf1_integration, live_updater).
Services use RaceService, StandingsService which delegate to those clients with Redis cache keys (races:2026 etc.).
