"""
Pydantic schemas for OccupancyReading — request/response contracts.
Updated for Phase 6: exposes confidence_score, model_version, processing_time_ms.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class OccupancyReadingBase(BaseModel):
    occupancy_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Occupancy percentage estimate (0.0 to 100.0)"
    )


class OccupancyReadingCreate(OccupancyReadingBase):
    warehouse_id: int = Field(..., description="ID of the warehouse")
    camera_id: int = Field(..., description="ID of the camera recording the metric")
    # Phase 6 fields — optional on create; defaults applied by the DB model
    confidence_score: Optional[float] = Field(
        default=1.0, ge=0.0, le=1.0, description="Model confidence score (0.0–1.0)"
    )
    processing_time_ms: Optional[int] = Field(
        default=0, ge=0, description="Model inference time in milliseconds"
    )
    model_version: Optional[str] = Field(
        default="1.0.0", max_length=50, description="Semantic version of the inference model"
    )


class OccupancyReadingResponse(OccupancyReadingBase):
    id: int
    warehouse_id: int
    camera_id: int
    confidence_score: float
    processing_time_ms: int
    model_version: str
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)
