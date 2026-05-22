import httpx
from fastapi import Depends, HTTPException
from playwright.async_api import BrowserContext

import app.lifespan as _lifespan
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.fetchers.http_fetcher import HttpFetcher


def get_http_client() -> httpx.AsyncClient:
    if _lifespan.http_client is None:
        raise HTTPException(status_code=503, detail="HTTP client not available")
    return _lifespan.http_client


def get_browser_context() -> BrowserContext:
    if _lifespan.browser_context is None:
        raise HTTPException(status_code=503, detail="Browser context not available")
    return _lifespan.browser_context


def get_fetcher(context: BrowserContext = Depends(get_browser_context)) -> BrowserFetcher:
    """Fetcher principal — contexto persistente con cookies CF entre requests."""
    return BrowserFetcher(context)


def get_http_fetcher(client: httpx.AsyncClient = Depends(get_http_client)) -> HttpFetcher:
    """Fetcher HTTP liviano, para endpoints sin Cloudflare."""
    return HttpFetcher(client)
