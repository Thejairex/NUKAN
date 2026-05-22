import logging
import time
from typing import Mapping

from playwright.async_api import Browser, Error as PlaywrightError

from app.core.constants import DEFAULT_HEADERS
from app.core.exceptions import FetchError

logger = logging.getLogger(__name__)

_CF_CHALLENGE_TITLE = "just a moment"
_CF_WAIT_TIMEOUT_S = 30       # máximo tiempo esperando que Cloudflare resuelva
_CF_POLL_INTERVAL_MS = 1_000  # cada cuánto revisamos si el challenge terminó
_NAV_TIMEOUT_MS = 30_000 # timeout para la navegación inicial (incluye resolver el challenge)


class BrowserFetcher:
    """Fetcher basado en Playwright. Cada llamada abre una página nueva
    dentro del browser compartido y la cierra al terminar."""

    def __init__(self, browser: Browser) -> None:
        self._browser = browser

    async def get_html(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        full_url = _build_url(url, params)

        context = await self._browser.new_context(
            user_agent=DEFAULT_HEADERS["User-Agent"],
            locale="en-US",
            timezone_id="America/New_York",
            viewport={"width": 1920, "height": 1080},
            # navigator.webdriver = false
            extra_http_headers={"Accept-Language": DEFAULT_HEADERS["Accept-Language"]},
        )
        # Ocultar la huella de automatización antes de navegar.
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = await context.new_page()
        try:
            try:
                await page.goto(full_url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
            except PlaywrightError as exc:
                raise FetchError(full_url, f"navigation error: {exc}") from exc

            # Esperar a que el challenge de Cloudflare se resuelva, si aparece.
            deadline = time.monotonic() + _CF_WAIT_TIMEOUT_S
            while time.monotonic() < deadline:
                title = (await page.title()).lower()
                if _CF_CHALLENGE_TITLE not in title:
                    break
                logger.debug("CF challenge activo en %s, esperando...", full_url)
                await page.wait_for_timeout(_CF_POLL_INTERVAL_MS)
            else:
                raise FetchError(full_url, "Cloudflare challenge no resuelto en tiempo")

            # Breve pausa para que el JS post-challenge termine de renderizar.
            try:
                await page.wait_for_load_state("networkidle", timeout=8_000)
            except PlaywrightError:
                # networkidle puede no ocurrir en páginas con polling; no es fatal.
                pass

            html = await page.content()
            logger.debug("BrowserFetcher: %s (%d bytes)", full_url, len(html))
            return html

        finally:
            await page.close()
            await context.close()


def _build_url(base: str, params: Mapping[str, str | int] | None) -> str:
    if not params:
        return base
    query = "&".join(f"{k}={v}" for k, v in params.items())
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{query}"
