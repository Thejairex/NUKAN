class NukanError(Exception):
    """Base para todos los errores del dominio."""


class FetchError(NukanError):
    """Falló la obtención del HTML desde la fuente (red, timeout, status != 2xx)."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Fetch failed for {url!r}: {reason}")


class ParseError(NukanError):
    """El HTML obtenido no tiene la estructura esperada."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Parse failed for {url!r}: {reason}")


class SeriesNotFoundError(NukanError):
    """El slug solicitado no existe en la fuente."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Series not found: {slug!r}")
