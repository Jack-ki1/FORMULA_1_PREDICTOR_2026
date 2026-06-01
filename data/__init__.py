# F1 Prediction System

# Data quality assertions - run at import time to catch mismatches
from data.calendar_2026 import CALENDAR_2026
from data.circuit_data import CIRCUITS

_cal_rounds = {r["circuit"]: r["round"] for r in CALENDAR_2026}
for cid, circuit in CIRCUITS.items():
    if cid in _cal_rounds:
        assert circuit["round_2026"] == _cal_rounds[cid], \
            f"Round mismatch for {cid}: circuit={circuit['round_2026']}, calendar={_cal_rounds[cid]}"
