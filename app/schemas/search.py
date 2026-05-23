from pydantic import BaseModel

from app.schemas.common import PaginationSchema


class SearchResultSchema(BaseModel):
    slug: str
    title: str
    series_id: int
    cover_url: str | None
    origin: str | None
    rating: float | None
    series_url: str | None
    genres: list[str]
    chapter_count: int | None


class SearchResponseSchema(BaseModel):
    query: str
    results: list[SearchResultSchema]
    pagination: PaginationSchema
