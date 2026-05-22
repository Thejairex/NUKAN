import httpx
from fastapi import Depends, HTTPException
from playwright.async_api import Browser

import app.lifespan as _lifespan
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.fetchers.http_fetcher import HttpFetcher


def get_http_client() -> httpx.AsyncClient:
    if _lifespan.http_client is None:
        raise HTTPException(status_code=503, detail="HTTP client not available")
    return _lifespan.http_client


def get_browser() -> Browser:
    if _lifespan.browser is None:
        raise HTTPException(status_code=503, detail="Browser not available")
    return _lifespan.browser


def get_fetcher(browser: Browser = Depends(get_browser)) -> BrowserFetcher:
    """Fetcher principal — usa Playwright para superar el challenge de Cloudflare."""
    return BrowserFetcher(browser)


def get_http_fetcher(client: httpx.AsyncClient = Depends(get_http_client)) -> HttpFetcher:
    """Fetcher HTTP liviano, para endpoints sin Cloudflare."""
    return HttpFetcher(client)
