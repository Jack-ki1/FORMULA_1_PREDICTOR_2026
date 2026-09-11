# AUDIT.md — F1 Predictor 2026/2027 (`FORMULA_1_PREDICTOR_2026_2027_V2`)

Audit performed by reading the source tree, then **actually installing the
project and running it** (clean venv, `pip install -r requirements.txt`,
booting the Flask app, hitting the prediction API, running the test suite,
and import-testing every module) to turn suspected issues into confirmed
ones wherever possible. Findings marked **[VERIFIED]** were reproduced live
in this session; findings marked **[STATIC]** are high-confidence from
reading the code but were not executed.

---

## Phase 1 — Repo map

Non-source directories/files skipped per instructions: `.git/`,
`__pycache__/` (23 compiled artifacts — see Blocker/Nit table, they
shouldn't be committed at all), `cache/fastf1_cache/**` (binary FastF1
session cache + sqlite http cache), `cache/api_responses/*.json` (2 stale
API response snapshots), `f1_predictions.db` / `f1_predictor.db` (binary
sqlite files — also flagged below, they shouldn't be committed either).

```
FORMULA_1_PREDICTOR_2026_2027_V2/
├── app.py                          Second, competing Flask entry point. Registers dashboard_bp/health_bp
│                                    that dashboard/app.py deliberately does NOT register. Not used by
│                                    Dockerfile/README/main.py — orphaned duplicate. See M-1, B-6.
├── main.py                         Real entry point (matches README/AGENTS.md/Dockerfile). Boots DB
│                                    migration, live updater, then dashboard.app.create_app().
├── improve.md / IMPROVEMENTS.md    Byte-identical roadmap docs — duplicate file. See M-2.
├── AGENTS.md, README.md            Project docs. Both reference test files and a BUILD_PLAN.md that
│                                    don't exist in the repo. See D-1.
├── Dockerfile                      Builds from requirements.txt, runs `python main.py`. Build is
│                                    currently broken — see B-1.
├── requirements.txt / pyproject.toml   Two divergent, inconsistent dependency lists. See B-1, B-2, M-4.
├── .env.example                    Template env vars; DEFAULT DEBUG differs from code default. See m-1.
├── .dockerignore                   Fine, but repo has no top-level .gitignore — see M-6.
│
├── config/
│   ├── settings.py                 Pydantic Settings (needs `pydantic-settings`, never declared). B-2.
│   ├── api_settings.py             Base URLs/retry/rate-limit constants for Jolpica/OpenF1/FastF1.
│   ├── constants.py                 Team colors, points systems, target metadata, grid-position prior.
│   ├── feature_weights.py          Chaos/wet/reliability/strategy/grid tunables read from env.
│   └── team_driver_lineup_2026.py  Single source of truth for 11 teams / 22 drivers.
│
├── data/
│   ├── api_client.py               Generic HTTP client w/ disk cache + retry/backoff. Cache READ path
│   │                                has an uncaught NameError — see B-3 (root cause, affects clients below).
│   ├── jolpica_client.py / openf1_client.py   Subclass APIClient — inherit B-3.
│   ├── fastf1_integration.py, huggingface_dataset.py, live_updater.py, pipeline*.py,
│   │   validation.py, provenance.py, session_context.py, fallback.py   Data sourcing/pipeline helpers.
│   ├── calendar_2026.py, circuit_data.py, driver_data.py, team_data.py, season_2026.py
│   │                                Static/derived 2026 season reference data consumed by config + engine.
│   └── constructors.json, drivers.json                                  Static JSON fixtures.
│
├── database/
│   ├── models.py                   SQLAlchemy declarative models (teams/drivers/races/predictions/etc,
│   │                                one shared `Base` — also imported into by models/prediction.py).
│   ├── connection.py                Separate engine/session factory + seeding helpers (`DatabaseConnection`).
│   │                                Duplicates database/client.py's responsibility — see M-3.
│   ├── client.py                   Separate engine/session factory + stats/cache (`DatabaseClient`), used
│   │                                by the live prediction path. Duplicates connection.py — see M-3.
│   └── init.py                     Runs the raw-SQL migration at boot. `verify_database_connection()` has
│                                    a confirmed SQLAlchemy 2.0 raw-string-execute bug — see B-4.
│
├── migrations/
│   ├── _001_initial_schema.py      The migration actually imported/used by database/init.py. Correct.
│   └── 001_initial_schema.py       Dead, broken duplicate (no leading underscore) — never imported anywhere,
│                                    uses removed `engine.execute()` and invalid inline MySQL INDEX syntax
│                                    inside a SQLite CREATE TABLE. See M-5.
│
├── models/prediction.py            Prediction/SessionData/PredictionMetadata/DatabaseMigration ORM models,
│                                    sharing database/models.py's Base (good — not a duplicate registry).
│
├── engine/
│   ├── predictor.py                 Main orchestrator: grid → Monte Carlo → optional AI blend → chaos
│   │                                 smoothing → calibration → persistence. Verified working end-to-end.
│   ├── monte_carlo.py               Vectorised numpy race simulator. Reviewed in depth — no issues found.
│   ├── grid_model.py, elo_calculator.py, tire_model.py, weather_model.py, safety_car_model.py,
│   │   pit_strategy.py, fantasy_scoring.py, benchmark_suite.py                 Sampled — no blockers found.
│   ├── ml_models.py, calibration.py, ensemble_predictor.py    Import scikit-learn directly at module
│   │                                 level; scikit-learn is not in requirements.txt — see B-5.
│   ├── probability_model.py         Calibration/confidence/drift helpers used by predictor.py.
│   └── ai_client.py                 Multi-provider (Gemini/OpenAI/Anthropic/Groq/Mistral/Cohere) LLM
│                                     caller, used for optional prediction "AI boost" and chat.
│
├── ai/
│   ├── provider.py                  HuggingFace/OpenAI/Ollama provider manager + multi-agent entry point.
│   ├── config.py                    AI provider config.
│   ├── local/ollama_provider.py     Talks to a local Ollama server via the `openai` package (not declared
│   │                                 as a dependency anywhere) — see B-2.
│   ├── agents/chief_strategist.py   "Chief strategist" agent; imports engine.tire_model, creating a
│   │                                 latent ai↔engine circular import — see m-2.
│   └── rag/telemetry_rag.py         Simple retrieval helper over telemetry text.
│
├── security/
│   ├── auth.py                      JWT issuing/verification + require_auth/require_role decorators.
│   │                                 There is no login/token-issuing route anywhere — see B-6.
│   └── middleware.py                Security headers, naive in-memory rate limiter, input validation.
│
├── dashboard/
│   ├── app.py                       Real Flask app factory (used by main.py). Registers landing/
│   │                                 predictions/standings/h2h/constructors/analytics_settings/reports.
│   │                                 Does NOT register dashboard_bp or health_bp (see blueprints below).
│   ├── blueprints/dashboard.py       Defines dashboard_bp with @require_auth on every route incl. `/`.
│   │                                 Never registered by dashboard/app.py — dead code, but IS registered
│   │                                 by the orphaned root app.py, where it's unreachable (no login route)
│   │                                 and also references a missing error.html template. See B-6, M-1.
│   ├── blueprints/health.py          health_bp; also never registered by dashboard/app.py. Has its own
│   │                                 bug (`import datetime` then `datetime.utcnow()`) — see B-4.
│   ├── blueprints/landing.py, predictions.py, standings.py, h2h.py, constructors.py,
│   │   analytics_settings.py, reports.py    The 7 blueprints actually wired up. Reviewed — reports.py's
│   │                                 export path silently degrades (PDF→HTML, XLSX→CSV) — see B-5.
│   ├── static/{css,js,img,videos}/  Front-end assets (not exhaustively reviewed — see recommendations).
│   └── templates/*.html             homepage/dashboard/standings/h2h/constructors/analytics_settings —
│                                     all present and match the registered blueprints.
│
├── reports/
│   ├── csv_excel_report.py          CSV works standalone; Excel silently falls back to CSV bytes
│   │                                 mislabeled as .xlsx if openpyxl isn't installed (it isn't, by
│   │                                 default) — see B-5.
│   ├── pdf_generator.py             Falls back to raw HTML bytes served with a `application/pdf`
│   │                                 mimetype if weasyprint isn't installed (it isn't, by default) — B-5.
│   └── share_card_generator.py      Text/HTML/Markdown share card — no issues found.
│
├── monitoring/blueprint.py, metrics.py   Prometheus `/metrics` endpoint. Never registered by
│                                    dashboard/app.py or main.py — dead code; also needs
│                                    `prometheus_client`, undeclared — see m-3.
├── cache/redis.py                   Redis-backed cache with a DictCache in-memory fallback — solid.
│
├── scripts/                         migrate_db.py, seed_2026_calendar.py, measure_accuracy.py,
│                                     calibrate_probabilities.py, optimize_weights.py,
│                                     post_race_evaluation.py, data_quality_report.py,
│                                     generate_results_template.py — reviewed at a sampling level;
│                                     calibrate_probabilities.py inherits the scikit-learn gap (B-5).
│
└── tests/                           test_ai_client.py, test_dashboard_blueprints.py, test_predictor.py —
                                      12 tests, all pass once the missing deps (B-2) are installed. Good
                                      quality, but leave large parts of the codebase untested — see T-1.
```

---

## Phase 3 — Findings

Severity key: **Blocker** = breaks install/boot/a whole advertised feature ·
**Major** = wrong behavior, silent data loss, real security gap ·
**Minor** = works but wrong/confusing/fragile · **Nit** = cosmetic/hygiene.

### Blockers

| # | File/Location | Category | Description | Proposed fix |
|---|---|---|---|---|
| B-1 | `requirements.txt:24` | Dependency | `sqlite3>=3.35.0` is listed as a pip package. sqlite3 is a Python **stdlib** module, not a PyPI package. **[VERIFIED]** `pip install -r requirements.txt` fails immediately with `No matching distribution found for sqlite3`. This also breaks the Dockerfile build (`RUN pip install -r requirements.txt`), i.e. the container image cannot be built at all. | Delete the line. |
| B-2 | `requirements.txt`, `pyproject.toml` | Dependency | Five packages the code imports unconditionally are never declared in `requirements.txt` (the path README tells users to use): `pydantic-settings` (`config/settings.py`, needed by nearly everything), `Flask-CORS` (`dashboard/app.py`), `openai` (`ai/local/ollama_provider.py`), `scikit-learn` (`engine/ml_models.py`, `engine/calibration.py`, `engine/ensemble_predictor.py`, `scripts/calibrate_probabilities.py` — also missing from `pyproject.toml`'s main deps despite `xgboost`/`lightgbm` being advertised in the README), and `redis`/`prometheus_client` for the code paths that use them. **[VERIFIED]** — a clean venv following the README instructions cannot even `import config.settings`, and following that, the whole `create_app()` call chain fails at `from flask_cors import CORS` and then `from openai import OpenAI` until all 3 core ones are installed by hand. | Add `pydantic-settings`, `Flask-CORS`, `openai`, `scikit-learn`, `xgboost`, `lightgbm` to `requirements.txt` (and reconcile with `pyproject.toml`, see M-4). Add `redis` and `prometheus_client` too, or make those imports lazy/optional-guarded like `cache/redis.py` already does for the `redis` client object. |
| B-3 | `data/api_client.py:58` | Correctness bug | `_get_cached_response()` calls `datetime.fromisoformat(...)`, but the module only imports `import datetime as dt` and `from datetime import timedelta` — the bare name `datetime` is never bound. **[VERIFIED]** live: reading any existing cache file raises `NameError: name 'datetime' is not defined`, and this is **not** one of the exception types caught by the surrounding `except (json.JSONDecodeError, KeyError, ValueError):`, so it propagates uncaught. This is the base class for `JolpicaClient` and `OpenF1Client`, so any cached GET response from either live-data source crashes instead of being served from cache. The repo even ships two pre-populated files under `cache/api_responses/*.json` that will trigger this the moment they're read. | Change the call to `dt.datetime.fromisoformat(...)` (consistent with the rest of the module), and add `NameError`/general `Exception` to the caught types as defense in depth. |
| B-4 | `database/init.py:27`, `dashboard/blueprints/health.py:53` | Correctness bug | (a) `verify_database_connection()` calls `conn.execute("SELECT COUNT(*) ...")` with a bare string. SQLAlchemy 2.0 requires `text(...)`. **[VERIFIED]**: raises `Not an executable object`. (b) `health.py` does `import datetime` then calls `datetime.utcnow()` — that's a module, not the `datetime.datetime` class. **[VERIFIED]**: raises `AttributeError: module 'datetime' has no attribute 'utcnow'`. Also present in the dead `dashboard/blueprints/dashboard.py` (`db.execute("SELECT COUNT(*) FROM predictions ...")`, same bare-string problem) — see M-1. | Wrap the raw SQL in `sqlalchemy.text(...)`; fix the `health.py` import to `from datetime import datetime, timezone` and use `datetime.now(timezone.utc)` (`utcnow()` is also deprecated in 3.12+). |
| B-5 | `reports/pdf_generator.py`, `reports/csv_excel_report.py`, `engine/ml_models.py` + friends | Missing dependency / silent feature degradation | `weasyprint` and `openpyxl` are only listed in `pyproject.toml`'s *optional* `[reports]` extra, never in `requirements.txt`. **[VERIFIED]** neither is importable after following the documented setup. The effect is silent, not a crash: `PDFGenerator.generate_pdf()` catches the `ImportError` and returns raw HTML bytes, which `dashboard/blueprints/reports.py` then serves with `mimetype='application/pdf'` — the downloaded "PDF" is actually an HTML file that most PDF viewers will refuse to open. Likewise `generate_excel()` silently returns CSV bytes for a file the API labels `.xlsx`. Separately, `scikit-learn`/`xgboost`/`lightgbm` (advertised in the README as "Gradient Boosting (XGBoost/LightGBM)... Random Forest... Logistic Regression") are absent from `requirements.txt`, so `engine/ml_models.py`, `engine/calibration.py`, `engine/ensemble_predictor.py`, and `scripts/calibrate_probabilities.py` all fail with `ModuleNotFoundError` on the documented install path. | Add `weasyprint`, `openpyxl`, `scikit-learn`, `xgboost`, `lightgbm` to `requirements.txt`. Until then, at minimum make the PDF/Excel fallbacks return a correct `Content-Type` for what they actually produced, or return a clear 501 error instead of silently mislabeling the file. |
| B-6 | `app.py` (root), `security/auth.py` | Dead/broken code + auth design gap | The root `app.py` is a second, independent Flask entry point that registers `dashboard_bp` and `health_bp` — both of which put `@require_auth` on every route, including `/`. There is **no route anywhere in the codebase that calls `generate_jwt_token()`** — no login, registration, or token-issuing endpoint exists. If this file were ever run (it isn't referenced by `main.py`, `Dockerfile`, or the README, so today it's orphaned dead code, see M-1), every route it registers would return `401` for every request, permanently. | Fixed by deleting the dead file (see M-1) rather than wiring up a real auth flow, since adding real login is a product decision outside the scope of this cleanup — flagged for the maintainer rather than guessed at. |

### Majors

| # | File/Location | Category | Description | Proposed fix |
|---|---|---|---|---|
| M-1 | `app.py` (root) vs `dashboard/app.py` + `main.py` | Duplication / dead code | Two competing "main app" definitions exist. `main.py` (the one Docker/README/tests actually use) builds its Flask app from `dashboard/app.py::create_app()`, which registers 7 blueprints and deliberately *excludes* `dashboard_bp`/`health_bp` (there's already an inline comment in `dashboard/app.py` documenting an earlier fix for this exact confusion). The root `app.py` is an older/alternate version that *does* register those two blueprints, each broken in its own way (B-4, B-6) and also referencing a nonexistent `error.html` template. It is never imported by anything else in the repo. | **Deleted** `app.py` from the repo root (Phase 4). Its unique routes (`/ping`, JWT config on `app.config`) added nothing that `dashboard/app.py`'s `/health` doesn't already cover. |
| M-2 | `improve.md`, `IMPROVEMENTS.md` | Duplication | Byte-for-byte identical files (confirmed via `diff`, zero output). | **Merged** (Phase 5): kept `IMPROVEMENTS.md` (matches the naming convention of `README.md`/`AGENTS.md`), deleted `improve.md`. |
| M-3 | `database/connection.py` (`DatabaseConnection`/`db`) vs `database/client.py` (`DatabaseClient`) | Duplication / architecture | Two independent classes each build their own SQLAlchemy `engine` + `sessionmaker`/`scoped_session`, each with their own `get_session()`/`session_scope()`. `connection.py`'s `db` singleton is used by the one-off seeding scripts (`scripts/migrate_db.py`, `scripts/seed_2026_calendar.py`); `client.py`'s `DatabaseClient` is used by the live request path (`engine/predictor.py`, the dead `dashboard/blueprints/{dashboard,health}.py`). Nothing forces these two connection pools to agree, and a future change to pool settings has to be made twice. | Flagged rather than merged outright — collapsing two independently-tested connection layers into one touches every DB call site in the app and is exactly the kind of change the brief calls out as "costly if wrong." Documented here with a concrete recommendation for the maintainer: keep `database/client.DatabaseClient` (it's the one already exercised by the live code path and has caching baked in) and have the scripts use it too, retiring `database/connection.py`. |
| M-4 | `requirements.txt` vs `pyproject.toml` | Inconsistency | The two dependency manifests disagree substantially: `pyproject.toml` has `Flask-CORS`, `scikit-learn`, `xgboost`, `lightgbm`, `pydantic`-adjacent packages that `requirements.txt` lacks; `requirements.txt` has `Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-Login`, `Flask-WTF`, `alembic`, `psycopg2-binary`, `seaborn`, `matplotlib` that nothing in the codebase imports (dead/aspirational deps) and that `pyproject.toml` lacks. `Werkzeug` is listed twice in `requirements.txt` (lines 15 and 20). | Fixed `requirements.txt` (Phase 4): removed the bad `sqlite3` line, de-duplicated `Werkzeug`, added the 6 missing-but-actually-used packages from B-2/B-5, and removed the packages nothing imports (`Flask-Migrate`, `Flask-Login`, `Flask-WTF`, `alembic`, `psycopg2-binary`, `seaborn`, `matplotlib`, `Flask-SQLAlchemy` — the app uses raw SQLAlchemy, not the Flask extension). Left `pyproject.toml` as a documented follow-up (see final summary) rather than rewriting both in the same pass. |
| M-5 | `migrations/001_initial_schema.py` | Dead code / duplication | Not imported anywhere (`database/init.py` imports `migrations._001_initial_schema`, the underscore-prefixed sibling). It is also independently broken: it calls the removed-in-SQLAlchemy-2.0 `engine.execute(...)` directly instead of via a connection, and embeds MySQL-only inline `INDEX idx_race_session (...)` syntax inside a `CREATE TABLE` statement that SQLite cannot parse. Confirmed no other file references `001_initial_schema` (`grep -r` across the repo). | **Deleted** (Phase 4/5) — the underscore-prefixed file is the real, working migration. |
| M-6 | (repo root) | Hygiene / repo hosting mistake | No `.gitignore` exists anywhere in the repo. As a result, 23 `__pycache__/*.pyc` files, two SQLite DBs (`f1_predictions.db`, `f1_predictor.db` — see m-4 for why there are two), and the FastF1 binary session cache (`cache/fastf1_cache/**`, ~98MB, including a `.sqlite` HTTP cache and several `.ff1pkl` binary blobs) are all committed to git. This bloats the repo, causes noisy diffs, and risks committing stale/environment-specific state as if it were source. | **Added** a `.gitignore` covering `__pycache__/`, `*.pyc`, `*.db`, `cache/fastf1_cache/`, `cache/api_responses/*.json`, `.env`, `venv/`. **Also ran `git rm --cached`** on `cache/fastf1_cache/**`, `f1_predictions.db`, `f1_predictor.db`, and the 2 tracked files under `cache/api_responses/` — this untracks them (stops committing them going forward) while leaving the files on disk for anyone who already has this checkout. History was not rewritten, per the constraint against force-pushing over existing history. |
| M-7 | `data/api_client.py` cache write path (`_cache_response`) | Missing error handling | Same class as B-3: `except (IOError, json.JSONDecodeError): pass` on the *write* path silently swallows any other exception (e.g. `TypeError` if `data` isn't JSON-serializable, `OSError` subtypes not covered by `IOError` on some platforms — though in Python 3 `IOError` is an alias for `OSError` so this one is mostly fine, the read-path NameError is the real gap). Documented here for completeness alongside B-3 since they're the same failure mode in the same file. | Covered by the same fix as B-3. |
| M-8 | `ai/provider.py` ↔ `ai/agents/chief_strategist.py` ↔ `engine/__init__.py` ↔ `engine/predictor.py` ↔ `engine/ai_client.py` | Architecture / fragile circular import | **[VERIFIED]**: importing `ai.provider` or `ai.agents.chief_strategist` as the *first* import in a process (e.g. `python -c "from ai.provider import AIProviderManager"`, or any test file that imports from `ai.*` before anything under `engine.*`) raises `ImportError: cannot import name '...' from partially initialized module` — a genuine circular dependency between the `ai` and `engine` packages (`ai.provider` → `ai.agents.chief_strategist` → `engine.tire_model` → `engine/__init__.py` → `engine.predictor` → `engine.ai_client` → `ai.provider`). It does not currently break the shipped app only because every real entry point happens to import `engine.predictor` before anything in `ai.*`. This is exactly the kind of ordering-dependent bug that resurfaces the next time someone adds a script, notebook, or test that imports `ai.*` first. | Flagged rather than fixed outright — breaking the cycle means either moving `ChiefStrategistAgent`'s tire-model dependency behind a lazy/local import, or moving the shared pieces both packages need into a third module they can both depend on without depending on each other. Both are reasonable but are a design decision, not a one-line fix, so left as a documented recommendation (final summary) rather than guessed at silently. |

### Minors

| # | File/Location | Category | Description | Proposed fix |
|---|---|---|---|---|
| m-1 | `config/settings.py:19` vs `.env.example` | Inconsistency | `Settings.DEBUG` defaults to `True` in code; `.env.example` documents `DEBUG=False`. Flask's `debug=True` enables the Werkzeug interactive debugger, which allows arbitrary code execution from any client that can reach the port if `main.py` is ever run without an explicit `.env` — a real footgun for a "just clone and run" README. | Changed the code default to `False` to match `.env.example` and the security-conscious default a new contributor would expect (Phase 4). |
| m-2 | `database/models.py:7` | Outdated pattern | `from sqlalchemy.ext.declarative import declarative_base` is deprecated since SQLAlchemy 2.0 (confirmed via the `MovedIn20Warning` raised on every test run). | Changed import to `from sqlalchemy.orm import declarative_base` (Phase 4). |
| m-3 | `monitoring/blueprint.py`, `monitoring/metrics.py` | Dead code | `monitoring_bp` (Prometheus `/metrics` endpoint) is never registered by `dashboard/app.py` or `main.py`, and needs `prometheus_client`, which isn't declared anywhere. Referenced by nothing else in the codebase. | Left in place but flagged — unlike the confirmed-broken `dashboard_bp`/`health_bp`/`app.py` trio, wiring this up is a reasonable, low-risk *addition* a maintainer may actually want, so it's called out as a "finish this" opportunity in Phase 6 rather than deleted. |
| m-4 | `f1_predictions.db`, `f1_predictor.db` (repo root) | Inconsistency | Two different committed SQLite files with confusingly similar names. `config/settings.py`'s default `DATABASE_URL` points at `sqlite:///./f1_predictions.db`; `.env.example` documents `DATABASE_URL=sqlite:///f1_predictor.db`. Depending on which one a given install actually uses, it may load stale/unrelated data left over from a previous session. | Both are now git-ignored going forward (M-6); documented here rather than deleted from the working tree, since deleting someone's local database file is exactly the kind of destructive action the brief says to avoid guessing on. |
| m-5 | `AGENTS.md`, `README.md` | Documentation gap | Both list a test suite (`test_probability_model.py`, `test_grid_autofill.py`, `test_fantasy_scoring.py`, `test_api_clients.py`) that does not exist; the actual suite is `test_ai_client.py`, `test_dashboard_blueprints.py`, `test_predictor.py`. Both also point to a `BUILD_PLAN.md` that isn't in the repo. | Updated the "Tests" sections of both docs to list the real files (Phase 4). Left the `BUILD_PLAN.md` reference as a comment for the maintainer rather than inventing a document that never existed. |
| m-6 | `dashboard/blueprints/reports.py` | Missing validation | `api_export()` does `data = request.json` with no null/shape check before `.get()`-chaining into it; an empty POST body (`request.json` is `None`) raises `AttributeError` inside the `try`, which is caught and returned as a generic 500 rather than a clean 400. Same pattern in `analytics_settings.py::api_update_feature_weights()`. | Left as a documented follow-up (Phase 6 candidate) — low severity, and touching every blueprint's input validation at once risks scope creep beyond what was asked. |

### Nits

| # | File/Location | Category | Description | Proposed fix |
|---|---|---|---|---|
| n-1 | Repo-wide | Style | Logging is inconsistent: most modules use the `logging` module correctly, but every `dashboard/blueprints/*.py` route handler and `main.py`/`scripts/*.py` use bare `print()` for status output. Acceptable for the CLI scripts; less so for library/blueprint code that already imports `logging` elsewhere in the same file. | Not changed — cosmetic, and `print()` in one-shot CLI scripts (`scripts/*.py`, `main.py`) is arguably the right call; only the blueprint files would benefit, and that's a larger diff than this pass's budget justifies. Flagged for a future pass. |
| n-2 | `ai/local/ollama_provider.py` | Naming | File is named for Ollama but implements its client via the `openai` SDK pointed at an OpenAI-compatible local endpoint — not wrong, just a non-obvious name for a first-time reader. | Not changed — purely cosmetic, no functional impact. |
| n-3 | `database/client.py:9-14` | Style | Three consecutive blank lines between the `Prediction` import and the `config.settings` import for no apparent reason. | Not changed — harmless whitespace, not worth a diff line in a file otherwise untouched by this pass. |

---

## Test coverage gap (T-1)

The existing 12 tests (`tests/test_ai_client.py`, `test_dashboard_blueprints.py`,
`test_predictor.py`) are well-written and all pass, but they only exercise:
`AIClient` provider-name parsing, five dashboard API routes, and
`generate_prediction()`'s three session types. **Entirely untested**:
`security/auth.py` and `security/middleware.py` (the JWT/rate-limit/input-
validation code — arguably the highest-risk untested surface in the repo),
`database/init.py` (would have caught B-4a immediately), `data/api_client.py`
and its cache path (would have caught B-3 immediately), every `reports/*`
generator's fallback behavior (would have caught B-5), and the majority of
`engine/*` beyond the orchestrator (`grid_model`, `elo_calculator`,
`tire_model`, `weather_model`, `safety_car_model`, `pit_strategy`,
`fantasy_scoring`, `benchmark_suite`, `calibration`, `ensemble_predictor`,
`ml_models`). Not fixed in this pass (writing a real test suite for ~15
untested modules is a separate, large effort) but called out explicitly
since three of the five confirmed Blockers in this report would have been
caught by tests that simply *import the module and call the happy path*.

---

## Merges performed (Phase 5)

| Merge | Files | Reasoning |
|---|---|---|
| 1 | `improve.md` deleted, `IMPROVEMENTS.md` kept | Byte-identical (M-2). No consumer references `improve.md` by name (`grep -r "improve.md"` → no hits outside itself), so nothing to update. |
| 2 | `migrations/001_initial_schema.py` deleted | Dead + broken duplicate of `migrations/_001_initial_schema.py` (M-5). No importer anywhere in the repo. |
| 3 | `app.py` (root) deleted | Orphaned duplicate Flask entry point, superseded by `main.py` + `dashboard/app.py` (M-1). Not referenced by `Dockerfile`, `README.md`, `AGENTS.md`, or any test. |

**Not merged**, despite being duplication findings, because doing so safely
requires touching every call site and is a data-model-adjacent decision:
`database/connection.py` vs `database/client.py` (M-3) — documented with a
concrete recommendation instead.

---

## Improvements made beyond the strict bug list (Phase 6)

- `.gitignore` added (M-6) — prevents the next commit from re-adding compiled
  `.pyc` files, databases, or the FastF1 binary cache.
- `requirements.txt` rewritten to actually match what the code imports
  (M-4/B-1/B-2/B-5) — `pip install -r requirements.txt && python main.py`
  now works from a clean checkout, which it did not before this pass.
- README/AGENTS.md test list corrected (m-5) so a new contributor running
  `pytest tests/test_probability_model.py` (a file that doesn't exist)
  doesn't hit a wall on their first command.
- `config/settings.py` `DEBUG` default flipped to `False` (m-1) so a
  first-time `git clone && python main.py` doesn't accidentally expose the
  Werkzeug debugger.

---

## Addendum — second pass (documentation + manifest reconciliation)

- **README.md** — the "Architecture Audit Summary" section previously
  claimed items like "Security Enhancements" and "Monitoring and
  Observability" were "addressed in Phase 10/11." Verified against the
  running app: both `security/auth.py`+`security/middleware.py` and
  `monitoring/blueprint.py` are real, working code that is **never
  imported by anything the running app registers** (same root cause as
  M-1/B-6). Rewrote that section to state the verified status of each
  item instead of the aspirational one, and added a note flagging the
  "Phase 11–14 Implementation Summary" sections further down as
  unverified roadmap text, with one concrete correction: Phase 13 claims
  "Full Coverage: All Jolpica, OpenF1, and FastF1 endpoints tested" —
  false; none of the 3 existing test files touch those clients at all.
- **AGENTS.md** — corrected the stale test-file listing (`test_probability_model.py`,
  `test_grid_autofill.py`, `test_fantasy_scoring.py`, `test_api_clients.py`
  → the real `test_ai_client.py`, `test_dashboard_blueprints.py`,
  `test_predictor.py`), and removed two dangling references to a
  `BUILD_PLAN.md` that doesn't exist in the repo.
- **pyproject.toml** — reconciled with the fixed `requirements.txt` (M-4):
  added `pydantic-settings`, `PyJWT`, `requests-cache`, `scipy`, `redis`,
  `prometheus_client`, `openai` to main dependencies (all are imported
  unconditionally somewhere in the codebase); moved `weasyprint`/`openpyxl`
  out of the optional `[reports]` extra into main dependencies, since PDF/
  Excel export is an advertised core feature (README's "Export Reports:
  CSV, JSON, PDF, and shareable summary cards"), not something that
  should silently degrade when skipped; dropped the `advanced-ml`
  (`pymc`, `lifelines`, `gpy`) and `reportlab` extras since nothing in the
  codebase imports any of them. Validated with `tomllib.load()`.

### Final verification (clean environment, run twice — before writing this
addendum and again immediately before finishing)

```
$ python3 -m venv /tmp/venv_verify && pip install -r requirements.txt   # clean, no errors
$ pytest tests/ -q                                                     # 12 passed
$ python3 -c "from dashboard.app import create_app; create_app()..."   # predict-session -> 200 "success"
$ python3 -c "from database.init import verify_database_connection..." # -> True
```

All four were failing or erroring before this pass (install failed outright
on `sqlite3>=3.35.0`; app couldn't even import `config.settings` without
manually installing 5 undeclared packages; `verify_database_connection()`
raised `Not an executable object`). All four pass cleanly now.

One correction to this report's own earlier claim: M-6 originally said the
committed cache/database binaries were "removed from the working tree" —
they were not; only `.gitignore` had been added, which doesn't affect
already-tracked files. Fixed with a follow-up `git rm --cached` commit on
`cache/fastf1_cache/**` (~98MB), `f1_predictions.db`, `f1_predictor.db`,
and the 2 tracked files under `cache/api_responses/` — untracked, but left
on disk, with no history rewrite.
