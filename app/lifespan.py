import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright
from playwright_stealth import Stealth

from app.core.config import settings
from app.core.constants import DEFAULT_HEADERS

logger = logging.getLogger(__name__)

# Recursos compartidos — inicializados en startup, liberados en shutdown.
http_client: httpx.AsyncClient | None = None
browser: Browser | None = None
browser_context: BrowserContext | None = None
_playwright: Playwright | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global http_client, browser, browser_context, _playwright

    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
    )

    _playwright = await async_playwright().start()
    # Stealth parchea los métodos de lanzamiento del playwright instance
    # para que todo browser/context creado desde acá tenga los patches aplicados.
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

    # Contexto persistente: las cookies de Cloudflare (cf_clearance) se conservan
    # entre requests. El challenge solo se resuelve una vez por arranque del servidor.
    browser_context = await browser.new_context(
        user_agent=DEFAULT_HEADERS["User-Agent"],
        locale="en-US",
        timezone_id="America/New_York",
        viewport={"width": 1920, "height": 1080},
        extra_http_headers={"Accept-Language": DEFAULT_HEADERS["Accept-Language"]},
    )
    logger.info("Playwright browser y contexto persistente iniciados")

    yield

    await browser_context.close()
    await browser.close()
    await _playwright.stop()
    logger.info("Playwright detenido")

    await http_client.aclose()
    http_client = None
    browser = None
    browser_context = None
    _playwright = None
