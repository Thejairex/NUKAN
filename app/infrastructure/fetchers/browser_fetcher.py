import logging
import time
from typing import Mapping

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
)

from app.core.constants import DEFAULT_HEADERS
from app.core.exceptions import FetchError
from app.infrastructure.proxy.proxy_rotator import ProxyRotator

logger = logging.getLogger(__name__)

_CF_CHALLENGE_TITLE = "just a moment"
_CF_WAIT_TIMEOUT_S = 25
_CF_POLL_INTERVAL_MS = 1_000
_NAV_TIMEOUT_MS = 30_000


class BrowserFetcher:
    """Fetcher Playwright con rotación de proxies.

    Crea un BrowserContext nuevo por intento. Si Cloudflare no se resuelve
    o el proxy da error de red, marca el proxy como muerto y prueba el
    siguiente del pool hasta agotar `max_retries`.
    """

    def __init__(
        self,
        browser: Browser,
        rotator: ProxyRotator,
        max_retries: int = 4,
    ) -> None:
        self._browser = browser
        self._rotator = rotator
        self._max_retries = max_retries

    async def get_html(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        full_url = _build_url(url, params)
        last_error = "sin intentos realizados"
        tried: set[str] = set()

        for attempt in range(1, self._max_retries + 1):
            proxy = self._rotator.acquire(exclude=tried)
            if proxy is None:
                raise FetchError(
                    full_url, f"pool de proxies agotado tras {attempt - 1} intentos"
                )
            tried.add(proxy["server"])

            logger.info(
                "fetch %s — intento %d/%d via %s",
                full_url,
                attempt,
                self._max_retries,
                proxy["server"],
            )

            try:
                html = await self._try_once(full_url, proxy)
                logger.info("fetch OK via %s (%d bytes)", proxy["server"], len(html))
                self._rotator.mark_alive(proxy)
                return html
            except _AttemptFailed as exc:
                last_error = exc.reason
                logger.info("fetch falló via %s: %s", proxy["server"], exc.reason)
                self._rotator.mark_dead(proxy)
                continue

        raise FetchError(full_url, f"todos los proxies fallaron: {last_error}")

    async def _try_once(self, full_url: str, proxy: dict[str, str]) -> str:
        context: BrowserContext | None = None
        try:
            context = await self._browser.new_context(
                user_agent=DEFAULT_HEADERS["User-Agent"],
                locale="en-US",
                timezone_id="America/New_York",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={"Accept-Language": DEFAULT_HEADERS["Accept-Language"]},
                proxy=proxy,
            )
            page = await context.new_page()

            try:
                await page.goto(
                    full_url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS
                )
            except PlaywrightError as exc:
                raise _AttemptFailed(f"navigation error: {exc}") from exc

            if not await _wait_for_cloudflare(page):
                raise _AttemptFailed("Cloudflare challenge no resuelto en tiempo")

            try:
                await page.wait_for_load_state("networkidle", timeout=8_000)
            except PlaywrightError:
                pass

            return await page.content()
        finally:
            if context is not None:
                try:
                    await context.close()
                except PlaywrightError:
                    pass


class _AttemptFailed(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


async def _wait_for_cloudflare(page: Page) -> bool:
    deadline = time.monotonic() + _CF_WAIT_TIMEOUT_S
    while time.monotonic() < deadline:
        try:
            title = (await page.title()).lower()
        except PlaywrightError:
            return False
        if _CF_CHALLENGE_TITLE not in title:
            return True
        await page.wait_for_timeout(_CF_POLL_INTERVAL_MS)
    return False


def _build_url(base: str, params: Mapping[str, str | int] | None) -> str:
    if not params:
        return base
    query = "&".join(f"{k}={v}" for k, v in params.items())
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{query}"
