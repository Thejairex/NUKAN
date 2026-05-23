import logging
from typing import Any

import orjson

from app.domain.interfaces.cache import CacheRepository

logger = logging.getLogger(__name__)


class CacheService:
    """Serialización JSON sobre CacheRepository.

    Las capas superiores trabajan con objetos Python; esta clase se encarga
    de serializar con orjson antes de guardar y deserializar al leer.
    """

    def __init__(self, repo: CacheRepository) -> None:
        self._repo = repo

    async def get(self, key: str) -> Any | None:
        raw = await self._repo.get(key)
        if raw is None:
            return None
        try:
            return orjson.loads(raw)
        except orjson.JSONDecodeError:
            logger.warning("Cache hit inválido para key=%r — descartado", key)
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        raw = orjson.dumps(value)
        await self._repo.set(key, raw.decode(), ttl)

    async def delete(self, key: str) -> None:
        await self._repo.delete(key)
