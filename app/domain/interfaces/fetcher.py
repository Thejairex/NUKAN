from typing import Mapping, Protocol


class Fetcher(Protocol):
    async def get_html(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str: ...
