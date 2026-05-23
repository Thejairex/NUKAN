from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Series:
    slug: str
    title: str
    cover_url: str | None
    series_type: str | None      # "Web Novel", "Light Novel", etc.
    original_language: str | None
    status: str | None           # "Complete", "Ongoing", etc.
    year: int | None
    description: str | None
    authors: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    rating: float | None = None
    rating_votes: int | None = None
    chapter_count: int | None = None
    volume_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "cover_url": self.cover_url,
            "series_type": self.series_type,
            "original_language": self.original_language,
            "status": self.status,
            "year": self.year,
            "description": self.description,
            "authors": list(self.authors),
            "artists": list(self.artists),
            "genres": list(self.genres),
            "tags": list(self.tags),
            "rating": self.rating,
            "rating_votes": self.rating_votes,
            "chapter_count": self.chapter_count,
            "volume_count": self.volume_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Series":
        return cls(
            slug=d["slug"],
            title=d["title"],
            cover_url=d.get("cover_url"),
            series_type=d.get("series_type"),
            original_language=d.get("original_language"),
            status=d.get("status"),
            year=d.get("year"),
            description=d.get("description"),
            authors=d.get("authors", []),
            artists=d.get("artists", []),
            genres=d.get("genres", []),
            tags=d.get("tags", []),
            rating=d.get("rating"),
            rating_votes=d.get("rating_votes"),
            chapter_count=d.get("chapter_count"),
            volume_count=d.get("volume_count"),
        )
