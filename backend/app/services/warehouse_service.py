from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate

logger = logging.getLogger(__name__)

class WarehouseService:
    """
    CRUD services for Warehouse management.
    """

    @staticmethod
    def create_warehouse(db: Session, schema: WarehouseCreate) -> Warehouse:
        logger.info(f"Creating a new warehouse: {schema.name}")
        db_obj = Warehouse(
            name=schema.name,
            location=schema.location,
            description=schema.description
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_warehouse_by_id(db: Session, warehouse_id: int) -> Optional[Warehouse]:
        logger.info(f"Fetching warehouse with id: {warehouse_id}")
        return db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()

    @staticmethod
    def get_all_warehouses(db: Session, skip: int = 0, limit: int = 100) -> List[Warehouse]:
        logger.info("Fetching all warehouses")
        return db.query(Warehouse).offset(skip).limit(limit).all()

    @staticmethod
    def update_warehouse(db: Session, warehouse_id: int, schema: WarehouseUpdate) -> Optional[Warehouse]:
        logger.info(f"Updating warehouse with id: {warehouse_id}")
        db_obj = WarehouseService.get_warehouse_by_id(db, warehouse_id)
        if not db_obj:
            logger.warning(f"Warehouse with id {warehouse_id} not found for update")
            return None
        
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
            
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete_warehouse(db: Session, warehouse_id: int) -> bool:
        logger.info(f"Deleting warehouse with id: {warehouse_id}")
        db_obj = WarehouseService.get_warehouse_by_id(db, warehouse_id)
        if not db_obj:
            logger.warning(f"Warehouse with id {warehouse_id} not found for deletion")
            return False
        db.delete(db_obj)
        db.commit()
        return True
