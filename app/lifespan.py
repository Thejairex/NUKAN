import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI
from playwright.async_api import Browser, Playwright, async_playwright
from playwright_stealth import Stealth

from app.core.config import settings
from app.core.constants import DEFAULT_HEADERS
from app.domain.interfaces.cache import CacheRepository
from app.infrastructure.cache.memory_cache import MemoryCache
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.proxy.proxy_rotator import ProxyRotator

logger = logging.getLogger(__name__)

# Recursos compartidos — inicializados en startup, liberados en shutdown.
http_client: httpx.AsyncClient | None = None
browser: Browser | None = None
proxy_rotator: ProxyRotator | None = None
_playwright: Playwright | None = None
cache: CacheRepository | None = None
_redis_client: aioredis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global http_client, browser, proxy_rotator, _playwright, cache, _redis_client

    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
    )

    proxy_rotator = ProxyRotator(
        http_client=http_client,
        env_raw=settings.proxy_urls,
        proxyscrape_url=settings.proxyscrape_url,
    )
    await proxy_rotator.initialize()

    _playwright = await async_playwright().start()
    Stealth().hook_playwright_context(_playwright)
    browser = await _playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
        ],
    )
    logger.info("Playwright browser iniciado (contexto por request via rotator)")

    if settings.redis_url:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=False)
        cache = RedisCache(_redis_client)
        logger.info("Caché: Redis (%s)", settings.redis_url)
    else:
        cache = MemoryCache()
        logger.info("Caché: memoria (sin persistencia entre reinicios)")

    yield

    await browser.close()
    await _playwright.stop()
    logger.info("Playwright detenido")

    if _redis_client is not None:
        await _redis_client.aclose()

    await http_client.aclose()
    http_client = None
    browser = None
    proxy_rotator = None
    _playwright = None
    cache = None
    _redis_client = None
