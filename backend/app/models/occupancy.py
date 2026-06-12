from sqlalchemy import Float, ForeignKey, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import TYPE_CHECKING

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.warehouse import Warehouse
    from app.models.camera import Camera

class OccupancyReading(Base):
    """
    SQLAlchemy model representing an OccupancyReading entity.
    """
    __tablename__ = "occupancy_reading"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouse.id", ondelete="CASCADE"), nullable=False)
    camera_id: Mapped[int] = mapped_column(ForeignKey("camera.id", ondelete="CASCADE"), nullable=False)
    occupancy_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Production additions
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="occupancy_readings")
    camera: Mapped["Camera"] = relationship("Camera", back_populates="occupancy_readings")
