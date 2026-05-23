# CLAUDE.md

## Project identity

**Name:** Nukan  
**Type:** Python microservice  
**Purpose:** Read-only unofficial API for NovelUpdates-style metadata, inspired by the role Jikan plays for MyAnimeList.[cite:12][cite:14][cite:20]

Nukan should expose a clean JSON API over public NovelUpdates pages without attempting to replace the source site, mirror its entire catalog, or support authenticated user actions. Jikan is a useful reference here because it focuses on public, non-authenticated, read-only access rather than full platform functionality.[cite:12][cite:14][cite:57]

## Product goal

Build a lightweight metadata provider that Bibliotaku can query for series discovery and enrichment. The service should prioritize low load on the origin, predictable response contracts, and a fast path based on plain HTTP fetching and HTML parsing, with browser automation reserved only for exceptional cases.[cite:14][cite:39][cite:41]

## Core philosophy

- Read-only first.
- Low load over maximum coverage.
- HTTP scraping first, browser fallback second.
- Stable response schemas even when the source markup changes.
- Cache normalized results aggressively.
- Keep business rules in Bibliotaku, not in Nukan.[cite:12][cite:14][cite:49]

## What Nukan is

Nukan is a provider adapter for public metadata such as search results, series details, optional releases, genres, tags, and related recommendations when those fields can be extracted reliably. It exists to give Bibliotaku a stable integration point instead of coupling Laravel directly to source HTML.[cite:14][cite:49]

## What Nukan is not

- Not a full NovelUpdates mirror.
- Not an authenticated client.
- Not a bulk crawler.
- Not a long-term canonical database of all source content.
- Not a browser-first scraping system.
- Not a public unlimited API with unrestricted throughput.[cite:12][cite:14][cite:57]

## Technical direction

### Network layer

Use `httpx.AsyncClient` as the default transport. HTTPX provides async support and is a better fit than per-request synchronous clients when the goal is low-overhead concurrency and connection reuse.[cite:39]

Create one shared async client at application startup and reuse it for the lifespan of the FastAPI app rather than instantiating a new client on every request. FastAPI works well with response models and application-level lifecycle patterns, which helps keep transport and API concerns separated.[cite:49][cite:58][cite:59]

### Parsing layer

Use `BeautifulSoup` with `lxml` as the default parser path. Beautiful Soup does not need native async support for this architecture because the async benefit comes from the HTTP fetch stage, while parsing remains a local CPU-bound step after the response is already in memory.[cite:39]

Selectors must live inside dedicated parser modules instead of route handlers or service classes. Parsing code should validate the presence of minimum required nodes and fail explicitly when a page layout is no longer compatible.

### Browser fallback

Use Playwright only when the required data is not available in the initial HTML or when a route truly depends on JavaScript-rendered content. Playwright’s Python library supports installation through `pip install playwright` followed by `playwright install`, and Chromium alone is enough for the initial fallback strategy.[cite:35][cite:41]

Never default to Playwright for search or normal detail pages unless repeated evidence shows the HTTP path is insufficient. Browser sessions are expensive compared with plain HTTP requests and should remain observable, intentional, and rare.[cite:35][cite:41]

## Architecture rules

1. Keep API, domain contracts, scraping logic, and infrastructure separated.
2. Use thin route handlers and move logic into services.
3. Define explicit interfaces for fetchers, parsers, caches, and scrapers.
4. Return typed response models for every public endpoint.
5. Cache normalized output, not ad hoc fragments.
6. Add retries only for transient network failures.
7. Do not silently swallow parsing failures.
8. Prefer maintainability over clever abstractions.
9. Browser fallback must be opt-in at the scraper level.
10. Every endpoint must have a defined cache policy.[cite:14][cite:39][cite:49]

## Suggested project structure

```text
nukan/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── search.py
│   │       └── series.py
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   └── exceptions.py
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── release.py
│   │   │   ├── search_result.py
│   │   │   └── series.py
│   │   ├── interfaces/
│   │   │   ├── cache.py
│   │   │   ├── fetcher.py
│   │   │   ├── parser.py
│   │   │   └── scraper.py
│   │   └── value_objects/
│   │       └── pagination.py
│   ├── infrastructure/
│   │   ├── cache/
│   │   │   ├── memory_cache.py
│   │   │   └── redis_cache.py
│   │   ├── fetchers/
│   │   │   ├── browser_fetcher.py
│   │   │   └── http_fetcher.py
│   │   ├── parsers/
│   │   │   ├── release_parser.py
│   │   │   ├── search_parser.py
│   │   │   └── series_parser.py
│   │   └── scrapers/
│   │       └── novelupdates_scraper.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── search.py
│   │   └── series.py
│   ├── services/
│   │   ├── cache_service.py
│   │   ├── search_service.py
│   │   └── series_service.py
│   ├── lifespan.py
│   └── main.py
├── pyproject.toml
├── .env.example
└── CLAUDE.md
```

This structure keeps HTML acquisition, parsing, schema normalization, and API exposure independent enough to evolve without turning the project into a tangled scraper script.[cite:49]

## Core interfaces

### Fetcher

```python
from typing import Mapping, Protocol

class Fetcher(Protocol):
    async def get_html(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str: ...
```

### Parser

```python
from typing import Generic, Protocol, TypeVar

T = TypeVar("T")

class Parser(Protocol, Generic[T]):
    def parse(self, html: str) -> T: ...
```

### Cache repository

```python
from typing import Protocol

class CacheRepository(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int) -> None: ...
    async def delete(self, key: str) -> None: ...
```

### Source scraper

```python
from typing import Protocol

class NovelSourceScraper(Protocol):
    async def search(self, query: str, page: int = 1): ...
    async def get_series(self, slug: str): ...
```

These contracts make it easy to keep an HTTP-first implementation while still allowing a controlled browser fallback path behind the same abstraction.[cite:35][cite:39][cite:41]

## Recommended dependencies

### Runtime

- `fastapi`
- `uvicorn[standard]`
- `httpx`
- `beautifulsoup4`
- `lxml`
- `pydantic`
- `pydantic-settings`
- `playwright`
- `orjson`
- `tenacity`
- `redis` optional

### Development

- `ruff`
- `mypy`
- `asgi-lifespan` optional

### Install

```bash
pip install fastapi uvicorn[standard] httpx beautifulsoup4 lxml pydantic pydantic-settings playwright orjson tenacity redis ruff mypy asgi-lifespan
playwright install chromium
```

Playwright requires a second installation step to download browser binaries, and Chromium is enough for the initial fallback setup.[cite:35][cite:41]

## Endpoint design

### MVP

- `GET /health`
- `GET /search?query=<text>&page=1`
- `GET /series/{slug}`

### Optional later endpoints

- `GET /series/{slug}/releases`
- `GET /series/{slug}/recommendations`
- `GET /genres`
- `GET /tags`

Each endpoint must be read-only and return stable response models rather than raw scraped fragments. FastAPI’s response model system is a good fit for enforcing that contract.[cite:49][cite:58]

## Cache policy

- Cache normalized JSON results.
- Use per-endpoint TTLs.
- Keep longer TTLs for slow-changing resources like series details.
- Keep shorter TTLs for releases or frequently updated lists.
- Prefer stale-while-revalidate patterns where possible.
- Avoid cache bypass unless explicitly requested for debugging.[cite:57]

## Error policy

- Distinguish fetch failures from parse failures.
- Return clean API errors instead of leaking internal stack traces.
- Raise explicit domain exceptions for unsupported or broken source pages.
- Log route, source URL, cache status, fallback usage, and failure type.
- Never return partial success silently when required fields are missing.

## Performance rules

- Keep concurrency intentionally low.
- Reuse one `httpx.AsyncClient`.
- Avoid recursive discovery.
- Never crawl the full source catalog.
- Prefer direct page access over broad pagination sweeps.
- Track Playwright usage rate; it should remain a minority path.[cite:39][cite:41]

## Coding conventions

- Use full type hints.
- Prefer Protocols for boundaries.
- Keep classes focused.
- Keep functions small and explicit.
- Do not put selectors in routes.
- Do not embed parsing logic in schemas.
- Do not mix cache serialization with parsing logic.
- Use Pydantic models at the API boundary.[cite:49]

## Integration contract with Bibliotaku

Nukan is an external provider for Bibliotaku. It should return generic, source-oriented metadata, while Bibliotaku remains responsible for mapping that data into the application domain. In particular, PHP-side enums such as `MediaType` and `MediaStatus` should stay in the Laravel app, not in the Python microservice, so the service remains reusable and domain-light.

Suggested Laravel-side shape:

```text
app/Domain/Metadata/Providers/NovelUpdatesProvider.php
app/Domain/Metadata/DTOs/
app/Domain/Media/Enums/MediaType.php
app/Domain/Media/Enums/MediaStatus.php
```

## Non-goals

- No account login flows.
- No write operations.
- No full dataset persistence.
- No public unlimited scraping gateway.
- No browser-first architecture.
- No coupling of Laravel business rules into Python.[cite:12][cite:14][cite:57]

## Definition of done

A feature is done when:

- It uses the HTTP path first.
- It has a typed response model.
- It has a defined cache policy.
- It logs failures clearly.
- It does not leak source HTML details.
- It is safe for Bibliotaku to consume as a stable provider contract.[cite:39][cite:49]

## First milestones

1. Bootstrap FastAPI app and shared HTTPX client lifecycle.
2. Implement `GET /health`.
3. Implement `HttpFetcher`.
4. Implement `SearchParser`.
5. Ship `GET /search`.
6. Add cache.
7. Implement `SeriesParser`.
8. Ship `GET /series/{slug}`.
9. Add Playwright fallback only if a validated case requires it.[cite:39][cite:41][cite:49]

## Estado de implementación

### Milestone 1 — Completado ✓
Bootstrap de la app, cliente HTTP compartido y `GET /health`.

Archivos creados/modificados:
- `pyproject.toml` — metadata del proyecto + config de ruff y mypy.
- `.env.example` — variables de entorno disponibles (copiar a `.env` para desarrollo).
- `app/core/config.py` — `Settings` (pydantic-settings); se carga desde `.env` automáticamente. Variables: `app_env`, `log_level`, `http_timeout`, `cache_*_ttl`, `redis_url`.
- `app/core/constants.py` — URLs base de NovelUpdates y `DEFAULT_HEADERS` con User-Agent de navegador real.
- `app/core/exceptions.py` — jerarquía de excepciones: `NukanError` → `FetchError`, `ParseError`, `SeriesNotFoundError`.
- `app/domain/interfaces/fetcher.py` — `Fetcher` Protocol (renombrado desde `fetchet.py`, ahora `async`).
- `app/lifespan.py` — crea un único `httpx.AsyncClient` al arrancar la app y lo cierra al detenerla. El cliente vive en `app.lifespan.http_client`.
- `app/api/deps.py` — `get_http_client()`: función de inyección de dependencias FastAPI que expone el cliente compartido a las rutas.
- `app/main.py` — instancia FastAPI con lifespan, registra routers.
- `app/api/routes/health.py` — `GET /health` → `{"status": "ok", "version": "0.1.0"}`.

### Milestone 2 — Completado ✓
`HttpFetcher`: implementación concreta del protocolo `Fetcher`.

- `app/infrastructure/fetchers/http_fetcher.py` — `HttpFetcher` recibe un `httpx.AsyncClient` en el constructor (inyectado, nunca lo crea él mismo). Lógica:
  - Reintenta automáticamente hasta 3 veces con backoff exponencial (1 s → 8 s) en `TimeoutException` y `NetworkError` via `tenacity`.
  - Convierte errores de red y status no exitosos en `FetchError` con la URL y el motivo, para que las capas superiores puedan loguear y manejar sin conocer httpx.
  - Status 429/5xx son retryable; 404 y 403 se propagan directamente sin reintentar.
- `app/api/deps.py` — se agregó `get_fetcher()`: toma el `AsyncClient` vía `Depends(get_http_client)` y devuelve un `HttpFetcher` listo. Las rutas lo reciben con `Depends(get_fetcher)`.

### Hallazgo crítico — Cloudflare + proxy residencial obligatorio en producción
NovelUpdates protege **todas** sus páginas con Cloudflare Managed Challenge (JS). `httpx` recibe 403 en todas las URLs. El 200 que devuelve `/series/{slug}` sin autenticar es una página vacía por defecto del servidor, no contenido real.

**Cloudflare en IPs de datacenter nunca resuelve el challenge automáticamente** aunque se use Playwright con stealth. Requiere proxy residencial. En desarrollo local (IP residencial) Playwright pasa el challenge sin proxy.

### Milestone 3 — Completado ✓
`BrowserFetcher`: fetcher principal basado en Playwright con contexto persistente y proxy residencial.

- `app/lifespan.py` — gestiona tres recursos: `http_client` (httpx), `browser` (Playwright Chromium), `browser_context` (contexto persistente). Arquitectura clave:
  - `Stealth().hook_playwright_context(_playwright)` — aplica 20+ patches de fingerprinting (WebGL, plugins, chrome runtime, permissions) a nivel del playwright instance antes de lanzar el browser.
  - `browser_context` es **persistente** (no se recrea por request). Las cookies `cf_clearance` que emite Cloudflare al resolver el challenge se conservan entre requests. El challenge se enfrenta solo una vez por arranque del servidor.
  - `_pick_proxy()` — selecciona al azar uno de los proxies de `PROXY_URLS` y lo pasa al contexto. Loguea `host:port` sin credenciales.
- `app/infrastructure/fetchers/browser_fetcher.py` — recibe el `BrowserContext` compartido (no el `Browser`). Por request abre una `Page` nueva dentro del contexto persistente y la cierra al terminar. Espera hasta 60 s a que el título deje de ser "Just a moment…".
- `app/api/deps.py` — `get_fetcher()` devuelve `BrowserFetcher(context)`. `get_http_fetcher()` devuelve `HttpFetcher` para casos sin CF.
- `requirements.txt` — agregado `playwright-stealth==2.0.3`.

### Proxy residencial — configuración
Sin proxy, Cloudflare bloquea permanentemente las IPs de datacenter (VPS, cloud). Con IP residencial (desarrollo local) funciona sin proxy.

Variable de entorno `PROXY_URLS`: lista de proxies separados por coma, formato `http://user:pass@host:port`. Se elige uno al azar en cada arranque. En desarrollo se puede dejar vacío.

### Milestone 4 — Completado ✓
`SearchParser` + `GET /search`.

- `app/domain/value_objects/pagination.py` — `Pagination(page, has_next)` dataclass frozen.
- `app/domain/entities/search_result.py` — `SearchResult(slug, title, series_id, cover_url, origin, rating, genres)` y `SearchPage(results, pagination)`.
- `app/infrastructure/parsers/search_parser.py` — `SearchParser.parse(html) -> SearchPage`. Selectores clave:
  - Resultados: `div.search_main_box_nu` (25 por página).
  - Slug: extraído del `href` del link (`/series/<slug>/`).
  - Series ID: atributo `id` del span adyacente al título (`sid136512` → `136512`).
  - Origin/rating: `div.search_ratings` contiene `<span class="orgcn">CN</span>(4.5)` — origin del span, rating con regex `\((\d+\.\d+)\)`.
  - Géneros: `div.search_genre a`.
  - Paginación: `div.digg_pagination` → `span.current` para página actual, `a.next_page` para `has_next`.
- `app/schemas/common.py` — `PaginationSchema`.
- `app/schemas/search.py` — `SearchResultSchema`, `SearchResponseSchema`.
- `app/services/search_service.py` — `SearchService` orquesta fetcher + parser. Construye la URL como `NOVELUPDATES_SEARCH_URL + query` y agrega `pg=N` solo si `page > 1`.
- `app/api/routes/search.py` — `GET /search?query=&page=1`. Convierte `FetchError`/`ParseError` en HTTP 502. El mapeo dominio→schema ocurre en la ruta.
- `app/main.py` — registrado `search.router`.

### Milestone 5 — Completado ✓
Capa de caché con soporte dual memoria/Redis.

**Arquitectura de caché:**
- `app/domain/interfaces/cache.py` — `CacheRepository` Protocol: `get`, `set`, `delete`. Permite intercambiar implementaciones sin tocar los servicios.
- `app/infrastructure/cache/memory_cache.py` — `MemoryCache`: dict en memoria con TTL calculado con `time.monotonic()`. Usa `asyncio.Lock` para thread-safety. No persiste entre reinicios. Default cuando `REDIS_URL` está vacío.
- `app/infrastructure/cache/redis_cache.py` — `RedisCache`: wrapper sobre `redis.asyncio`. El cliente Redis se inicializa en `lifespan.py` y se inyecta; no lo crea la caché misma.
- `app/services/cache_service.py` — `CacheService`: serializa/deserializa con `orjson` antes de guardar en el repositorio. Las capas superiores entregan objetos Python, no strings.

**Integración en lifespan:**
En `app/lifespan.py` se decide qué implementación usar al arrancar:
```python
if settings.redis_url:
    _redis_client = aioredis.from_url(settings.redis_url)
    cache = RedisCache(_redis_client)
else:
    cache = MemoryCache()
```
El cliente Redis se cierra explícitamente en shutdown con `await _redis_client.aclose()`.

**Integración en SearchService:**
`SearchService` recibe `CacheService` por constructor. Antes de fetch comprueba caché con clave `search:{query}:page:{page}`. Si hay hit retorna sin tocar el browser. Si hay miss, fetchea, parsea, guarda con `ttl=settings.cache_search_ttl` (por defecto 300 s).

**Serialización de entidades de dominio:**
`SearchResult` y `SearchPage` tienen métodos `to_dict()` / `from_dict()`. Esto mantiene la lógica de serialización en la entidad, sin acoplar `CacheService` a los tipos concretos del dominio.

**Inyección de dependencias:**
`app/api/deps.py` expone `get_cache_repo()` y `get_cache()`. La ruta pide `get_cache` vía `Depends` y lo pasa al servicio.

**TTLs configurables:**
- `CACHE_SEARCH_TTL` (default 300 s) — resultados de búsqueda.
- `CACHE_SERIES_TTL` (default 3600 s) — detalles de serie (Milestone 6).
- `CACHE_DEFAULT_TTL` (default 300 s) — fallback genérico.

### Próximos milestones
- **Milestone 6**: `SeriesParser` + `GET /series/{slug}`.

## Comandos de desarrollo

```bash
# Activar entorno virtual (PowerShell)
venv\Scripts\Activate.ps1

# Levantar servidor de desarrollo (recarga automática)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Linting
ruff check app/

# Formateo
ruff format app/

# Type checking
mypy app/
```

## Docker

La imagen incluye Python 3.13-slim + Chromium de Playwright. Pesa ~900 MB por los binarios del navegador.

```bash
# Construir
docker build -t nukan .

# Correr (pasar variables de entorno con --env-file)
docker run --rm -p 8000:8000 --env-file .env nukan
```

**Decisiones de diseño del Dockerfile:**
- `PLAYWRIGHT_BROWSERS_PATH=/opt/playwright` — Playwright instala Chromium en `~/.cache/ms-playwright` por defecto, lo que lo deja en `/root/.cache` si se instala como root y lo hace inaccesible al usuario sin privilegios. Fijar esta variable mueve los binarios a `/opt/playwright`, que luego se hace legible (`chmod 755`) para todos.
- Usuario `appuser` sin privilegios — el proceso uvicorn corre sin root.
- `--workers 1` — con un solo worker no hay problemas de estado compartido (`http_client` global en `lifespan.py`). Si se escala a múltiples workers se debe revisar la gestión del cliente.
- `requirements.txt` se copia antes que el código para aprovechar el cache de capas de Docker.

**Archivos de dependencias:**
- `requirements.txt` — solo runtime (lo que va a producción).
- `requirements-dev.txt` — runtime + `ruff`, `mypy`, `asgi-lifespan` para desarrollo local.

## Instructions for Claude

When generating code for Nukan:

- Prioritize clarity over speed of writing.
- Prefer the simplest architecture that preserves boundaries.
- Keep transport, parsing, cache, and API layers separated.
- Assume the consumer is Bibliotaku, a Laravel 13 app with typed enums and clean provider boundaries.
- Optimize for low source load and long-term maintainability.
- Treat Playwright as a tool of exception, not the default path.
