"""Shared fixtures for database integration tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from alembic.migration import MigrationContext
from alembic.operations import Operations
from enact.platform.database.migrations import enable_tenant_rls
from enact.platform.database.session import (
    SessionManager,
    create_database_engine,
    create_session_factory,
)
from sqlalchemy import Connection, make_url, text
from testcontainers.community.postgres import PostgresContainer

APP_PASSWORD = 'test-app-only'


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


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def rls_database_urls(postgres_database_url: str) -> tuple[str, str]:
    """Provision test-only tenant tables and return admin and application URLs."""
    engine = create_database_engine(postgres_database_url)

    try:
        async with engine.begin() as connection:
            await connection.execute(text('CREATE ROLE enact_owner NOLOGIN'))
            await connection.execute(
                text(
                    'CREATE ROLE enact_app LOGIN NOINHERIT NOSUPERUSER NOCREATEDB '
                    "NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'test-app-only'"
                )
            )
            await connection.execute(text('CREATE SCHEMA enact AUTHORIZATION enact_owner'))
            await connection.execute(text('GRANT USAGE ON SCHEMA enact TO enact_app'))
            await connection.execute(text('SET LOCAL ROLE enact_owner'))
            await connection.execute(
                text(
                    'CREATE TABLE enact.rls_test_parents ('
                    'organization_id uuid NOT NULL, '
                    'id uuid NOT NULL, '
                    'value text NOT NULL, '
                    'CONSTRAINT pk_rls_test_parents PRIMARY KEY (organization_id, id)'
                    ')'
                )
            )
            await connection.execute(
                text(
                    'CREATE TABLE enact.rls_test_children ('
                    'organization_id uuid NOT NULL, '
                    'id uuid NOT NULL, '
                    'parent_id uuid NOT NULL, '
                    'value text NOT NULL, '
                    'CONSTRAINT pk_rls_test_children PRIMARY KEY (organization_id, id), '
                    'CONSTRAINT fk_rls_test_children_parent '
                    'FOREIGN KEY (organization_id, parent_id) '
                    'REFERENCES enact.rls_test_parents (organization_id, id)'
                    ')'
                )
            )
            await connection.run_sync(_enable_test_table_rls)
            await connection.execute(
                text(
                    'GRANT SELECT, INSERT, UPDATE, DELETE '
                    'ON enact.rls_test_parents, enact.rls_test_children TO enact_app'
                )
            )
    finally:
        await engine.dispose()

    app_url = make_url(postgres_database_url).set(
        username='enact_app',
        password=APP_PASSWORD,
    )
    return postgres_database_url, app_url.render_as_string(hide_password=False)


@pytest.fixture(scope='session')
def rls_admin_database_url(rls_database_urls: tuple[str, str]) -> str:
    """Provide the administrator URL after RLS test provisioning."""
    return rls_database_urls[0]


@pytest_asyncio.fixture
async def rls_session_manager(
    rls_database_urls: tuple[str, str],
) -> AsyncGenerator[SessionManager]:
    """Provide session infrastructure connected as the runtime application role."""
    engine = create_database_engine(rls_database_urls[1])
    manager = SessionManager(engine, create_session_factory(engine))

    try:
        yield manager
    finally:
        await manager.dispose()


def _enable_test_table_rls(connection: Connection) -> None:
    """Apply production RLS helpers to the disposable tenant tables."""
    operations = Operations(MigrationContext.configure(connection))
    enable_tenant_rls(operations, 'rls_test_parents')
    enable_tenant_rls(operations, 'rls_test_children')
