"""Typed application configuration loaded from the environment."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import AnyHttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class DatabaseSettings(BaseSettings):
    """Validated database configuration shared by API and migration processes."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='ENACT_DATABASE_',
        extra='ignore',
    )

    host: str = 'localhost'
    username: str = 'enact_app'
    password: SecretStr
    port: int = 5432
    name: str = 'enact'
    ssl_mode: Literal['disable', 'require'] = 'disable'

    @property
    def database_url(self) -> str:
        """Build the async SQLAlchemy database URL.

        Returns:
            A URL containing the configured PostgreSQL connection and transport parameters.
        """
        query = {'ssl': 'require'} if self.ssl_mode == 'require' else {}
        url = URL.create(
            drivername='postgresql+asyncpg',
            username=self.username,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.name,
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


class Settings(BaseSettings):
    """Validated configuration for the Enact API process."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='ENACT_',
        extra='ignore',
    )

    environment: Literal['development', 'testing', 'production'] = 'development'
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    api_url: AnyHttpUrl = AnyHttpUrl('http://localhost:8000')
    database: DatabaseSettings
    object_storage: ObjectStorageSettings

    @model_validator(mode='after')
    def require_database_tls_in_production(self) -> Self:
        """Reject production application configuration without database transport security."""
        if self.environment == 'production' and self.database.ssl_mode != 'require':
            msg = 'database SSL mode must be require in production'
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Load and cache the process configuration.

    Returns:
        The validated application settings.

    Raises:
        pydantic.ValidationError: If required configuration is missing or invalid.
    """
    # BaseSettings supplies required fields from environment sources at runtime.
    database = DatabaseSettings()  # pyright: ignore[reportCallIssue]
    object_storage = ObjectStorageSettings()  # pyright: ignore[reportCallIssue]
    return Settings(  # pyright: ignore[reportCallIssue]
        database=database,
        object_storage=object_storage,
    )
