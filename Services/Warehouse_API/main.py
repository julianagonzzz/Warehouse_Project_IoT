import logging
from fastapi import FastAPI
from app.database import engine, Base
from app.modules.health.health_controller import router as health_controller
from app.modules.products.products_controller import router as products_controller
from app.modules.inventory.inventory_controller import router as inventory_controller

logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Warehouse Cloud Platform — Refactored Modular Monolith",
    description="Fase 1 Corregida: Arquitectura limpia sin fugas transaccionales ni acoplamiento cruzado.",
    version="1.1.0"
)

app.include_router(health_controller)
app.include_router(products_controller)
app.include_router(inventory_controller)