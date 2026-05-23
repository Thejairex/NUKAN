import asyncio
import time
from dataclasses import dataclass


@dataclass
class _Entry:
    value: str
    expires_at: float


class MemoryCache:
    """Caché en memoria con TTL. No es persistente entre reinicios del servidor."""


    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}
        self._lock = asyncio.Lock()

    # Implementación simple: cada entrada tiene un timestamp de expiración, y se verifica al leer.
    async def get(self, key: str) -> str | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    # Al escribir, se calcula el timestamp de expiración sumando el TTL al tiempo actual.
    async def set(self, key: str, value: str, ttl: int) -> None:
        async with self._lock:
            self._store[key] = _Entry(value=value, expires_at=time.monotonic() + ttl)

    # Eliminación simple: se borra la entrada sin importar su estado. No es necesario verificar expiración.
    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)
