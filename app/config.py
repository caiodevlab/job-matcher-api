"""
Configurações da aplicação.
Carregadas via variáveis de ambiente / .env usando Pydantic Settings.
"""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações globais da API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Job Matcher API"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = ""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/jobmatcher",
        description="Async connection string",
    )

    # CORS
    cors_origins: List[str] = ["*"]

    # Scraper
    scraper_timeout_seconds: int = 30
    scraper_user_agent: str = "JobMatcherBot/0.1 (+https://github.com/caiodevlab/job-matcher-api)"
    scraper_min_interval_minutes: int = 30  # anti-duplicação

    # Ranking
    ranker_exact_weight: int = 3
    ranker_partial_weight: int = 1
    ranker_level_weight: int = 2
    ranker_area_weight: int = 2

    ranker_high_threshold: int = 15
    ranker_medium_threshold: int = 8
    ranker_low_threshold: int = 3

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, v):
        """Aceita string separada por vírgula e transforma em lista."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Singleton de settings — cacheado para evitar releitura do .env."""
    return Settings()
