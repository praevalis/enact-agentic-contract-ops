"""Typed application configuration loaded from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Validated configuration for the Enact API process."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='ENACT_',
        extra='ignore',
    )

    environment: Literal['development', 'testing', 'production'] = 'development'
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    database_host: str = 'localhost'
    database_username: str = 'enact_app'
    database_password: SecretStr
    database_port: int = 5432
    database_name: str = 'enact'
    api_url: AnyHttpUrl = AnyHttpUrl('http://localhost:8000')

    @property
    def database_url(self) -> str:
        """Build the async SQLAlchemy database URL.

        Returns:
            A URL containing the configured PostgreSQL connection parameters and mandatory
            transport encryption in production.
        """
        query = {'ssl': 'require'} if self.environment == 'production' else {}
        url = URL.create(
            drivername='postgresql+asyncpg',
            username=self.database_username,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
            query=query,
        )
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    """Load and cache the process configuration.

    Returns:
        The validated application settings.

    Raises:
        pydantic.ValidationError: If required configuration is missing or invalid.
    """
    # BaseSettings supplies required fields from environment sources at runtime.
    return Settings()  # pyright: ignore[reportCallIssue]
