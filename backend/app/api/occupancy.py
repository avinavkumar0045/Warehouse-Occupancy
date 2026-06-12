from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.schemas.occupancy import OccupancyReadingResponse
from app.services.occupancy_service import OccupancyService
from app.services.warehouse_service import WarehouseService
from app.services.camera_service import CameraService

router = APIRouter(prefix="/occupancy", tags=["Occupancy"])

@router.get("", response_model=List[OccupancyReadingResponse])
def get_all_occupancy_readings(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
) -> List[OccupancyReadingResponse]:
    """
    Retrieve historical logs of all occupancy readings in the platform.
    """
    return OccupancyService.get_all_readings(db, skip=skip, limit=limit)

@router.get("/{warehouse_id}", response_model=List[OccupancyReadingResponse])
def get_warehouse_occupancy_readings(
    warehouse_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
) -> List[OccupancyReadingResponse]:
    """
    Retrieve historical occupancy readings for a specific warehouse.
    """
    db_warehouse = WarehouseService.get_warehouse_by_id(db, warehouse_id)
    if not db_warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Warehouse with ID {warehouse_id} not found"
        )
    return OccupancyService.get_readings_by_warehouse(db, warehouse_id, skip=skip, limit=limit)

@router.get("/camera/{camera_id}", response_model=List[OccupancyReadingResponse])
def get_camera_occupancy_readings(
    camera_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
) -> List[OccupancyReadingResponse]:
    """
    Retrieve historical occupancy readings captured by a specific camera.
    """
    db_camera = CameraService.get_camera_by_id(db, camera_id)
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Camera with ID {camera_id} not found"
        )
    return OccupancyService.get_readings_by_camera(db, camera_id, skip=skip, limit=limit)

@router.post("/trigger", status_code=status.HTTP_200_OK)
def trigger_occupancy_polling() -> dict:
    """
    Manually trigger the occupancy estimation task for all active cameras.
    Useful for pipeline verification and frontend refreshes.
    """
    from app.scheduler.scheduler_service import poll_cameras_job
    poll_cameras_job()
    return {"message": "Occupancy polling job triggered and executed successfully."}

