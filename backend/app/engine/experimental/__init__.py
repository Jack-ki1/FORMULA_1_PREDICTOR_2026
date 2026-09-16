"""
EXPERIMENTAL — not wired into the production prediction path.

Nothing in this folder is imported by `backend/app/engine/predictor.py` or by
`backend/app/prediction/orchestrator.py`. It is kept because the implementation
is reasonable and may be wired in later, but it is segregated so that the
question "is this live?" is answered by the folder name rather than by a grep
someone has to remember to run.

Context (modify.md section 3): `safety_car_model.py` has zero references
anywhere in the repository — no production import, no training import, no test.
It previously sat alongside `monte_carlo.py` and `probability_model.py` — modules
that genuinely drive every prediction — with no way to tell the two apart.

Note: `ensemble_predictor.py` was a candidate for this folder, but it is NOT
dead — `training/pipelines/train.py` imports it to fit OOF ensemble weights. It
is therefore training-only, not unused, and stays in `engine/`.

To promote something out of here:
  1. Import it from the real pipeline (predictor/orchestrator).
  2. Add a test that asserts its effect on output.
  3. Move the file back up and delete this note's entry.
"""
