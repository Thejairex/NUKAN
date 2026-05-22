from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI

from app.core.config import settings
from app.core.constants import DEFAULT_HEADERS


# El cliente compartido vive aquí; deps.py lo expone a las rutas.
http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global http_client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
    )
    yield
    await http_client.aclose()
    http_client = None
