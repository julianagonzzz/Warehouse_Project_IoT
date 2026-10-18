from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.products.models import ProductEntity
from app.modules.products.schemas import ProductCreate

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, product_in: ProductCreate) -> ProductEntity:
        product = ProductEntity(**product_in.model_dump())
        self.db.add(product)
        self.db.flush()  # Sincroniza estado para obtener ID sin confirmar transacción
        return product

    def get_by_id(self, product_id: int) -> Optional[ProductEntity]:
        return self.db.query(ProductEntity).filter(ProductEntity.id == product_id).first()

    def get_all(self, skip: int, limit: int) -> List[ProductEntity]:
        return self.db.query(ProductEntity).offset(skip).limit(limit).all()