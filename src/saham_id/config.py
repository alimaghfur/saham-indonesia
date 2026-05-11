"""Centralized configuration loaded from environment variables.

All settings live in one place so each module stays source-agnostic.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global config, populated from `.env` or process environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Data source preferences ---
    data_sources: str = Field(
        default="yahoo,rti",
        alias="SAHAM_ID_DATA_SOURCES",
        description="Comma-separated fallback chain.",
    )

    # --- API keys ---
    itick_api_key: str = Field(default="", alias="ITICK_API_KEY")
    goapi_api_key: str = Field(default="", alias="GOAPI_API_KEY")
    sectors_api_key: str = Field(default="", alias="SECTORS_API_KEY")

    # --- Scraper politeness ---
    rti_rate_limit_per_min: int = Field(default=30, alias="SAHAM_ID_RTI_RATE_LIMIT_PER_MIN")

    # --- Local paths ---
    cache_dir: Path = Field(default=Path("./data/cache"), alias="SAHAM_ID_CACHE_DIR")
    log_level: str = Field(default="INFO", alias="SAHAM_ID_LOG_LEVEL")

    # --- Cache settings ---
    cache_enabled: bool = Field(default=True, alias="SAHAM_ID_CACHE_ENABLED")
    cache_memory_maxsize: int = Field(default=1024, alias="SAHAM_ID_CACHE_MEMORY_MAXSIZE")
    cache_default_ttl: int = Field(default=300, alias="SAHAM_ID_CACHE_DEFAULT_TTL")
    cache_disk_enabled: bool = Field(default=True, alias="SAHAM_ID_CACHE_DISK_ENABLED")

    # --- Retry settings ---
    retry_max_attempts: int = Field(default=3, alias="SAHAM_ID_RETRY_MAX_ATTEMPTS")
    retry_min_wait: float = Field(default=1.0, alias="SAHAM_ID_RETRY_MIN_WAIT")
    retry_max_wait: float = Field(default=30.0, alias="SAHAM_ID_RETRY_MAX_WAIT")

    @property
    def data_source_chain(self) -> list[str]:
        return [s.strip().lower() for s in self.data_sources.split(",") if s.strip()]


settings = Settings()
