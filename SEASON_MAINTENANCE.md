# Season Maintenance Guide
## Keeping the F1 Prediction System Relevant — 2026 and Beyond

This document explains exactly what to update, when, and how — so the model
stays accurate throughout the season and can be cleanly extended into 2027+.

---

## The Maintenance Cycle

```
BEFORE EACH RACE WEEKEND          DURING WEEKEND          AFTER RACE
────────────────────────────      ──────────────────────  ─────────────────────
□ Verify circuit is in DB         □ Run final prediction  □ Add race results
□ Check driver lineup changes     □ Note weather update   □ Update ELO ratings
□ Apply any car upgrade flags     □ (no model changes)    □ Save historical snapshot
□ Update qualifying data (Sat)                            □ Re-run next-race preview
□ Run final pre-race prediction
```

---

## 1 — After Every Race: Add Results to `data/season_2026.py`

Open `data/season_2026.py` and append a new entry to `SEASON_RESULTS_2026`:

```python
{
    "round": 5,
    "circuit": "canada",
    "name": "Canadian Grand Prix",
    "date": "2026-05-24",
    "sprint": True,
    "results": [
        {"driver": "antonelli", "position": 1, "grid": 1, "points": 25, "dnf": False, "fastest_lap": True},
        {"driver": "russell",   "position": 2, "grid": 2, "points": 18, "dnf": False, "fastest_lap": False},
        # ... all drivers
        {"driver": "leclerc",   "position": None, "grid": 3, "points": 0, "dnf": True, "fastest_lap": False,
         "note": "DNF — Wall of Champions"},
    ],
},
```

Then update `DRIVER_STANDINGS_AFTER_R4` → rename to `DRIVER_STANDINGS_AFTER_R5` and
update every driver's points total. Similarly update `CONSTRUCTOR_STANDINGS_AFTER_R4`.

> **Shortcut:** use the post-race update script:
> ```bash
> python scripts/post_race_update.py --round 5 --circuit canada \
>   --results "antonelli:1,russell:2,norris:3"
> ```

---

## 2 — Update Driver ELO Ratings

ELO should be recalculated after each race based on finishing order vs. expected order.

In `data/driver_data.py`, update the `"elo"` field for each driver.

**Formula used:**

```
expected_score  = 1 / (1 + 10^((opponent_elo - driver_elo) / 400))
actual_score    = 1 if beat opponent else 0
new_elo         = old_elo + K * (actual_score - expected_score)
K = 32 (configurable in config/settings.py)
```

The post-race script computes this automatically:
```bash
python scripts/post_race_update.py --round 5 --update-elo
```

---

## 3 — Update Recent Form Scores

`driver["recent_form"]` is a list of finishing positions, most recent first.
After each race, **prepend** the new result and **drop the oldest** if the list
exceeds `RECENCY_WINDOW` (default 8):

```python
# Before Canada (R5):
"recent_form": [1, 1, 1, 2]    # Miami, Japan, China, Australia

# After Canada (assuming P1):
"recent_form": [1, 1, 1, 1, 2] # Canada, Miami, Japan, China, Australia
```

---

## 4 — Mid-Season Driver/Team Changes

### Driver substitution (injury, replacement, etc.)
1. Mark the original driver as inactive (add `"active": False`)
2. Add the replacement driver entry to `data/driver_data.py`
3. Set replacement's `experience_races` and `elo` appropriately
4. Add team-mate notes

### Car upgrades
When a team announces a confirmed upgrade package:
1. Increase their `_CONSTRUCTOR_STRENGTH` value in `engine/feature_engineering.py`
2. Add a note with the round number

```python
_CONSTRUCTOR_STRENGTH: dict = {
    "mercedes": 0.96,
    "mclaren":  0.85,  # ← Updated after R6 upgrade package (Monaco)
    ...
}
```

### Power unit changes / grid penalties
These are handled per-race via grid position overrides in the prediction CLI:
```bash
# Verstappen takes 5-place grid penalty → start P8 instead of P3
python main.py predict --race monaco --grid-override "verstappen:8"
```

---

## 5 — Add New Circuits Each Round

For each upcoming race, add a circuit entry to `data/circuit_data.py`:

```python
"silverstone": {
    "id": "silverstone",
    "name": "Silverstone Circuit",
    "city": "Silverstone",
    "country": "United Kingdom",
    "round_2026": 10,
    "race_date": "2026-07-06",
    "sprint_weekend": False,
    "circuit_type": ["balanced"],
    "lap_count": 52,
    "lap_distance_km": 5.891,
    "total_distance_km": 306.198,
    "safety_car_probability": 0.52,
    "overtaking_difficulty": 5,
    "power_unit_demand": 7.5,
    "brake_demand": 7.0,
    "tire_deg_rate": 8.5,
    "active_aero_demand": 7.5,
    "rain_probability_typical": 0.45,
    "wall_crash_probability_per_lap": 0.002,
    "drs_zones": 2,
    "team_historical_wins_since_2010": {
        "mercedes": 11, "red_bull": 5, "ferrari": 2, "mclaren": 3
    },
}
```

> **Tip:** Copy the closest circuit type as a template and adjust values.
> The 2026 full calendar is in `data/calendar_2026.py`.

---

## 6 — Quarterly Model Recalibration

Every ~6 races, run the calibration check:

```bash
python scripts/recalibrate_model.py
```

This will:
- Compare predicted probabilities vs. actual outcomes for all completed races
- Output Brier scores, log-loss, and calibration curve data
- Suggest updated Platt scaling parameters
- Recommend feature weight adjustments

Apply the suggested changes to:
- `config/settings.py` → `FEATURE_WEIGHTS`
- `engine/probability_model.py` → `PLATT_A_WIN`, `PLATT_B_WIN`

---

## 7 — End of Season: Archive and Prepare for 2027

### Step 1 — Archive 2026 data
```bash
python scripts/archive_season.py --season 2026
# Creates data/historical/2026/ with all race snapshots
```

### Step 2 — Create 2027 season files
```bash
cp data/season_2026.py data/season_2027.py
# Empty the SEASON_RESULTS and reset standings to 0
```

### Step 3 — Update driver roster
For 2027, typical changes to handle:
- Driver seat changes (announced ~September of current year)
- New rookie entries
- Retirement declarations
- Team name changes

Update `data/driver_data.py`:
```python
# Mark retired drivers
"hamilton": {
    ...
    "active_2027": False,  # Add this flag
}

# Add new drivers
"new_rookie": {
    "id": "new_rookie",
    "name": "New Rookie",
    "elo": 1480,           # Start at below-average ELO
    "experience_races": 0,
    # ... fill in profile from F2/junior data
}
```

### Step 4 — Reset ELO with decay
Apply a 10% decay toward the mean (1500) to prevent over-anchoring:
```bash
python scripts/reset_elo_new_season.py --decay 0.10
```

### Step 5 — Refit calibration on full 2026 data
```bash
python scripts/recalibrate_model.py --season 2026 --fit-platt
# Updates PLATT_A_WIN, PLATT_B_WIN, PLATT_A_TOP3 in probability_model.py
```

---

## 8 — Data Sources to Monitor

| Source | What to watch | Update frequency |
|--------|--------------|------------------|
| Formula1.com | Official results, grid penalties | After each session |
| Ergast API | Machine-readable results (free) | ~2hrs after race |
| Autosport / RaceFans | Upgrade confirmations | Weekly |
| FIA documents | Post-race steward decisions | Race weekend |
| Team social media | Driver changes, car livery updates | As announced |
| AccuWeather / Meteoblue | Pre-race weather forecasts | Thursday–Sunday |

### Ergast API integration (optional but powerful)

Set `ERGAST_API_BASE` in `.env` and run:
```bash
python scripts/sync_from_ergast.py --round 5
# Auto-populates results from the official API after each race
```

---

## 9 — Feature Tuning Cheatsheet

| Signal weakening? | Action |
|-------------------|--------|
| Grid position not predicting well | Reduce `grid_position` weight, increase `recent_form` |
| Rookie form underestimated | Increase `elo_rating` weight for drivers with <10 races |
| Safety car races breaking predictions | Increase `safety_car_upside` weight |
| Wet races unpredictable | Increase `weather_adjustment` weight, raise `wet_skill` precision |
| DNF rates outdated | Update `dnf_rate_recent` from last 6 races |

---

## 10 — Season Timeline Checklist

```
March     □ Season launch — verify all 20 drivers + 24 circuits loaded
          □ Reset ELO from 2025 final values
          □ Set constructor strength baselines

April–May □ After R1-R4: validate model calibration, adjust if Brier > 0.06
          □ Mid-season upgrade tracker active

June–Aug  □ Quarterly recalibration run
          □ Summer break: prepare remaining calendar circuits

Sept–Oct  □ Final standings verification
          □ Archive season data
          □ Begin 2027 roster updates

November  □ End-of-season ELO decay
          □ Refit Platt scaling on full season
          □ Update README with 2027 instructions
```
