from sqlalchemy import String, Boolean, ForeignKey, DateTime, Float, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.warehouse import Warehouse
    from app.models.occupancy import OccupancyReading

class Camera(Base):
    """
    SQLAlchemy model representing a Camera entity.
    """
    __tablename__ = "camera"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouse.id", ondelete="CASCADE"), nullable=False)
    camera_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rtsp_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_storage_camera: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Production additions
    coverage_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    roi_polygon: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    camera_status: Mapped[str] = mapped_column(String(20), default="ONLINE", nullable=False)
    last_successful_capture: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="cameras")
    occupancy_readings: Mapped[List["OccupancyReading"]] = relationship(
        "OccupancyReading", 
        back_populates="camera", 
        cascade="all, delete-orphan"
    )
