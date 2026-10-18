import logging
from typing import Optional

import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Timeouts: si Redis no responde, se prefiere ir rápido a PostgreSQL
# en lugar de dejar el request esperando.
_client = redis.Redis.from_url(
    settings.REDIS_URL,
    socket_connect_timeout=0.5,
    socket_timeout=0.5,
    decode_responses=True,
)


def inventory_key(product_id: int) -> str:
    return f"warehouse:{settings.WAREHOUSE_ID}:inventory:{product_id}"


def cache_get(key: str) -> Optional[str]:
    """Devuelve el valor guardado, o None si no existe o si Redis está caído."""
    if not settings.CACHE_ENABLED:
        return None
    try:
        return _client.get(key)
    except redis.RedisError:
        logger.warning("Redis no disponible al leer %s; se usa PostgreSQL", key)
        return None


def cache_set(key: str, value: str) -> None:
    """Guarda el valor con TTL. Si Redis falla, solo se registra el error."""
    if not settings.CACHE_ENABLED:
        return
    try:
        _client.set(key, value, ex=settings.CACHE_TTL_SECONDS)
    except redis.RedisError:
        logger.warning("Redis no disponible al escribir %s", key)


def cache_delete(key: str) -> None:
    """Invalidación explícita. Se llama después de modificar PostgreSQL."""
    if not settings.CACHE_ENABLED:
        return
    try:
        _client.delete(key)
    except redis.RedisError:
        # Si no se pudo borrar, el TTL limita cuánto dura el dato obsoleto.
        logger.warning("Redis no disponible al invalidar %s", key)
