import logging

from sqlalchemy import create_engine, text
from backend.app.database.migrations._001_initial_schema import upgrade

logger = logging.getLogger(__name__)

_initialized = False


def initialize_database(force: bool = False):
    """Initialize the database with migrations.

    Idempotent AND memoised: `create_app()` calls this, and create_app() is
    called once per test and once per worker — running the full migration each
    time was pure startup cost. Migrations are only re-run with force=True.
    """
    global _initialized
    if _initialized and not force:
        return
    try:
        upgrade()
        _initialized = True
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def verify_database_connection():
    """Verify database connection is working."""
    try:
        from backend.app.config.settings import settings
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            logger.info(f"Database connection verified. Found {table_count} tables.")
            return True
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False