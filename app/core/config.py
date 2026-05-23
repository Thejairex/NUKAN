from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    http_timeout: float = 10.0

    cache_default_ttl: int = 300
    cache_series_ttl: int = 3600
    cache_search_ttl: int = 300

    redis_url: str = ""

    # Lista de proxies residenciales separados por coma.
    # Formato de cada entrada: http://user:pass@host:port
    # Se priorizan sobre los proxies públicos.
    proxy_urls: str = ""

    # URL opcional para obtener proxies públicos en JSON (formato proxyscrape v3).
    # Si está vacío, solo se usan los de proxy_urls.
    proxyscrape_url: str = ""

    # Reintentos máximos rotando proxy ante fallo (CF challenge o error de red).
    proxy_max_retries: int = 4


settings = Settings()
