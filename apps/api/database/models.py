"""
Database models using SQLAlchemy.
Defines the database schema for the F1 Predictor system.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """
    A signed-in user, provisioned via Auth.js (NextAuth) OAuth sign-in.
    The frontend never talks to Postgres directly — Auth.js calls
    `POST /api/auth/sync-user` (routers/auth.py) on first sign-in, which
    upserts a row here keyed on (provider, provider_account_id).
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(30), nullable=False)          # 'github', 'google'
    provider_account_id = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    picks = relationship("UserPick", back_populates="user")
    leaderboard_entry = relationship("LeaderboardEntry", back_populates="user", uselist=False)

    __table_args__ = (
        UniqueConstraint('provider', 'provider_account_id', name='uq_user_provider_account'),
    )


class Team(Base):
    """Team model for constructor information."""
    __tablename__ = 'teams'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    color_hex = Column(String(7), nullable=False)
    base = Column(String(100))
    engine = Column(String(50))
    championships = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    
    # Relationships
    drivers = relationship("Driver", back_populates="team")
    constructor_standings = relationship("ConstructorStanding", back_populates="team")


class Driver(Base):
    """Driver model for driver information."""
    __tablename__ = 'drivers'
    
    id = Column(String(50), primary_key=True)  # Driver code
    name = Column(String(100), nullable=False)
    number = Column(Integer, nullable=False)
    team_id = Column(String(50), ForeignKey('teams.id'), nullable=False)
    wet_skill = Column(Integer, default=50)
    reliability_base = Column(Integer, default=50)
    nationality = Column(String(50))
    date_of_birth = Column(String(20))
    
    # Relationships
    team = relationship("Team", back_populates="drivers")
    driver_standings = relationship("DriverStanding", back_populates="driver")
    qualifying_results = relationship("QualifyingResult", back_populates="driver")
    race_results = relationship("RaceResult", back_populates="driver")


class Circuit(Base):
    """Circuit model for track information."""
    __tablename__ = 'circuits'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    laps = Column(Integer, nullable=False)
    length_km = Column(Float, nullable=False)
    drs_zones = Column(Integer, default=2)
    overtaking_rating = Column(String(20))
    
    # Relationships
    races = relationship("Race", back_populates="circuit")


class Race(Base):
    """Race model for race information."""
    __tablename__ = 'races'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False)
    round = Column(Integer, nullable=False)
    circuit_id = Column(String(50), ForeignKey('circuits.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)  # completed, upcoming, cancelled
    sprint = Column(Boolean, default=False)
    
    # Relationships
    circuit = relationship("Circuit", back_populates="races")
    qualifying_results = relationship("QualifyingResult", back_populates="race")
    race_results = relationship("RaceResult", back_populates="race")


class QualifyingResult(Base):
    """Qualifying results model."""
    __tablename__ = 'qualifying_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    driver_id = Column(String(50), ForeignKey('drivers.id'), nullable=False)
    position = Column(Integer, nullable=False)
    q1_time = Column(String(20))
    q2_time = Column(String(20))
    q3_time = Column(String(20))
    source = Column(String(20), default='simulated')  # live, simulated, manual
    
    # Relationships
    race = relationship("Race", back_populates="qualifying_results")
    driver = relationship("Driver", back_populates="qualifying_results")


class RaceResult(Base):
    """Race results model."""
    __tablename__ = 'race_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    driver_id = Column(String(50), ForeignKey('drivers.id'), nullable=False)
    position = Column(Integer, nullable=False)
    points = Column(Integer, default=0)
    status = Column(String(50))  # Finished, DNF, DNS, etc.
    grid = Column(Integer)
    laps = Column(Integer)
    time = Column(String(20))
    fastest_lap = Column(Boolean, default=False)
    
    # Relationships
    race = relationship("Race", back_populates="race_results")
    driver = relationship("Driver", back_populates="race_results")


class DriverStanding(Base):
    """Driver championship standings model."""
    __tablename__ = 'driver_standings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False)
    round = Column(Integer, nullable=False)
    driver_id = Column(String(50), ForeignKey('drivers.id'), nullable=False)
    position = Column(Integer, nullable=False)
    points = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    podiums = Column(Integer, default=0)
    
    # Relationships
    driver = relationship("Driver", back_populates="driver_standings")


class ConstructorStanding(Base):
    """Constructor championship standings model."""
    __tablename__ = 'constructor_standings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False)
    round = Column(Integer, nullable=False)
    team_id = Column(String(50), ForeignKey('teams.id'), nullable=False)
    position = Column(Integer, nullable=False)
    points = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    
    # Relationships
    team = relationship("Team", back_populates="constructor_standings")


class UserPick(Base):
    """A signed-in user's prediction pick for one race/session/category.

    race_id and driver_id intentionally aren't foreign keys into the
    `races`/`drivers` tables below — those are populated independently
    by apps/ingest from Jolpica and use their own integer/relational
    identifiers, whereas race_id/driver_id here need to match the plain
    string codes ('au', 'VER', ...) that CALENDAR_2026, Prediction.race_id,
    and config/team_driver_lineup_2026.py use everywhere else in the app.
    """
    __tablename__ = 'user_picks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    race_id = Column(String(50), nullable=False)     # CALENDAR_2026 race code, e.g. 'au'
    session = Column(String(20), nullable=False)      # 'qualifying' | 'race' | 'sprint'
    target = Column(String(20), nullable=False)        # 'winner' | 'podium' | 'pole' | 'fastest_lap'
    driver_id = Column(String(10), nullable=False)     # driver code, e.g. 'VER'
    made_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='pending')  # pending, resolved, expired
    points = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="picks")

    __table_args__ = (
        UniqueConstraint('user_id', 'race_id', 'session', 'target', name='uq_pick_per_slot'),
    )


class LeaderboardEntry(Base):
    """Fantasy leaderboard — one row per user, running season total."""
    __tablename__ = 'leaderboard'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    total_score = Column(Integer, default=0)
    picks_made = Column(Integer, default=0)
    picks_resolved = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="leaderboard_entry")


class UserSettings(Base):
    """Per-user feature-weight slider preferences (chaos/wet/reliability/
    strategy/grid) — replaces the old Flask app's global, unscoped
    in-memory settings with something that actually persists per user."""
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    chaos_level = Column(Integer, default=50)
    wet_influence = Column(Integer, default=50)
    reliability_influence = Column(Integer, default=50)
    strategy_aggressiveness = Column(Integer, default=50)
    grid_weight = Column(Integer, default=55)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelRun(Base):
    """Model performance tracking."""
    __tablename__ = 'model_runs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    target = Column(String(20), nullable=False)
    accuracy = Column(Float, nullable=False)
    baseline = Column(Float, nullable=False)
    backtest_season = Column(Integer, nullable=False)
    model_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class CacheEntry(Base):
    """API response cache model."""
    __tablename__ = 'cache_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, nullable=False)
    response_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    source = Column(String(20), default='cached')
