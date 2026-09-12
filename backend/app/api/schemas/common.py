"""Common schemas: error contract, health, races."""
try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC=True
except ImportError:
    HAS_PYDANTIC=False
    BaseModel=object

if HAS_PYDANTIC:
    from typing import Any, Optional, List, Dict
    class ErrorDetail(BaseModel):
        code: str
        message: str
        details: Optional[Dict[str,Any]] = None
        request_id: Optional[str] = None
    class ErrorResponse(BaseModel):
        error: ErrorDetail
    class HealthResponse(BaseModel):
        status: str
        version: str
        timestamp: Optional[str] = None
    class RaceResponse(BaseModel):
        id: str
        name: str
        circuit: str
        date: str
        status: str
