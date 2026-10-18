from typing import List
from fastapi import APIRouter, Depends, status
from app.database import get_db
from sqlalchemy.orm import Session
from app.modules.inventory.schemas import MovementCreate, MovementResponse, InventoryResponse
from app.modules.inventory.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("/{product_id}", response_model=InventoryResponse)
def get_inventory(product_id: int, db: Session = Depends(get_db)):
    service = InventoryService(db)
    return service.get_stock(product_id)

@router.post("/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(payload: MovementCreate, db: Session = Depends(get_db)):
    service = InventoryService(db)
    # El controlador solo delega y responde. No maneja commits ni fallas transaccionales de DB.
    return service.process_movement(payload)

@router.get("/{product_id}/movements", response_model=List[MovementResponse])
def get_movements(product_id: int, db: Session = Depends(get_db)):
    service = InventoryService(db)
    return service.get_movements(product_id)