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
    # Se selecciona uno al azar en cada arranque del servidor.
    proxy_urls: str = ""


settings = Settings()
