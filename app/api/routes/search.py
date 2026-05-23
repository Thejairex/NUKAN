import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_cache, get_fetcher
from app.core.config import settings
from app.core.exceptions import FetchError, ParseError
from app.infrastructure.fetchers.browser_fetcher import BrowserFetcher
from app.infrastructure.parsers.search_parser import SearchParser
from app.schemas.common import PaginationSchema
from app.schemas.search import SearchResponseSchema, SearchResultSchema
from app.services.cache_service import CacheService
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])


def _get_search_service(
    fetcher: BrowserFetcher = Depends(get_fetcher),
    cache: CacheService = Depends(get_cache),
) -> SearchService:
    return SearchService(fetcher=fetcher, parser=SearchParser(), cache=cache)


@router.get("/search", response_model=SearchResponseSchema)
async def search(
    query: str = Query(..., min_length=1, description="Texto a buscar"),
    page: int = Query(1, ge=1, description="Número de página"),
    service: SearchService = Depends(_get_search_service),
) -> SearchResponseSchema:
    try:
        result = await service.search(query=query, page=page, ttl=settings.cache_search_ttl)
    except FetchError as exc:
        logger.error("FetchError en /search: %s", exc)
        raise HTTPException(status_code=502, detail="Error al obtener datos de la fuente")
    except ParseError as exc:
        logger.error("ParseError en /search: %s", exc)
        raise HTTPException(status_code=502, detail="Error al procesar la respuesta de la fuente")

    return SearchResponseSchema(
        query=query,
        results=[
            SearchResultSchema(
                slug=r.slug,
                title=r.title,
                series_id=r.series_id,
                cover_url=r.cover_url,
                origin=r.origin,
                rating=r.rating,
                genres=r.genres,
            )
            for r in result.results
        ],
        pagination=PaginationSchema(
            page=result.pagination.page,
            has_next=result.pagination.has_next,
        ),
    )
