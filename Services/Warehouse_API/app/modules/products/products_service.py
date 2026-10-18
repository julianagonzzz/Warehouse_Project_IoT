from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.modules.products.schemas import ProductCreate
# CORRECCIÓN: Dependencia limpia hacia el SERVICE del módulo vecino, no a su repositorio privado
from app.modules.inventory.inventory_service import InventoryService
from app.modules.products.products_repository import ProductRepository

class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.inventory_service = InventoryService(db)

    def create_product_with_inventory(self, product_in: ProductCreate):
        try:
            # 1. Crear la entidad Producto
            product = self.product_repo.create(product_in)
            
            # 2. Delegar de forma segura la inicialización de stock al servicio de inventario
            self.inventory_service.initialize_stock(product.id)
            
            # 3. Confirmar ciclo transaccional unificado
            self.db.commit()
            return product
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en orquestación atómica de producto: {str(e)}"
            )

    def get_product(self, product_id: int):
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        return product

    def list_products(self, skip: int, limit: int):
        return self.product_repo.get_all(skip, limit)