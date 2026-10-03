"""Async SQLAlchemy engine and session-factory construction."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_database_engine(database_url: str) -> AsyncEngine:
    """Create the process-wide asynchronous database engine.

    Args:
        database_url: Async SQLAlchemy database URL.

    Returns:
        An asynchronous engine with connection liveness checking enabled.
    """
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create the process-wide asynchronous session factory.

    Args:
        engine: Engine to bind to newly created sessions.

    Returns:
        A factory that creates independent asynchronous sessions.
    """
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
