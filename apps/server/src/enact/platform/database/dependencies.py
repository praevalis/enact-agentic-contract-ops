"""FastAPI dependency adapters for database infrastructure."""

from collections.abc import AsyncGenerator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .manager import DatabaseManager
from .session import SessionManager


def get_database_manager(request: Request) -> DatabaseManager:
    """Return the application database manager.

    Args:
        request: Active request containing application database state.

    Returns:
        The process-wide database manager.
    """
    return cast(DatabaseManager, request.app.state.database_manager)


def get_session_manager(
    database_manager: Annotated[DatabaseManager, Depends(get_database_manager)],
) -> SessionManager:
    """Return the initialized session manager.

    Args:
        database_manager: Application database manager resolved by FastAPI.

    Returns:
        The process-wide session manager.

    Raises:
        RuntimeError: If database infrastructure has not been initialized.
    """
    return database_manager.get_session_manager()


async def get_session(
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> AsyncGenerator[AsyncSession]:
    """Yield a request-scoped database session.

    Args:
        session_manager: Initialized session manager resolved by FastAPI.

    Yields:
        A request-scoped asynchronous session.
    """
    async with session_manager.session_scope() as session:
        yield session
