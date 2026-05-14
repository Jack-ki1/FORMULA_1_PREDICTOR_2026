# Historical Data Format

This directory stores pre-race prediction snapshots and post-race outcomes
for backtesting and model calibration.

## Directory Structure

```
data/historical/
├── README.md          ← This file
├── 2025/
│   ├── round_01_bahrain_predictions.json
│   ├── round_01_bahrain_outcomes.json
│   ├── round_02_jeddah_predictions.json
│   ├── round_02_jeddah_outcomes.json
│   └── ...
└── 2026/
    ├── round_01_australia_predictions.json
    ├── round_01_australia_outcomes.json
    └── ...
```

## File Formats

### `*_predictions.json`
```json
[
  {
    "round": 1,
    "driver_id": "antonelli",
    "win_prob": 0.42,
    "top3_prob": 0.78,
    "top10_prob": 0.94
  },
  ...
]
```

### `*_outcomes.json`
```json
[
  {
    "round": 1,
    "driver_id": "antonelli",
    "position": 1
  },
  {
    "round": 1,
    "driver_id": "russell",
    "position": 2
  },
  ...
]
```

## Generating Snapshots Automatically

After each race, the post_race_update.py script auto-generates outcome files:
```bash
python scripts/post_race_update.py --round 1 --circuit australia --results "antonelli:1,russell:2,..."
# Creates: data/historical/2026/round_01_australia_outcomes.json
```

For prediction snapshots (pre-race), run the predictor on Thursday and save:
```bash
python main.py predict --race australia --json-out > \
  data/historical/2026/round_01_australia_predictions.json
```

## Using for Backtesting
```python
from engine.calibration import temporal_cross_validate
# See scripts/backtest_2025_season.py for full usage
```
