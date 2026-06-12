from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class WarehouseBase(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the warehouse")
    location: str = Field(..., max_length=255, description="Location of the warehouse")
    description: Optional[str] = Field(None, description="Description or notes about the warehouse")

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Name of the warehouse")
    location: Optional[str] = Field(None, max_length=255, description="Location of the warehouse")
    description: Optional[str] = Field(None, description="Description or notes about the warehouse")

class WarehouseResponse(WarehouseBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
