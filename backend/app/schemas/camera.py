"""
Pydantic schemas for Camera — request/response contracts.
Updated for Phase 6: exposes coverage_weight, roi_polygon, camera_status,
last_successful_capture, and notes.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Any


class CameraBase(BaseModel):
    camera_name: str = Field(..., max_length=255, description="Name of the camera")
    rtsp_url: str = Field(..., max_length=2048, description="RTSP stream URL")
    is_storage_camera: bool = Field(
        True, description="True if the camera monitors a storage area"
    )
    is_active: bool = Field(
        True, description="True if the camera is active and polled by the scheduler"
    )


class CameraCreate(CameraBase):
    warehouse_id: int = Field(..., description="ID of the warehouse this camera belongs to")
    # Phase 6 optional fields on create
    coverage_weight: float = Field(
        default=1.0, ge=0.1, le=10.0,
        description="Weight for weighted occupancy averaging (default 1.0)"
    )
    notes: Optional[str] = Field(
        default=None, description="Operator notes about this camera"
    )


class CameraUpdate(BaseModel):
    warehouse_id: Optional[int] = Field(None, description="Warehouse ID")
    camera_name: Optional[str] = Field(None, max_length=255)
    rtsp_url: Optional[str] = Field(None, max_length=2048)
    is_storage_camera: Optional[bool] = None
    is_active: Optional[bool] = None
    coverage_weight: Optional[float] = Field(None, ge=0.1, le=10.0)
    roi_polygon: Optional[List[Any]] = Field(
        None, description="List of {x, y} dicts defining the ROI polygon"
    )
    camera_status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class CameraResponse(CameraBase):
    id: int
    warehouse_id: int
    # Phase 6 fields
    coverage_weight: float
    roi_polygon: Optional[List[Any]]
    camera_status: str
    last_successful_capture: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
