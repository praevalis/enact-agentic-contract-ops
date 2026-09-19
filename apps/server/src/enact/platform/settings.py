"""Typed application configuration loaded from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class DatabaseSettings(BaseSettings):
    """Validated database configuration shared by API and migration processes."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='ENACT_',
        extra='ignore',
    )

    environment: Literal['development', 'testing', 'production'] = 'development'
    database_host: str = 'localhost'
    database_username: str = 'enact_app'
    database_password: SecretStr
    database_port: int = 5432
    database_name: str = 'enact'

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


class ObjectStorageSettings(BaseSettings):
    """Validated configuration for the S3-compatible object-storage boundary."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='ENACT_OBJECT_STORAGE_',
        extra='ignore',
    )

    endpoint_url: AnyHttpUrl = AnyHttpUrl('http://localhost:9000')
    access_key: SecretStr
    secret_key: SecretStr
    bucket: str = 'enact-documents'
    region: str = 'us-east-1'


class Settings(DatabaseSettings):
    """Validated configuration for the Enact API process."""

    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    api_url: AnyHttpUrl = AnyHttpUrl('http://localhost:8000')
    object_storage: ObjectStorageSettings


@lru_cache
def get_settings() -> Settings:
    """Load and cache the process configuration.

    Returns:
        The validated application settings.

    Raises:
        pydantic.ValidationError: If required configuration is missing or invalid.
    """
    # BaseSettings supplies required fields from environment sources at runtime.
    object_storage = ObjectStorageSettings()  # pyright: ignore[reportCallIssue]
    return Settings(object_storage=object_storage)  # pyright: ignore[reportCallIssue]
