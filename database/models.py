"""
Database Layer — SQLAlchemy ORM models for F1 Prediction System v3.0.

Replaces static Python modules with persistent SQLite database.
Provides ACID guarantees, concurrent access, and efficient historical queries.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL — can be overridden via environment variable
DATABASE_URL = os.getenv("F1_DATABASE_URL", "sqlite:///f1_predictor.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Models ─────────────────────────────────────────────────────────────────────

class Driver(Base):
    """Driver profiles with ELO ratings and attributes."""
    __tablename__ = "drivers"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    number = Column(Integer)
    nationality = Column(String)
    team = Column(String, ForeignKey("constructors.id"))
    elo_rating = Column(Float, default=1500.0)
    qualifying_elo = Column(Float, default=1500.0)
    wet_weather_elo = Column(Float, default=1500.0)
    wet_skill = Column(Float, default=7.0)
    experience_races = Column(Integer, default=0)
    dnf_rate_career = Column(Float, default=0.15)
    dnf_rate_recent = Column(Float, default=0.15)
    qualifying_delta_avg = Column(Float, default=0.0)
    championship_points_2026 = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    track_type_fit = Column(JSON)  # Dict: {"high_speed": 1.0, "street": 0.95, ...}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    constructor = relationship("Constructor", back_populates="drivers")
    results = relationship("RaceResult", back_populates="driver")
    predictions = relationship("Prediction", back_populates="driver")
    elo_history = relationship("ELOHistory", back_populates="driver")


class Constructor(Base):
    """Constructor (team) profiles."""
    __tablename__ = "constructors"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nationality = Column(String)
    base_strength = Column(Float, default=0.5)
    reliability = Column(Float, default=0.85)
    championship_points_2026 = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    drivers = relationship("Driver", back_populates="constructor")
    results = relationship("ConstructorResult", back_populates="constructor")


class Circuit(Base):
    """Circuit profiles with characteristics."""
    __tablename__ = "circuits"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String)
    country = Column(String)
    lap_count = Column(Integer)
    circuit_length_km = Column(Float)
    lap_record = Column(Float)  # Seconds
    circuit_type = Column(JSON)  # List: ["high_speed", "street", ...]
    safety_car_probability = Column(Float, default=0.5)
    rain_probability_typical = Column(Float, default=0.2)
    overtaking_difficulty = Column(Float, default=0.5)  # 0=easy, 1=hard
    drs_zones = Column(Integer, default=2)
    elevation_change_m = Column(Integer)
    first_grand_prix = Column(Integer)
    round_2026 = Column(Integer)
    race_date = Column(String)
    sprint_weekend = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    races = relationship("Race", back_populates="circuit")


class Race(Base):
    """Race events."""
    __tablename__ = "races"
    
    id = Column(Integer, primary_key=True, index=True)
    circuit_id = Column(String, ForeignKey("circuits.id"))
    season = Column(Integer)
    round = Column(Integer)
    race_name = Column(String)
    race_date = Column(String)
    sprint_weekend = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    weather_conditions = Column(JSON)  # Dict with weather data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    circuit = relationship("Circuit", back_populates="races")
    results = relationship("RaceResult", back_populates="race")
    predictions = relationship("Prediction", back_populates="race")


class RaceResult(Base):
    """Historical race results for drivers."""
    __tablename__ = "race_results"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    driver_id = Column(String, ForeignKey("drivers.id"))
    grid_position = Column(Integer)
    final_position = Column(Integer)
    points = Column(Float, default=0.0)
    fastest_lap = Column(Boolean, default=False)
    status = Column(String)  # "Finished", "DNF", "DNF - Engine", etc.
    laps_completed = Column(Integer)
    race_time_seconds = Column(Float)
    tire_strategy = Column(JSON)  # List of compounds used
    pit_stops = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    race = relationship("Race", back_populates="results")
    driver = relationship("Driver", back_populates="results")


class ConstructorResult(Base):
    """Historical race results for constructors."""
    __tablename__ = "constructor_results"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    constructor_id = Column(String, ForeignKey("constructors.id"))
    points = Column(Float, default=0.0)
    driver1_position = Column(Integer)
    driver2_position = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    race = relationship("Race")
    constructor = relationship("Constructor", back_populates="results")


class Prediction(Base):
    """Stored predictions for accuracy tracking."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    driver_id = Column(String, ForeignKey("drivers.id"))
    predicted_position = Column(Float)
    win_probability = Column(Float)
    top3_probability = Column(Float)
    top10_probability = Column(Float)
    dnf_probability = Column(Float)
    composite_score = Column(Float)
    model_version = Column(String, default="v3.0")
    actual_position = Column(Integer, nullable=True)  # Filled after race
    actual_result = Column(String, nullable=True)
    brier_score = Column(Float, nullable=True)  # Computed post-race
    created_at = Column(DateTime, default=datetime.utcnow)
    evaluated_at = Column(DateTime, nullable=True)
    
    # Relationships
    race = relationship("Race", back_populates="predictions")
    driver = relationship("Driver", back_populates="predictions")


class ELOHistory(Base):
    """Historical ELO ratings after each race."""
    __tablename__ = "elo_history"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(String, ForeignKey("drivers.id"))
    race_id = Column(Integer, ForeignKey("races.id"))
    elo_rating = Column(Float)
    qualifying_elo = Column(Float)
    wet_weather_elo = Column(Float)
    race_date = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    driver = relationship("Driver", back_populates="elo_history")
    race = relationship("Race")


class ModelWeight(Base):
    """Optimized feature weights from Optuna tuning."""
    __tablename__ = "model_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    weight_name = Column(String, nullable=False, unique=True)
    weight_value = Column(Float, nullable=False)
    optimized_at = Column(DateTime, default=datetime.utcnow)
    optuna_study_id = Column(Integer)
    validation_score = Column(Float)  # Brier score or log-loss
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class CalibrationParameter(Base):
    """Platt calibration parameters per outcome type."""
    __tablename__ = "calibration_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    outcome_type = Column(String, nullable=False)  # "win", "top3", "top10", "dnf"
    parameter_a = Column(Float, default=1.0)
    parameter_b = Column(Float, default=0.0)
    fitted_at = Column(DateTime, default=datetime.utcnow)
    training_races = Column(Integer)
    brier_score_before = Column(Float)
    brier_score_after = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Database Initialization ───────────────────────────────────────────────────

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (dependency injection for FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_from_static():
    """
    Migrate data from static Python modules to database.
    Run once during initial setup.
    """
    from data.driver_data import get_all_drivers as static_drivers
    from data.circuit_data import get_all_circuits as static_circuits
    from data.season_2026 import DRIVER_STANDINGS_AFTER_R5, CONSTRUCTOR_STANDINGS_AFTER_R5
    
    init_db()
    db = SessionLocal()
    
    try:
        # Migrate circuits
        for circuit in static_circuits():
            # Map circuit data fields to database model fields
            db_circuit = Circuit(
                id=circuit.get("id"),
                name=circuit.get("name"),
                city=circuit.get("city"),
                country=circuit.get("country"),
                lap_count=circuit.get("lap_count"),
                circuit_length_km=circuit.get("lap_distance_km"),  # Map lap_distance_km to circuit_length_km
                safety_car_probability=circuit.get("safety_car_probability", 0.5),
                rain_probability_typical=circuit.get("rain_probability_typical", 0.2),
                overtaking_difficulty=float(circuit.get("overtaking_difficulty", 5)) / 10.0,  # Normalize 0-10 to 0-1
                drs_zones=circuit.get("drs_zones", 2),
                circuit_type=circuit.get("circuit_type", []),
                round_2026=circuit.get("round_2026"),
                race_date=circuit.get("race_date"),
                sprint_weekend=circuit.get("sprint_weekend", False),
            )
            db.add(db_circuit)
        
        # Migrate constructors
        constructor_ids = set()
        for driver in static_drivers():
            if driver.get("team") and driver["team"] not in constructor_ids:
                constructor_ids.add(driver["team"])
        
        for const_id in constructor_ids:
            constructor = Constructor(id=const_id, name=const_id.replace("_", " ").title())
            db.add(constructor)
        
        # Migrate drivers
        for driver in static_drivers():
            db_driver = Driver(
                id=driver["id"],
                name=driver["name"],
                number=driver.get("number"),
                team=driver.get("team"),
                elo_rating=driver.get("elo", 1500.0),
                wet_skill=driver.get("wet_skill", 7.0),
                experience_races=driver.get("experience_races", 0),
                dnf_rate_career=driver.get("dnf_rate_career", 0.15),
                dnf_rate_recent=driver.get("dnf_rate_recent", 0.15),
                qualifying_delta_avg=driver.get("qualifying_delta_avg", 0.0),
                championship_points_2026=driver.get("championship_points_2026", 0.0),
                active=driver.get("active", True),
                track_type_fit=driver.get("track_type_fit", {}),
            )
            db.add(db_driver)
        
        db.commit()
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing F1 Predictor Database...")
    migrate_from_static()
