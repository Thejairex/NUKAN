import logging

from app.core.constants import NOVELUPDATES_SEARCH_URL
from app.core.exceptions import FetchError, ParseError
from app.domain.entities.search_result import SearchPage
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.parsers.search_parser import SearchParser
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

_SEARCH_CACHE_KEY = "search:{query}:page:{page}"


class SearchService:
    def __init__(self, fetcher: BrowserFetcher, parser: SearchParser, cache: CacheService) -> None:
        self._fetcher = fetcher
        self._parser = parser
        self._cache = cache

    async def search(self, query: str, page: int = 1, ttl: int = 300) -> SearchPage:
        cache_key = _SEARCH_CACHE_KEY.format(query=query, page=page)

        cached = await self._cache.get(cache_key)
        if cached is not None:
            logger.info("search cache hit query=%r page=%d", query, page)
            return SearchPage.from_dict(cached)

        params: dict[str, str | int] = {"pg": page} if page > 1 else {}
        url = f"{NOVELUPDATES_SEARCH_URL}{query}"

        logger.info("search cache miss query=%r page=%d url=%s", query, page, url)

        try:
            html = await self._fetcher.get_html(url, params=params or None)
        except FetchError:
            logger.exception("fetch falló para query=%r page=%d", query, page)
            raise

        try:
            result = self._parser.parse(html)
        except ParseError:
            logger.exception("parse falló para query=%r page=%d", query, page)
            raise

        await self._cache.set(cache_key, result.to_dict(), ttl)
        return result
