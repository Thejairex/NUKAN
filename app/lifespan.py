import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from playwright.async_api import Browser, Playwright, async_playwright

from app.core.config import settings
from app.core.constants import DEFAULT_HEADERS

logger = logging.getLogger(__name__)

# Recursos compartidos — inicializados en startup, liberados en shutdown.
http_client: httpx.AsyncClient | None = None
browser: Browser | None = None
_playwright: Playwright | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global http_client, browser, _playwright

    # Cliente HTTP liviano para requests sin Cloudflare (health checks, futuros endpoints).
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
    )

    # Browser Playwright: único proceso Chromium compartido por toda la app.
    # Se lanza con flags anti-detección para pasar el challenge de Cloudflare.
    _playwright = await async_playwright().start()
    browser = await _playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",  # necesario en Docker (shared memory limitada)
            "--disable-gpu",
        ],
    )
    logger.info("Playwright browser started")

    yield

    await browser.close()
    await _playwright.stop()
    logger.info("Playwright browser stopped")

    await http_client.aclose()
    http_client = None
    browser = None
    _playwright = None
