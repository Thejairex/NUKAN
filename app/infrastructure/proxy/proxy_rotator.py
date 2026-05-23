import logging
import random
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class ProxyRotator:
    """Pool de proxies con dos orígenes: env (prioritario) y lista pública remota.

    `acquire()` devuelve un proxy aleatorio, prefiriendo siempre los de env
    mientras quede al menos uno vivo. `mark_dead()` lo excluye hasta que
    `reset_dead()` lo reincorpore.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        env_raw: str,
        proxyscrape_url: str,
    ) -> None:
        self._http = http_client
        self._env_raw = env_raw
        self._proxyscrape_url = proxyscrape_url.strip()
        self._env_pool: list[dict[str, str]] = []
        self._public_pool: list[dict[str, str]] = []
        self._dead: set[str] = set()
        # Último proxy con éxito — se prueba primero en futuras requests.
        self._preferred: dict[str, str] | None = None

    @property
    def alive_count(self) -> int:
        return sum(
            1
            for p in (*self._env_pool, *self._public_pool)
            if p["server"] not in self._dead
        )

    async def initialize(self) -> None:
        self._env_pool = self._parse_list(self._env_raw.split(","))
        logger.info("ProxyRotator: %d proxies de env", len(self._env_pool))

        if self._proxyscrape_url:
            await self._refresh_public()

        if not self._env_pool and not self._public_pool:
            logger.warning("ProxyRotator: pool vacío — todas las requests fallarán")

    async def _refresh_public(self) -> None:
        try:
            resp = await self._http.get(self._proxyscrape_url, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("proxyscrape fetch falló: %s", exc)
            return

        raw_urls: list[str] = []
        if isinstance(data, dict):
            for entry in data.get("proxies", []):
                if isinstance(entry, dict):
                    url = entry.get("proxy")
                    if isinstance(url, str):
                        raw_urls.append(url)

        self._public_pool = self._parse_list(raw_urls)
        logger.info("ProxyRotator: %d proxies públicos de proxyscrape", len(self._public_pool))

    @staticmethod
    def _parse_list(raw: list[str]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for r in raw:
            r = r.strip()
            if not r:
                continue
            try:
                parsed = urlparse(r)
            except ValueError:
                continue
            if not parsed.hostname or not parsed.port or not parsed.scheme:
                continue
            proxy: dict[str, str] = {
                "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            }
            if parsed.username:
                proxy["username"] = parsed.username
                proxy["password"] = parsed.password or ""
            out.append(proxy)
        return out

    def acquire(self, exclude: set[str] | None = None) -> dict[str, str] | None:
        skip = self._dead | (exclude or set())

        if self._preferred and self._preferred["server"] not in skip:
            return self._preferred

        for source in (self._env_pool, self._public_pool):
            candidates = [p for p in source if p["server"] not in skip]
            if candidates:
                return random.choice(candidates)
        return None

    def mark_alive(self, proxy: dict[str, str]) -> None:
        if self._preferred is None or self._preferred["server"] != proxy["server"]:
            logger.info("Proxy preferido actualizado: %s", proxy["server"])
        self._preferred = proxy

    def mark_dead(self, proxy: dict[str, str]) -> None:
        self._dead.add(proxy["server"])
        if self._preferred and self._preferred["server"] == proxy["server"]:
            self._preferred = None
        logger.info(
            "Proxy descartado: %s (vivos: %d)", proxy["server"], self.alive_count
        )

    def reset_dead(self) -> None:
        self._dead.clear()
