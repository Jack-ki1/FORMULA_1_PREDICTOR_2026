from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
import json
from models.prediction import Prediction




from config.settings import settings
from cache.redis import get_cache

logger = logging.getLogger(__name__)

# Create database engine with connection pooling
def create_database_engine():
    """Create SQLAlchemy engine with connection pooling."""
    return create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        echo=False,  # Set to True for debugging
        connect_args={"check_same_thread": False} if 'sqlite' in settings.DATABASE_URL else {}
    )

# Create session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use scoped session for thread safety
def get_db_session():
    """Get database session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database client class
class DatabaseClient:
    """Database client with connection pooling and data retention policies."""
    
    def __init__(self):
        self.engine = None
        self._initialize_engine()
        
        # Initialize cache
        self.cache = get_cache() if settings.CACHE_ENABLED else None
    
    def _initialize_engine(self):
        """Initialize database engine with connection pooling."""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                settings.DATABASE_URL,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                pool_recycle=settings.DATABASE_POOL_RECYCLE,
                echo=settings.DEBUG
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database engine: {e}")
            raise
    
    def get_session(self):
        """Get database session with optional caching."""
        return sessionmaker(bind=self.engine)()
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics with caching."""
        cache_key = "database:stats"
        
        # Try to get from cache first
        if self.cache:
            cached_stats = self.cache.get(cache_key)
            if cached_stats:
                logger.debug("Retrieved database stats from cache")
                return json.loads(cached_stats)
        
        try:
            with self.get_session() as db:
                # Get total predictions
                total_predictions = db.execute(
                    text("SELECT COUNT(*) FROM predictions")
                ).scalar()
                
                # Get recent predictions
                recent_predictions = db.execute(
                    text("SELECT COUNT(*) FROM predictions WHERE created_at > datetime('now', '-24 hours')")
                ).scalar()
                
                # Get prediction types count
                prediction_types = db.execute(
                    text("SELECT session, COUNT(*) FROM predictions GROUP BY session")
                ).fetchall()
                
                stats = {
                    'total_predictions': total_predictions or 0,
                    'recent_predictions_24h': recent_predictions or 0,
                    'prediction_types': dict(prediction_types) if prediction_types else {},
                    'status': 'healthy'
                }
                
                # Cache the results
                if self.cache:
                    self.cache.set(cache_key, stats, ttl=300)
                    
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e), 'status': 'unhealthy'}
    
    def get_prediction_by_id(self, prediction_id: int) -> Optional[Prediction]:
        """Get prediction by ID with caching."""
        cache_key = f"prediction:{prediction_id}"
        
        # Try to get from cache first
        if self.cache:
            cached_prediction = self.cache.get(cache_key)
            if cached_prediction:
                logger.debug(f"Retrieved prediction {prediction_id} from cache")
                return json.loads(cached_prediction)
        
        try:
            with self.get_session() as db:
                prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
                
                # Cache the result
                if self.cache and prediction:
                    self.cache.set(cache_key, prediction.__dict__, ttl=300)
                    
                return prediction
                
        except Exception as e:
            logger.error(f"Error getting prediction {prediction_id}: {e}")
            return None
    
    def save_prediction(self, prediction: Prediction) -> bool:
        """Save prediction with cache invalidation."""
        try:
            with self.get_session() as db:
                db.add(prediction)
                db.commit()
                db.refresh(prediction)
                
                # Invalidate related cache entries
                if self.cache:
                    self.cache.delete(f"prediction:{prediction.id}")
                    self.cache.delete("database:stats")
                    
                return True
                
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return False
    
    def cleanup_old_data(self) -> int:
        """Clean up old data according to retention policies with cache invalidation."""
        try:
            with self.get_session() as db:
                # Delete old predictions
                cutoff_date = datetime.utcnow() - timedelta(days=settings.PREDICTION_RETENTION_DAYS)
                deleted_count = db.execute(
                    text("DELETE FROM predictions WHERE created_at < :cutoff_date"),
                    {"cutoff_date": cutoff_date}
                ).rowcount
                
                db.commit()
                
                # Invalidate cache
                if self.cache:
                    self.cache.clear()
                    
                logger.info(f"Cleaned up {deleted_count} old predictions")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
