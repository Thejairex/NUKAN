from dataclasses import dataclass, field

from app.domain.value_objects.pagination import Pagination


@dataclass(frozen=True)
class SearchResult:
    slug: str
    title: str
    series_id: int
    cover_url: str | None
    origin: str | None       # "CN" | "JP" | "KR" | …
    rating: float | None
    genres: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchPage:
    results: list[SearchResult]
    pagination: Pagination
