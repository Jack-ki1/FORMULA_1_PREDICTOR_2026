import os


class Settings:
    data_mode = os.getenv("DATA_MODE", "auto")  # auto = live Jolpica with seed fallback, seed = offline only
    jolpica = os.getenv("JOLPICA_BASE", "https://api.jolpi.ca/ergast/f1")
    season = int(os.getenv("SEASON", "2026"))
    # Same-origin requests (the Vite dev proxy and the deployed Vercel app) need no CORS entry. Cross-origin callers
    # must be allow-listed explicitly; set CORS_ORIGINS="*" to allow any website to call the API.
    cors = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    max_sims = int(os.getenv("MAX_SIMS", "50000"))
    admin_token = os.getenv("SETTINGS_ADMIN_TOKEN", "")


settings = Settings()

# Runtime-tunable values (changed through the admin endpoint). They live in process memory only: on serverless they
# reset when the instance recycles, so set the matching environment variables for permanent changes.
runtime = {
    "cache_ttl": int(os.getenv("CACHE_TTL", "600")),
    "source_priority": "seed_only" if settings.data_mode == "seed" else "jolpica_first",
    "live_interval": int(os.getenv("LIVE_INTERVAL", "300")),
    "model_type": os.getenv("MODEL_TYPE", "monte_carlo_form"),
}
CHOICES = {"source_priority": {"jolpica_first", "seed_only"}, "model_type": {"monte_carlo", "monte_carlo_form"}}
