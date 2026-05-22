import logging
from typing import Mapping

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.exceptions import FetchError

logger = logging.getLogger(__name__)

# Reintentar solo en errores de red o 429/5xx, no en 404 o 403.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, FetchError):
        # FetchError producido por status HTTP retryable
        return exc.reason.startswith("HTTP ")
    return isinstance(exc, (httpx.TimeoutException, httpx.NetworkError))


class HttpFetcher:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def get_html(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        try:
            response = await self._client.get(url, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            logger.warning("timeout fetching %s", url)
            raise FetchError(url, f"timeout: {exc}") from exc
        except httpx.NetworkError as exc:
            logger.warning("network error fetching %s: %s", url, exc)
            raise FetchError(url, f"network error: {exc}") from exc

        if response.status_code in _RETRYABLE_STATUS:
            logger.warning("retryable status %s for %s", response.status_code, url)
            raise FetchError(url, f"HTTP {response.status_code}")

        if response.status_code == 404:
            raise FetchError(url, "HTTP 404")

        if not response.is_success:
            raise FetchError(url, f"HTTP {response.status_code}")

        logger.debug("fetched %s (%d bytes)", url, len(response.content))
        return response.text
