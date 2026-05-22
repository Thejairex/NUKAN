import logging
import time
from typing import Mapping

from playwright.async_api import BrowserContext, Error as PlaywrightError

from app.core.exceptions import FetchError

logger = logging.getLogger(__name__)

_CF_CHALLENGE_TITLE = "just a moment"
_CF_WAIT_TIMEOUT_S = 60       # datacenter IPs necesitan más tiempo
_CF_POLL_INTERVAL_MS = 1_000
_NAV_TIMEOUT_MS = 60_000


class BrowserFetcher:
    """Fetcher basado en Playwright con contexto persistente.

    Usa un BrowserContext compartido para que las cookies de Cloudflare
    (cf_clearance) se conserven entre requests. El challenge CF se resuelve
    una sola vez por arranque del servidor.
    """

    def __init__(self, context: BrowserContext) -> None:
        self._context = context

    async def get_html(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        full_url = _build_url(url, params)
        page = await self._context.new_page()

        try:
            try:
                await page.goto(full_url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
            except PlaywrightError as exc:
                raise FetchError(full_url, f"navigation error: {exc}") from exc

            # Esperar a que el challenge de Cloudflare se resuelva.
            deadline = time.monotonic() + _CF_WAIT_TIMEOUT_S
            while time.monotonic() < deadline:
                title = (await page.title()).lower()
                if _CF_CHALLENGE_TITLE not in title:
                    break
                logger.debug("CF challenge activo en %s, esperando...", full_url)
                await page.wait_for_timeout(_CF_POLL_INTERVAL_MS)
            else:
                raise FetchError(full_url, "Cloudflare challenge no resuelto en tiempo")

            try:
                await page.wait_for_load_state("networkidle", timeout=8_000)
            except PlaywrightError:
                pass

            final_title = await page.title()
            final_url = page.url
            html = await page.content()
            logger.info("BrowserFetcher: title=%r url=%s bytes=%d", final_title, final_url, len(html))
            return html

        finally:
            await page.close()


def _build_url(base: str, params: Mapping[str, str | int] | None) -> str:
    if not params:
        return base
    query = "&".join(f"{k}={v}" for k, v in params.items())
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{query}"
