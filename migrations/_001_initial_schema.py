from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Create initial database schema."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Create predictions table
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_id TEXT NOT NULL,
                    session_type TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    driver_code TEXT NOT NULL,
                    probability REAL NOT NULL,
                    confidence_interval TEXT,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_final BOOLEAN DEFAULT FALSE
                )
            """))
            conn.commit()
        
        # Create session_data table
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS session_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_id TEXT NOT NULL,
                    session_type TEXT NOT NULL,
                    strength_adjustments TEXT,
                    grid_positions TEXT,
                    sources TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        
        # Create prediction_metadata table
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS prediction_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_id TEXT NOT NULL,
                    session_type TEXT NOT NULL,
                    total_probability_sum REAL,
                    probability_validation_status TEXT,
                    validation_errors TEXT,
                    model_drift_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        
        # Create migrations table
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        # Create indexes separately for SQLite compatibility
        with engine.connect() as conn:
            # Indexes for predictions table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_race_session ON predictions (race_id, session_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_driver ON predictions (driver_code)"))
            
            # Indexes for session_data table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sess_data_race_session ON session_data (race_id, session_type)"))
            
            # Indexes for prediction_metadata table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_meta_race_session ON prediction_metadata (race_id, session_type)"))

            conn.commit()
        
        # Insert initial migration record
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT OR IGNORE INTO migrations (version, description) 
                VALUES ('001_initial_schema', 'Initial database schema')
            """))
            conn.commit()
        
        logger.info("Initial database schema created successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating initial schema: {e}")
        raise


def downgrade():
    """Drop initial database schema."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Drop indexes first
        with engine.connect() as conn:
            index_names = [
                'idx_race_session', 'idx_driver', 'idx_sess_data_race_session', 'idx_meta_race_session'
            ]
            for index_name in index_names:
                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
            conn.commit()
        
        # Drop tables in reverse order to avoid foreign key issues
        tables_to_drop = ['predictions', 'session_data', 'prediction_metadata', 'migrations']
        with engine.connect() as conn:
            for table in tables_to_drop:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            conn.commit()
        
        logger.info("Initial database schema dropped successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Error dropping initial schema: {e}")
        raise