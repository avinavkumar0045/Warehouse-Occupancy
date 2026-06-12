from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(warehouse: WarehouseCreate, db: Session = Depends(get_db)) -> WarehouseResponse:
    """
    Register a new warehouse in the platform.
    """
    return WarehouseService.create_warehouse(db, warehouse)

@router.get("", response_model=List[WarehouseResponse])
def get_warehouses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[WarehouseResponse]:
    """
    Retrieve all registered warehouses.
    """
    return WarehouseService.get_all_warehouses(db, skip=skip, limit=limit)

@router.get("/{id}", response_model=WarehouseResponse)
def get_warehouse(id: int, db: Session = Depends(get_db)) -> WarehouseResponse:
    """
    Get a single warehouse's details by ID.
    """
    db_warehouse = WarehouseService.get_warehouse_by_id(db, id)
    if not db_warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Warehouse with ID {id} not found"
        )
    return db_warehouse

@router.put("/{id}", response_model=WarehouseResponse)
def update_warehouse(id: int, warehouse: WarehouseUpdate, db: Session = Depends(get_db)) -> WarehouseResponse:
    """
    Update details of an existing warehouse.
    """
    db_warehouse = WarehouseService.update_warehouse(db, id, warehouse)
    if not db_warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Warehouse with ID {id} not found"
        )
    return db_warehouse

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a warehouse. (Note: cascade options will automatically delete associated cameras and readings).
    """
    success = WarehouseService.delete_warehouse(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Warehouse with ID {id} not found"
        )
    return
