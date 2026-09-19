"""Shared fixtures for database integration tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from enact.platform.database.session import (
    SessionManager,
    create_database_engine,
    create_session_factory,
)
from sqlalchemy import make_url
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope='session')
def postgres_database_url() -> Generator[str]:
    """Provide an asyncpg URL for a disposable PostgreSQL database."""
    with PostgresContainer('postgres:17-alpine') as postgres:
        url = make_url(postgres.get_connection_url()).set(drivername='postgresql+asyncpg')
        yield url.render_as_string(hide_password=False)


@pytest_asyncio.fixture
async def session_manager(
    postgres_database_url: str,
) -> AsyncGenerator[SessionManager]:
    """Provide isolated database session infrastructure."""
    engine = create_database_engine(postgres_database_url)
    manager = SessionManager(engine, create_session_factory(engine))

    try:
        yield manager
    finally:
        await manager.dispose()
