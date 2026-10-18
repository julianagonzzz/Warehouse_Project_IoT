from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: str

class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    category: Optional[str]
    unit: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True