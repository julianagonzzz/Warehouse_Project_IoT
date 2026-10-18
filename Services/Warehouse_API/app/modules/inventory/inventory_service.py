import logging
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.modules.inventory.schemas import MovementCreate
from app.modules.inventory.inventory_repository import InventoryRepository
from app.messaging.rabbitmq_publisher import publish_event

logger = logging.getLogger(__name__)


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InventoryRepository(db)

    def initialize_stock(self, product_id: int) -> None:
        # Método expuesto de forma segura para otros servicios del monolito
        self.repo.initialize_inventory(product_id)

    def get_stock(self, product_id: int):
        inventory = self.repo.get_by_product(product_id)
        if not inventory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventario no encontrado")
        return inventory

    def process_movement(self, movement_in: MovementCreate):
        try:
            # 1. Obtener balance actual bloqueando la fila de manera atómica
            inventory = self.repo.get_by_product_for_update(movement_in.product_id)
            if not inventory:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El inventario no existe")

            new_qty = inventory.quantity
            new_reserved = inventory.reserved_quantity
            m_type = movement_in.type
            qty = movement_in.quantity

            # 2. Evaluación estricta de Reglas de Negocio en Capa de Servicio
            if m_type in ["SHIPMENT", "TRANSFER_OUT"]:
                if new_qty < qty:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Stock insuficiente. Disponible: {new_qty}, Requerido: {qty}"
                    )
                new_qty -= qty

            elif m_type in ["RECEIPT", "TRANSFER_IN", "RETURN"]:
                new_qty += qty

            elif m_type == "RESERVATION":
                if new_qty < qty:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock insuficiente para reservar")
                new_qty -= qty
                new_reserved += qty

            elif m_type == "RELEASE":
                if new_reserved < qty:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Liberación excede reserva existente")
                new_reserved -= qty
                new_qty += qty
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de movimiento inválido")

            # 3. Aplicar mutación y registrar auditoría a través del repositorio
            self.repo.update_stock(inventory, new_qty, new_reserved)
            movement = self.repo.register_movement(movement_in.product_id, m_type, qty, movement_in.reference)
            
            # 4. Control de Transacción centralizado en el Servicio
            self.db.commit()
            self.db.refresh(movement)
        except Exception as e:
            self.db.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        # 5. Publicar el evento DESPUÉS del commit. Si RabbitMQ falla, el movimiento
        #    ya está guardado y no se pierde; solo se registra el error.
        try:
            publish_event({
                "event_id": str(uuid4()),
                "event_type": "INVENTORY_MOVEMENT_CREATED",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "movement_id": movement.id,
                "product_id": movement.product_id,
                "warehouse_id": movement.warehouse_id,
                "movement_type": movement.type,
                "quantity": movement.quantity,
                "reference": movement.reference,
            })
        except Exception:
            logger.exception("No se pudo publicar el evento en RabbitMQ")
        return movement

    def get_movements(self, product_id: int):
        return self.repo.get_movements_by_product(product_id)