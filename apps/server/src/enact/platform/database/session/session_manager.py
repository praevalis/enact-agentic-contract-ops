"""Short-lived asynchronous session and transaction management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class SessionManager:
    """Create transactional sessions and dispose their shared engine."""

    def __init__(
        self,
        engine: AsyncEngine,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Initialize the session manager.

        Args:
            engine: Process-wide asynchronous database engine.
            session_factory: Factory for independent asynchronous sessions.
        """
        self._engine: AsyncEngine | None = engine
        self._session_factory: async_sessionmaker[AsyncSession] | None = session_factory

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession]:
        """Yield one managed session without committing its transaction.

        Yields:
            A session rolled back on failure. The caller owns flushing and transaction
            commitment.

        Raises:
            RuntimeError: If the session manager has been disposed.
        """
        session_factory = self._session_factory
        if session_factory is None:
            raise RuntimeError('Session manager has been disposed.')

        async with session_factory() as session:
            try:
                yield session
            except BaseException:
                await session.rollback()
                raise

    @asynccontextmanager
    async def tenant_session_scope(
        self,
        organization_id: UUID,
    ) -> AsyncGenerator[AsyncSession]:
        """Yield a session with transaction-local tenant context.

        The caller owns flushing and commitment. Committing ends the transaction and clears
        the tenant context, so the session must not be used for further tenant queries after
        a commit.

        Args:
            organization_id: Authorized organization identifier for the transaction.

        Yields:
            A session whose current transaction is scoped to the organization.

        Raises:
            RuntimeError: If the session manager has been disposed.
            sqlalchemy.exc.SQLAlchemyError: If PostgreSQL cannot set the tenant context.
        """
        async with self.session_scope() as session:
            await session.execute(
                text("SELECT set_config('enact.organization_id', :organization_id, true)"),
                {'organization_id': str(organization_id)},
            )
            yield session

    async def dispose(self) -> None:
        """Dispose the underlying connection pool."""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None
