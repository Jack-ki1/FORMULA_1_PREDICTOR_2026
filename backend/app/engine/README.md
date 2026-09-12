# Engine — domain layer preserved 1:1
This directory is intentionally empty — the domain engine lives at ../../engine/ (predictor, monte_carlo, grid_model, probability_model, calibration, elo_calculator, etc.) per Phase 30 "What should NOT move initially".
Backend services (backend/app/services/*) thin-wrap engine.generate_prediction without algorithmic changes.
