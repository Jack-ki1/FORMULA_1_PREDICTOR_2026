import os
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("F1_DATABASE_URL", "sqlite:///f1_predictor.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
Base = declarative_base()


class Race(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    circuit_id = Column(String(64), nullable=False, index=True)
    season = Column(Integer, nullable=False, index=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    predictions = relationship("Prediction", back_populates="race", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id = Column(String(64), nullable=False, index=True)
    predicted_position = Column(Integer, nullable=False)
    win_probability = Column(Float, nullable=False)
    top3_probability = Column(Float, nullable=False)
    top10_probability = Column(Float, nullable=False)
    dnf_probability = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    model_version = Column(String(32), nullable=False)
    actual_position = Column(Integer, nullable=True)
    actual_result = Column(String(32), nullable=True)
    brier_score = Column(Float, nullable=True)
    evaluated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    race = relationship("Race", back_populates="predictions")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    team = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def create_database() -> None:
    """Create the SQLite metadata tables."""
    Base.metadata.create_all(engine)


def migrate_from_static() -> None:
    """Create the database and migrate driver/circuit metadata from static data modules."""
    from data.driver_data import get_all_drivers
    from data.circuit_data import CIRCUITS

    create_database()
    db = SessionLocal()
    try:
        existing_drivers = {driver.id for driver in db.query(Driver).all()}

        for driver in get_all_drivers():
            if driver["id"] not in existing_drivers:
                db.add(Driver(
                    id=driver["id"],
                    name=driver.get("name", driver["id"]).strip(),
                    team=driver.get("team", "unknown"),
                ))

        existing_races = {
            (race.circuit_id, race.season)
            for race in db.query(Race).all()
        }
        for circuit in CIRCUITS.values():
            key = (circuit["id"], 2026)
            if key not in existing_races:
                db.add(Race(
                    circuit_id=circuit["id"],
                    season=2026,
                    completed=False,
                ))

        db.commit()
    finally:
        db.close()
