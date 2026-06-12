from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.camera import Camera
    from app.models.occupancy import OccupancyReading

class Warehouse(Base):
    """
    SQLAlchemy model representing a Warehouse entity.
    """
    __tablename__ = "warehouse"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    # cascade="all, delete-orphan" ensures when a warehouse is deleted, its cameras and readings are also deleted
    cameras: Mapped[List["Camera"]] = relationship(
        "Camera", 
        back_populates="warehouse", 
        cascade="all, delete-orphan"
    )
    occupancy_readings: Mapped[List["OccupancyReading"]] = relationship(
        "OccupancyReading", 
        back_populates="warehouse", 
        cascade="all, delete-orphan"
    )
