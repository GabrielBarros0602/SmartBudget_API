"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration.

    Values are read from the process environment first, then from `.env`.
    Unknown keys are ignored so a shared `.env` can hold extra tooling vars.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SmartBudget API"
    environment: str = "development"
    version: str = "0.1.0"
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Exposed as a FastAPI dependency so tests can override it via
    `app.dependency_overrides[get_settings]`.
    """
    return Settings()
