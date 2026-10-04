"""Stable errors raised by database infrastructure."""

from enact.platform.errors import EnactError


class DatabaseError(EnactError):
    """Base class for database infrastructure errors."""


class DatabaseIntegrityError(DatabaseError):
    """Raised when a database integrity constraint rejects a write."""

    def __init__(self, constraint_name: str | None = None) -> None:
        """Initialize an integrity error.

        Args:
            constraint_name: Database constraint that rejected the write, when available.
        """
        self.constraint_name = constraint_name
        super().__init__(
            message='The database rejected the requested write.',
            code='database_integrity_error',
        )


class DatabasePersistenceError(DatabaseError):
    """Raised when the database cannot complete a persistence operation."""

    def __init__(self) -> None:
        """Initialize a persistence error."""
        super().__init__(
            message='The database could not complete the requested operation.',
            code='database_persistence_error',
        )
