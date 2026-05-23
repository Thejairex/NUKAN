import httpx
from fastapi import Depends, HTTPException
from playwright.async_api import Browser

import app.lifespan as _lifespan
from app.core.config import settings
from app.domain.interfaces.cache import CacheRepository
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.fetchers.http_fetcher import HttpFetcher
from app.infrastructure.proxy.proxy_rotator import ProxyRotator
from app.services.cache_service import CacheService


def get_http_client() -> httpx.AsyncClient:
    if _lifespan.http_client is None:
        raise HTTPException(status_code=503, detail="HTTP client not available")
    return _lifespan.http_client


def get_browser() -> Browser:
    if _lifespan.browser is None:
        raise HTTPException(status_code=503, detail="Browser not available")
    return _lifespan.browser


def get_proxy_rotator() -> ProxyRotator:
    if _lifespan.proxy_rotator is None:
        raise HTTPException(status_code=503, detail="Proxy rotator not available")
    return _lifespan.proxy_rotator


def get_fetcher(
    browser: Browser = Depends(get_browser),
    rotator: ProxyRotator = Depends(get_proxy_rotator),
) -> BrowserFetcher:
    """Fetcher principal — rota proxy por intento ante fallo de CF o red."""
    return BrowserFetcher(browser, rotator, max_retries=settings.proxy_max_retries)


def get_http_fetcher(client: httpx.AsyncClient = Depends(get_http_client)) -> HttpFetcher:
    """Fetcher HTTP liviano, para endpoints sin Cloudflare."""
    return HttpFetcher(client)


def get_cache_repo() -> CacheRepository:
    if _lifespan.cache is None:
        raise HTTPException(status_code=503, detail="Cache not available")
    return _lifespan.cache


def get_cache(repo: CacheRepository = Depends(get_cache_repo)) -> CacheService:
    return CacheService(repo)
