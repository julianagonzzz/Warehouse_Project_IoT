from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MovementCreate(BaseModel):
    product_id: int
    type: str = Field(..., description="RECEIPT, SHIPMENT, ADJUSTMENT, RESERVATION, RELEASE")
    quantity: int = Field(..., gt=0)
    reference: Optional[str] = None

class MovementResponse(BaseModel):
    id: int
    product_id: int
    warehouse_id: str
    type: str
    quantity: int
    reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryResponse(BaseModel):
    product_id: int
    warehouse_id: str
    quantity: int
    reserved_quantity: int
    updated_at: datetime

    class Config:
        from_attributes = True