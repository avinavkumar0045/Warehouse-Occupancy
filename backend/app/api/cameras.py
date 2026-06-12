from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from app.services.camera_service import CameraService
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(camera: CameraCreate, db: Session = Depends(get_db)) -> CameraResponse:
    """
    Register a camera and associate it with a warehouse.
    """
    # Verify warehouse exists
    db_warehouse = WarehouseService.get_warehouse_by_id(db, camera.warehouse_id)
    if not db_warehouse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Warehouse with ID {camera.warehouse_id} does not exist."
        )
    return CameraService.create_camera(db, camera)

@router.get("", response_model=List[CameraResponse])
def get_cameras(
    warehouse_id: Optional[int] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
) -> List[CameraResponse]:
    """
    Retrieve registered cameras, with optional filtering by warehouse_id.
    """
    return CameraService.get_all_cameras(db, warehouse_id=warehouse_id, skip=skip, limit=limit)

@router.get("/{id}", response_model=CameraResponse)
def get_camera(id: int, db: Session = Depends(get_db)) -> CameraResponse:
    """
    Retrieve camera details by camera ID.
    """
    db_camera = CameraService.get_camera_by_id(db, id)
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Camera with ID {id} not found"
        )
    return db_camera

@router.put("/{id}", response_model=CameraResponse)
def update_camera(id: int, camera: CameraUpdate, db: Session = Depends(get_db)) -> CameraResponse:
    """
    Update camera configurations, including location, name, state, and RTSP stream.
    """
    if camera.warehouse_id is not None:
        # Verify the target warehouse exists
        db_warehouse = WarehouseService.get_warehouse_by_id(db, camera.warehouse_id)
        if not db_warehouse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Warehouse with ID {camera.warehouse_id} does not exist."
            )
            
    db_camera = CameraService.update_camera(db, id, camera)
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Camera with ID {id} not found"
        )
    return db_camera

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(id: int, db: Session = Depends(get_db)) -> None:
    """
    Remove a camera registration from the platform.
    """
    success = CameraService.delete_camera(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Camera with ID {id} not found"
        )
    return
