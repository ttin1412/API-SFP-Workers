"""Environment-backed application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings shared by the worker components."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    host: str = "0.0.0.0"
    port: int = Field(default=8081, ge=1, le=65535)

    gcp_project_id: str = ""
    firestore_database_id: str = "(default)"
    gcs_bucket_name: str = ""
    quarantine_prefix: str = "quarantine/"
    trusted_prefix: str = "trusted/"

    max_file_size: int = Field(default=52_428_800, gt=0)
    max_archive_extracted_size: int = Field(default=209_715_200, gt=0)
    max_archive_files: int = Field(default=1_000, gt=0)
    max_archive_nesting_depth: int = Field(default=3, ge=0)

    clamav_host: str = "localhost"
    clamav_port: int = Field(default=3310, ge=1, le=65535)


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-in-practice settings object per process."""
    return Settings()
