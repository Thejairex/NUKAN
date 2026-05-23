import redis.asyncio as aioredis


class RedisCache:
    """Caché Redis. Requiere REDIS_URL configurado en .env."""

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)
