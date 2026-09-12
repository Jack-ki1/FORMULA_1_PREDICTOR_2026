from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any

# Use the shared Base from database/models.py to avoid duplicate registries
from database.models import Base


class Prediction(Base):
    """Database model for F1 race predictions."""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    race_id = Column(String(50), index=True)
    session_type = Column(String(20))
    prediction_type = Column(String(50))
    driver_code = Column(String(10))
    probability = Column(Float)
    confidence_interval = Column(JSON)  # {"lower": 0.1, "upper": 0.3}
    model_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_final = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Prediction(race_id='{self.race_id}', driver='{self.driver_code}', prob={self.probability:.3f})>"


class SessionData(Base):
    """Database model for session context data."""
    __tablename__ = 'session_data'
    
    id = Column(Integer, primary_key=True)
    race_id = Column(String(50), index=True)
    session_type = Column(String(20))
    strength_adjustments = Column(JSON)  # {"VER": 0.12, "HAM": 0.08}
    grid_positions = Column(JSON)  # {"VER": 1, "HAM": 2}
    sources = Column(JSON)  # ["jolpica", "openf1"]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SessionData(race_id='{self.race_id}', session='{self.session_type}')>"


class PredictionMetadata(Base):
    """Database model for prediction metadata and validation metrics."""
    __tablename__ = 'prediction_metadata'
    
    id = Column(Integer, primary_key=True)
    race_id = Column(String(50), index=True)
    session_type = Column(String(20))
    total_probability_sum = Column(Float)
    probability_validation_status = Column(String(20))  # "valid", "adjusted", "invalid"
    validation_errors = Column(Text)  # JSON string of errors
    model_drift_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PredictionMetadata(race_id='{self.race_id}', status='{self.probability_validation_status}')>"


class DatabaseMigration(Base):
    """Database model to track migrations."""
    __tablename__ = 'migrations'
    
    id = Column(Integer, primary_key=True)
    version = Column(String(20), unique=True)
    description = Column(String(200))
    applied_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Migration(version='{self.version}')>"
