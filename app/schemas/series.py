from pydantic import BaseModel


class SeriesSchema(BaseModel):
    slug: str
    title: str
    cover_url: str | None
    series_type: str | None
    original_language: str | None
    status: str | None
    year: int | None
    description: str | None
    authors: list[str]
    artists: list[str]
    genres: list[str]
    tags: list[str]
    rating: float | None
    rating_votes: int | None
