import httpx
from fastapi import HTTPException

import app.lifespan as _lifespan


def get_http_client() -> httpx.AsyncClient:
    if _lifespan.http_client is None:
        raise HTTPException(status_code=503, detail="HTTP client not available")
    return _lifespan.http_client
