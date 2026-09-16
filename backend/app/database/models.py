"""
Database models using SQLAlchemy.
Defines the database schema for the F1 Predictor system.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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
    user_picks = relationship("UserPick", back_populates="driver")


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
    """User fantasy picks model."""
    __tablename__ = 'user_picks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_nickname = Column(String(50), nullable=False)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    session = Column(String(20), nullable=False)
    target = Column(String(20), nullable=False)
    driver_id = Column(String(50), ForeignKey('drivers.id'), nullable=False)
    made_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='pending')  # pending, resolved, expired
    points = Column(Integer, default=0)
    
    # Relationships
    driver = relationship("Driver", back_populates="user_picks")


class LeaderboardEntry(Base):
    """Fantasy leaderboard model."""
    __tablename__ = 'leaderboard'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String(50), unique=True, nullable=False)
    total_score = Column(Integer, default=0)
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


class User(Base):
    """User authentication model."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    favorite_driver = Column(String(50))
    favorite_team = Column(String(50))
    theme_preference = Column(String(20), default='light')  # light, dark, auto
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    predictions = relationship("UserPrediction", back_populates="user")
    fantasy_teams = relationship("FantasyTeam", back_populates="user")


class UserPrediction(Base):
    """User's saved predictions."""
    __tablename__ = 'user_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    race_id = Column(Integer, nullable=False)
    session_type = Column(String(20), nullable=False)  # race, qualifying, practice
    prediction_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="predictions")


class FantasyTeam(Base):
    """User's fantasy team selections."""
    __tablename__ = 'fantasy_teams'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    season = Column(Integer, nullable=False)
    drivers = Column(Text, nullable=False)  # JSON array of driver codes
    captain = Column(String(50))  # Captain driver code (2x points)
    vice_captain = Column(String(50))  # Vice-captain (1.5x points)
    total_budget = Column(Float, default=100.0)
    remaining_budget = Column(Float, default=100.0)
    total_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="fantasy_teams")
