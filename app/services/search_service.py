import logging

from app.core.constants import NOVELUPDATES_SEARCH_URL
from app.core.exceptions import FetchError, ParseError
from app.domain.entities.search_result import SearchPage
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.parsers.search_parser import SearchParser

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, fetcher: BrowserFetcher, parser: SearchParser) -> None:
        self._fetcher = fetcher
        self._parser = parser

    async def search(self, query: str, page: int = 1) -> SearchPage:
        params: dict[str, str | int] = {"pg": page} if page > 1 else {}

        # La URL base ya incluye ?sf=1&sh= — el query va directo concatenado.
        url = f"{NOVELUPDATES_SEARCH_URL}{query}"

        logger.info("search query=%r page=%d url=%s", query, page, url)

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

        return result
