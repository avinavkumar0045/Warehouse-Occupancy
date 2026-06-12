"""
OccupancyService — CRUD operations for OccupancyReading.
Updated for Phase 6: persists confidence_score, model_version, processing_time_ms.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy.orm import Session

from app.models.occupancy import OccupancyReading
from app.schemas.occupancy import OccupancyReadingCreate

logger = logging.getLogger(__name__)


class OccupancyService:
    """Services for managing Occupancy Readings."""

    @staticmethod
    def create_reading(db: Session, schema: OccupancyReadingCreate) -> OccupancyReading:
        """Persist a new OccupancyReading, including Phase 6 metadata fields."""
        logger.info(
            f"OccupancyService: Storing reading — camera_id={schema.camera_id}, "
            f"warehouse_id={schema.warehouse_id}, "
            f"occupancy={schema.occupancy_percentage}%, "
            f"confidence={schema.confidence_score}, "
            f"model={schema.model_version}, "
            f"time={schema.processing_time_ms}ms."
        )
        db_obj = OccupancyReading(
            warehouse_id=schema.warehouse_id,
            camera_id=schema.camera_id,
            occupancy_percentage=schema.occupancy_percentage,
            confidence_score=schema.confidence_score if schema.confidence_score is not None else 1.0,
            processing_time_ms=schema.processing_time_ms if schema.processing_time_ms is not None else 0,
            model_version=schema.model_version if schema.model_version is not None else "1.0.0",
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_all_readings(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[OccupancyReading]:
        logger.info("OccupancyService: Fetching all occupancy readings.")
        return (
            db.query(OccupancyReading)
            .order_by(OccupancyReading.captured_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_readings_by_warehouse(
        db: Session, warehouse_id: int, skip: int = 0, limit: int = 100
    ) -> List[OccupancyReading]:
        logger.info(f"OccupancyService: Fetching readings for warehouse_id={warehouse_id}.")
        return (
            db.query(OccupancyReading)
            .filter(OccupancyReading.warehouse_id == warehouse_id)
            .order_by(OccupancyReading.captured_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_readings_by_camera(
        db: Session, camera_id: int, skip: int = 0, limit: int = 100
    ) -> List[OccupancyReading]:
        logger.info(f"OccupancyService: Fetching readings for camera_id={camera_id}.")
        return (
            db.query(OccupancyReading)
            .filter(OccupancyReading.camera_id == camera_id)
            .order_by(OccupancyReading.captured_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
