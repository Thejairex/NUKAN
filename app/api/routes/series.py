import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_cache, get_fetcher
from app.core.config import settings
from app.core.exceptions import FetchError, ParseError, SeriesNotFoundError
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.parsers.series_parser import SeriesParser
from app.schemas.series import SeriesSchema
from app.services.cache_service import CacheService
from app.services.series_service import SeriesService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["series"])


def _get_series_service(
    fetcher: BrowserFetcher = Depends(get_fetcher),
    cache: CacheService = Depends(get_cache),
) -> SeriesService:
    return SeriesService(fetcher=fetcher, parser=SeriesParser(), cache=cache)


@router.get("/series/{slug}", response_model=SeriesSchema)
async def get_series(
    slug: str,
    service: SeriesService = Depends(_get_series_service),
) -> SeriesSchema:
    try:
        series = await service.get_series(slug=slug, ttl=settings.cache_series_ttl)
    except SeriesNotFoundError:
        raise HTTPException(status_code=404, detail=f"Serie '{slug}' no encontrada")
    except FetchError as exc:
        logger.error("FetchError en /series/%s: %s", slug, exc)
        raise HTTPException(status_code=502, detail="Error al obtener datos de la fuente")
    except ParseError as exc:
        logger.error("ParseError en /series/%s: %s", slug, exc)
        raise HTTPException(status_code=502, detail="Error al procesar la respuesta de la fuente")

    return SeriesSchema(
        slug=series.slug,
        title=series.title,
        cover_url=series.cover_url,
        series_type=series.series_type,
        original_language=series.original_language,
        status=series.status,
        year=series.year,
        description=series.description,
        authors=series.authors,
        artists=series.artists,
        genres=series.genres,
        tags=series.tags,
        rating=series.rating,
        rating_votes=series.rating_votes,
    )
