from dataclasses import dataclass, field
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "series_id": self.series_id,
            "cover_url": self.cover_url,
            "origin": self.origin,
            "rating": self.rating,
            "genres": list(self.genres),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SearchResult":
        return cls(
            slug=d["slug"],
            title=d["title"],
            series_id=d["series_id"],
            cover_url=d.get("cover_url"),
            origin=d.get("origin"),
            rating=d.get("rating"),
            genres=d.get("genres", []),
        )


@dataclass(frozen=True)
class SearchPage:
    results: list[SearchResult]
    pagination: Pagination

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "pagination": {"page": self.pagination.page, "has_next": self.pagination.has_next},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SearchPage":
        pag = d["pagination"]
        return cls(
            results=[SearchResult.from_dict(r) for r in d["results"]],
            pagination=Pagination(page=pag["page"], has_next=pag["has_next"]),
        )
