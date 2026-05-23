import logging

from app.core.constants import NOVELUPDATES_SERIES_URL
from app.core.exceptions import FetchError, ParseError, SeriesNotFoundError
from app.domain.entities.series import Series
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.parsers.series_parser import SeriesParser
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

_SERIES_CACHE_KEY = "series:{slug}"


class SeriesService:
    def __init__(self, fetcher: BrowserFetcher, parser: SeriesParser, cache: CacheService) -> None:
        self._fetcher = fetcher
        self._parser = parser
        self._cache = cache

    async def get_series(self, slug: str, ttl: int = 3600) -> Series:
        cache_key = _SERIES_CACHE_KEY.format(slug=slug)

        cached = await self._cache.get(cache_key)
        if cached is not None:
            logger.info("series cache hit slug=%r", slug)
            return Series.from_dict(cached)

        url = f"{NOVELUPDATES_SERIES_URL}{slug}/"
        logger.info("series cache miss slug=%r url=%s", slug, url)

        try:
            html = await self._fetcher.get_html(url)
        except FetchError:
            logger.exception("fetch falló para slug=%r", slug)
            raise

        try:
            series = self._parser.parse(html, slug=slug)
        except (ParseError, SeriesNotFoundError):
            logger.exception("parse falló para slug=%r", slug)
            raise

        await self._cache.set(cache_key, series.to_dict(), ttl)
        return series
