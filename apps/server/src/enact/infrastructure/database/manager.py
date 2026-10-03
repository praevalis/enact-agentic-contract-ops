"""Application-level ownership of database infrastructure."""

from sqlalchemy import text

from .session import SessionManager, create_database_engine, create_session_factory


class DatabaseManager:
    """Coordinate database initialization, access, and shutdown."""

    def __init__(self, database_url: str) -> None:
        """Initialize an unstarted database manager.

        Args:
            database_url: Async SQLAlchemy URL used by the runtime application role.
        """
        self._database_url = database_url
        self._session_manager: SessionManager | None = None

    def initialize(self) -> None:
        """Create the engine and session infrastructure once."""
        if self._session_manager is not None:
            return

        engine = create_database_engine(self._database_url)
        session_factory = create_session_factory(engine)
        self._session_manager = SessionManager(engine, session_factory)

    def get_session_manager(self) -> SessionManager:
        """Return the initialized session manager.

        Returns:
            The process-wide session manager.

        Raises:
            RuntimeError: If database infrastructure has not been initialized.
        """
        if self._session_manager is None:
            raise RuntimeError('Database manager has not been initialized.')

        return self._session_manager

    async def ping(self) -> None:
        """Verify that the database accepts a query.

        Raises:
            RuntimeError: If database infrastructure has not been initialized.
            sqlalchemy.exc.SQLAlchemyError: If the database cannot execute the query.
        """
        async with self.get_session_manager().session_scope() as session:
            await session.execute(text('SELECT 1'))

    async def dispose(self) -> None:
        """Dispose database resources when initialized."""
        if self._session_manager is None:
            return

        await self._session_manager.dispose()
        self._session_manager = None
