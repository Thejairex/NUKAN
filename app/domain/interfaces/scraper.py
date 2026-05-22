# app/domain/interfaces/scraper.py
from typing import Protocol
from app.domain.entities.search_result import SearchPage
from app.domain.entities.series import SeriesDetails

class NovelSourceScraper(Protocol):
    async def search(self, query: str, page: int = 1) -> SearchPage: ...
    async def get_series(self, slug: str) -> SeriesDetails: ...