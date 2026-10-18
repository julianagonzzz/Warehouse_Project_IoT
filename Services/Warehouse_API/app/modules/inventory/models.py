import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base
from app.modules.shared.utils import schemas_utils

class InventoryEntity(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, unique=True, nullable=False) # Desacoplado de FK fuerte si se prefiere, o apuntado directo
    warehouse_id = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    updated_at = Column(DateTime, default=schemas_utils.current_utc_time, onupdate=schemas_utils.current_utc_time)

class InventoryMovementEntity(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    warehouse_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    reference = Column(String)
    created_at = Column(DateTime, default=schemas_utils.current_utc_time)