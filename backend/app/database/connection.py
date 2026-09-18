"""
Database connection and session management.
Handles SQLAlchemy connection pooling and session lifecycle.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from backend.app.config.settings import settings

# Import Base for table creation
try:
    from backend.app.database.models import Base
except ImportError:
    # Handle circular import by deferring import
    Base = None


class DatabaseConnection:
    """Manages database connection and sessions."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection.
        
        Args:
            database_url: Database connection string
        """
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        self.session = None
    
    def connect(self):
        """Create database engine and session factory."""
        # Import Base here to avoid circular import
        from backend.app.database.models import Base
        
        # Determine if we're using SQLite or PostgreSQL
        is_sqlite = self.database_url.startswith('sqlite')
        
        # Configure engine based on database type
        engine_kwargs = {
            'echo': settings.DEBUG,
            'pool_pre_ping': True,  # Verify connections before using
        }
        
        # SQLite-specific settings (not applicable to PostgreSQL)
        if is_sqlite:
            engine_kwargs.update({
                'pool_size': 5,
                'max_overflow': 10,
                'connect_args': {'check_same_thread': False}  # SQLite threading workaround
            })
        else:
            # PostgreSQL uses different pool defaults
            engine_kwargs.update({
                'pool_size': 10,  # Higher default for Postgres
                'max_overflow': 20,
            })
        
        self.engine = create_engine(self.database_url, **engine_kwargs)
        
        self.SessionLocal = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        )
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def disconnect(self):
        """Close database connections."""
        if self.session:
            self.session.close()
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()
    
    def get_session(self):
        """Get a database session."""
        if not self.SessionLocal:
            self.connect()
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db.session_scope() as session:
                session.add(object)
                session.commit()
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def init_db(self):
        """Initialize database with base data."""
        self.connect()
        
        # Import and run initialization scripts
        with self.session_scope() as session:
            # Check if data already exists
            if session.query(Team).count() > 0:
                print("Database already initialized")
                return
            
            # Initialize base data
            self._init_teams(session)
            self._init_drivers(session)
            self._init_circuits(session)
            self._init_calendar(session)
            
            print("Database initialized successfully")
    
    def _init_teams(self, session):
        """Initialize teams from backend.app.config."""
        from backend.app.config.team_driver_lineup_2026 import TEAMS_2026
        from backend.app.database.models import Team as TeamModel
        
        for team_data in TEAMS_2026:
            team = TeamModel(
                id=team_data['id'],
                name=team_data['name'],
                color_hex=team_data['color'],
            )
            session.add(team)
    
    def _init_drivers(self, session):
        """Initialize drivers from backend.app.config."""
        from backend.app.config.team_driver_lineup_2026 import TEAMS_2026
        from backend.app.database.models import Driver as DriverModel
        
        for team_data in TEAMS_2026:
            for driver_data in team_data['drivers']:
                driver = DriverModel(
                    id=driver_data['code'],
                    name=driver_data['name'],
                    number=driver_data['number'],
                    team_id=team_data['id'],
                    wet_skill=driver_data['wet_skill'],
                    reliability_base=driver_data['reliability'],
                )
                session.add(driver)
    
    def _init_circuits(self, session):
        """Initialize circuits from data module."""
        from backend.app.data.circuit_data import CIRCUITS
        from backend.app.database.models import Circuit as CircuitModel
        
        for circuit_id, circuit_data in CIRCUITS.items():
            circuit = CircuitModel(
                id=circuit_id,
                name=circuit_data['name'],
                location=circuit_data['location'],
                country=circuit_data['country'],
                laps=circuit_data['laps'],
                length_km=circuit_data['length_km'],
                drs_zones=circuit_data['drs_zones'],
                overtaking_rating=circuit_data['overtaking'],
            )
            session.add(circuit)
    
    def _init_calendar(self, session):
        """Initialize race calendar from data module."""
        from datetime import datetime
        from backend.app.data.calendar_2026 import CALENDAR_2026
        from backend.app.database.models import Race as RaceModel
        
        for race_data in CALENDAR_2026:
            if race_data['status'] == 'cancelled':
                continue
            
            # Parse date (simplified - in production use proper date parsing)
            date_str = race_data['date']
            # This is a simplified date parsing - adjust based on actual format
            race_date = datetime.strptime(f"2026-{date_str}", "%Y-%b %d")
            
            # Map circuit name to circuit ID
            circuit_id = race_data['circuit'].lower().replace(' ', '_')
            
            race = RaceModel(
                season=settings.SEASON_YEAR,
                round=race_data['round'],
                circuit_id=circuit_id,
                date=race_date,
                status=race_data['status'],
                sprint=race_data.get('sprint', False),
            )
            session.add(race)
    
    def clear_cache(self):
        """Clear expired cache entries."""
        from datetime import datetime, timezone
        from backend.app.database.models import CacheEntry as CacheEntryModel

        with self.session_scope() as session:
            expired_entries = session.query(CacheEntryModel).filter(
                CacheEntryModel.expires_at < datetime.now(timezone.utc)
            ).all()
            
            for entry in expired_entries:
                session.delete(entry)


# Global database connection instance
db = DatabaseConnection()

# Import models after class definition to avoid circular dependency
from backend.app.database.models import (
    Team as TeamModel, Driver as DriverModel, Circuit as CircuitModel, Race as RaceModel,
    QualifyingResult as QualifyingResultModel, RaceResult as RaceResultModel,
    DriverStanding as DriverStandingModel, ConstructorStanding as ConstructorStandingModel,
    UserPick as UserPickModel,
    LeaderboardEntry as LeaderboardEntryModel, ModelRun as ModelRunModel, CacheEntry as CacheEntryModel
)
from backend.app.models.prediction import Prediction as PredictionModel

# Export the model classes with proper names
Team = TeamModel
Driver = DriverModel
Circuit = CircuitModel
Race = RaceModel
QualifyingResult = QualifyingResultModel
RaceResult = RaceResultModel
DriverStanding = DriverStandingModel
ConstructorStanding = ConstructorStandingModel
Prediction = PredictionModel
UserPick = UserPickModel
LeaderboardEntry = LeaderboardEntryModel
ModelRun = ModelRunModel
CacheEntry = CacheEntryModel
