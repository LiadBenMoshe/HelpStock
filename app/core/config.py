from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HelpStock"
    environment: str = "development"
    log_level: str = "INFO"
    cache_ttl_seconds: int = 300
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])

    finnhub_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    newsapi_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
