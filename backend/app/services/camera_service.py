from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate

logger = logging.getLogger(__name__)

class CameraService:
    """
    CRUD services for Camera management.
    """

    @staticmethod
    def create_camera(db: Session, schema: CameraCreate) -> Camera:
        logger.info(
            f"CameraService: Creating camera '{schema.camera_name}' "
            f"for warehouse_id={schema.warehouse_id}, weight={schema.coverage_weight}."
        )
        db_obj = Camera(
            warehouse_id=schema.warehouse_id,
            camera_name=schema.camera_name,
            rtsp_url=schema.rtsp_url,
            is_storage_camera=schema.is_storage_camera,
            is_active=schema.is_active,
            coverage_weight=schema.coverage_weight,
            notes=schema.notes,
            camera_status="ONLINE",  # optimistic default until first health check
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_camera_by_id(db: Session, camera_id: int) -> Optional[Camera]:
        logger.info(f"Fetching camera with id: {camera_id}")
        return db.query(Camera).filter(Camera.id == camera_id).first()

    @staticmethod
    def get_all_cameras(db: Session, warehouse_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Camera]:
        logger.info(f"Fetching cameras (warehouse_id filter: {warehouse_id})")
        query = db.query(Camera)
        if warehouse_id is not None:
            query = query.filter(Camera.warehouse_id == warehouse_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_active_cameras(db: Session) -> List[Camera]:
        logger.info("Fetching all active cameras")
        return db.query(Camera).filter(Camera.is_active == True).all()

    @staticmethod
    def update_camera(db: Session, camera_id: int, schema: CameraUpdate) -> Optional[Camera]:
        logger.info(f"Updating camera with id: {camera_id}")
        db_obj = CameraService.get_camera_by_id(db, camera_id)
        if not db_obj:
            logger.warning(f"Camera with id {camera_id} not found for update")
            return None
        
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
            
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete_camera(db: Session, camera_id: int) -> bool:
        logger.info(f"Deleting camera with id: {camera_id}")
        db_obj = CameraService.get_camera_by_id(db, camera_id)
        if not db_obj:
            logger.warning(f"Camera with id {camera_id} not found for deletion")
            return False
        db.delete(db_obj)
        db.commit()
        return True
