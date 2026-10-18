from typing import List
from fastapi import APIRouter, Depends, status
from app.database import get_db
from sqlalchemy.orm import Session
from app.modules.products.schemas import ProductCreate, ProductResponse
from app.modules.products.products_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    service = ProductService(db)
    return service.create_product_with_inventory(payload)

@router.get("", response_model=List[ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = ProductService(db)
    return service.list_products(skip, limit)

@router.get("/{id}", response_model=ProductResponse)
def get_product(id: int, db: Session = Depends(get_db)):
    service = ProductService(db)
    return service.get_product(id)