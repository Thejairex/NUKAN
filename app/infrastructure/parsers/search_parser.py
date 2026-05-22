import re
import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from app.domain.entities.search_result import SearchPage, SearchResult
from app.domain.value_objects.pagination import Pagination
from app.core.exceptions import ParseError

logger = logging.getLogger(__name__)

# URL de origen usada solo en mensajes de error.
_SOURCE = "novelupdates/search"

_RATING_RE = re.compile(r"\((\d+\.\d+)\)")


class SearchParser:
    def parse(self, html: str) -> SearchPage:
        soup = BeautifulSoup(html, "lxml")

        boxes = soup.select("div.search_main_box_nu")
        if not boxes:
            title = soup.title.string if soup.title else "sin título"
            snippet = html[:800].replace("\n", " ")
            logger.error("HTML inesperado | title=%r | inicio=%s", title, snippet)
            raise ParseError(_SOURCE, "no se encontraron resultados (div.search_main_box_nu ausente)")

        results = [_parse_box(box) for box in boxes]
        results = [r for r in results if r is not None]

        pagination = _parse_pagination(soup)

        return SearchPage(results=results, pagination=pagination)


def _parse_box(box: Tag) -> SearchResult | None:
    link = box.select_one("div.search_title a")
    if not link or not link.get("href"):
        return None

    url = str(link["href"])
    slug = _slug_from_url(url)
    if not slug:
        return None

    title = link.get_text(strip=True)

    # sid123456 → 123456
    sid_span = box.select_one("div.search_title span[id]")
    series_id = _parse_series_id(str(sid_span["id"])) if sid_span and sid_span.get("id") else 0

    cover_tag = box.select_one("div.search_img_nu img")
    cover_url = str(cover_tag["src"]) if cover_tag and cover_tag.get("src") else None

    ratings_tag = box.select_one("div.search_ratings")
    origin: str | None = None
    rating: float | None = None
    if ratings_tag:
        origin_tag = ratings_tag.select_one("span[class^='org']")
        origin = origin_tag.get_text(strip=True) if origin_tag else None
        raw = ratings_tag.get_text(strip=True)
        match = _RATING_RE.search(raw)
        rating = float(match.group(1)) if match else None

    genres = [a.get_text(strip=True) for a in box.select("div.search_genre a")]

    return SearchResult(
        slug=slug,
        title=title,
        series_id=series_id,
        cover_url=cover_url,
        origin=origin,
        rating=rating,
        genres=genres,
    )


def _parse_pagination(soup: BeautifulSoup) -> Pagination:
    pag = soup.select_one("div.digg_pagination")
    if not pag:
        return Pagination(page=1, has_next=False)

    # Página actual: puede estar en <span class="current"> o inferirse
    current_span = pag.select_one("span.current")
    page = int(current_span.get_text(strip=True)) if current_span else 1

    has_next = pag.select_one("a.next_page") is not None

    return Pagination(page=page, has_next=has_next)


def _slug_from_url(url: str) -> str:
    # https://www.novelupdates.com/series/some-slug/ → "some-slug"
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


def _parse_series_id(sid: str) -> int:
    # "sid136512" → 136512
    digits = sid.lstrip("sid")
    return int(digits) if digits.isdigit() else 0
