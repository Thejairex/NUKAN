import logging
import re

from bs4 import BeautifulSoup

from app.core.exceptions import ParseError, SeriesNotFoundError
from app.domain.entities.series import Series

logger = logging.getLogger(__name__)

_SOURCE = "novelupdates/series"
_RATING_RE = re.compile(r"\((\d+\.\d+)\s*/\s*\d+\.\d+,\s*(\d+)\s*votes?\)", re.IGNORECASE)
_STATUS_RE = re.compile(r"\(([^)]+)\)\s*$")
_VOLUMES_RE = re.compile(r"(\d+)\s*Volumes?", re.IGNORECASE)

# Filas que muestra NovelUpdates por página en la tabla de releases.
_RELEASES_PER_PAGE = 15


class SeriesParser:
    def parse(self, html: str, slug: str) -> Series:
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.select_one("div.seriestitlenu")
        if not title_tag:
            title = soup.title.string if soup.title else "sin título"
            snippet = html[:500].replace("\n", " ")
            logger.error("Serie no encontrada | title=%r | inicio=%s", title, snippet)
            raise SeriesNotFoundError(slug)

        title = title_tag.get_text(strip=True)

        cover_tag = soup.select_one("div.seriesimg img")
        cover_url = str(cover_tag["src"]) if cover_tag and cover_tag.get("src") else None

        type_tag = soup.select_one("div#showtype a")
        series_type = type_tag.get_text(strip=True) if type_tag else None

        lang_tag = soup.select_one("div#showlang a")
        original_language = lang_tag.get_text(strip=True) if lang_tag else None

        status_div = soup.select_one("div#editstatus")
        status: str | None = None
        volume_count: int | None = None
        if status_div:
            raw_status = status_div.get_text(strip=True)
            m = _STATUS_RE.search(raw_status)
            status = m.group(1).strip() if m else raw_status or None
            mv = _VOLUMES_RE.search(raw_status)
            if mv:
                volume_count = int(mv.group(1))

        year_div = soup.select_one("div#edityear")
        year: int | None = None
        if year_div:
            raw_year = year_div.get_text(strip=True)
            year = int(raw_year) if raw_year.isdigit() else None

        desc_div = soup.select_one("div#editdescription")
        description: str | None = None
        if desc_div:
            description = desc_div.get_text(separator="\n", strip=True) or None

        authors = [a.get_text(strip=True) for a in soup.select("div#showauthors a")]
        artists = [a.get_text(strip=True) for a in soup.select("div#showartists a")]
        genres = [a.get_text(strip=True) for a in soup.select("div#seriesgenre a")]
        tags = [a.get_text(strip=True) for a in soup.select("div#showtags a")]

        rating: float | None = None
        rating_votes: int | None = None
        uvotes = soup.select_one("span.uvotes")
        if uvotes:
            m2 = _RATING_RE.search(uvotes.get_text())
            if m2:
                rating = float(m2.group(1))
                rating_votes = int(m2.group(2))

        chapter_count = _count_releases(soup)

        logger.info(
            "SeriesParser: slug=%r title=%r chapters=%s genres=%d tags=%d",
            slug, title, chapter_count, len(genres), len(tags),
        )

        return Series(
            slug=slug,
            title=title,
            cover_url=cover_url,
            series_type=series_type,
            original_language=original_language,
            status=status,
            year=year,
            description=description,
            authors=authors,
            artists=artists,
            genres=genres,
            tags=tags,
            rating=rating,
            rating_votes=rating_votes,
            chapter_count=chapter_count,
            volume_count=volume_count,
        )


def _count_releases(soup: BeautifulSoup) -> int | None:
    """Cuenta las releases traducidas desde table#myTable.

    Si la tabla tiene una sola página, el conteo es exacto.
    Si tiene varias páginas, se estima como (last_page - 1) * 15 + rows_page_1.
    La última página puede tener < 15 filas, así que el resultado puede
    sobrestimar en hasta 14 unidades.
    """
    tbl = soup.select_one("table#myTable")
    if tbl is None:
        return None

    rows = tbl.select("tr")
    data_rows = max(len(rows) - 1, 0)  # descontar fila de encabezado

    pag = tbl.find_next_sibling("div", class_="digg_pagination")
    if pag is None:
        return data_rows

    last_page = _last_page(pag)
    if last_page <= 1:
        return data_rows

    return (last_page - 1) * _RELEASES_PER_PAGE + data_rows


def _last_page(pag_div: BeautifulSoup) -> int:
    """Extrae el número de la última página de un div.digg_pagination."""
    links = [a for a in pag_div.select("a") if "next_page" not in (a.get("class") or [])]
    if not links:
        return 1
    href = links[-1].get("href", "")
    m = re.search(r"pg=(\d+)", href)
    return int(m.group(1)) if m else 1
