import logging
import re

from bs4 import BeautifulSoup

from app.core.exceptions import ParseError, SeriesNotFoundError
from app.domain.entities.series import Series

logger = logging.getLogger(__name__)

_SOURCE = "novelupdates/series"
_RATING_RE = re.compile(r"\((\d+\.\d+)\s*/\s*\d+\.\d+,\s*(\d+)\s*votes?\)", re.IGNORECASE)
_STATUS_RE = re.compile(r"\(([^)]+)\)\s*$")


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
        if status_div:
            raw_status = status_div.get_text(strip=True)
            m = _STATUS_RE.search(raw_status)
            status = m.group(1).strip() if m else raw_status or None

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

        logger.info(
            "SeriesParser: slug=%r title=%r genres=%d tags=%d",
            slug, title, len(genres), len(tags),
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
        )
