import logging

from sqlalchemy import create_engine, text
from backend.app.config.settings import settings
from backend.app.database.migrations._001_initial_schema import upgrade, downgrade

logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database with migrations."""
    try:
        # Run database migrations
        upgrade()
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