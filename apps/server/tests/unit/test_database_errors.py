"""Unit tests for database error translation."""

from typing import cast

import pytest
from enact.identity.errors import UserEmailAlreadyExistsError
from enact.infrastructure.database.errors import (
    DatabaseIntegrityError,
    DatabasePersistenceError,
)
from enact.infrastructure.database.session.flush import flush_session
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class _ConstraintViolation(Exception):
    """Represent a driver error carrying a PostgreSQL constraint name."""

    constraint_name = 'uq_users_email'


class _FailingSession:
    """Provide an asynchronous flush that raises a configured database error."""

    def __init__(self, error: SQLAlchemyError) -> None:
        """Initialize the failing session.

        Args:
            error: Error to raise during flush.
        """
        self._error = error

    async def flush(self) -> None:
        """Raise the configured database error."""
        raise self._error


@pytest.mark.unit
@pytest.mark.asyncio
class TestFlushSession:
    """Verify translation of SQLAlchemy flush failures."""

    async def test_maps_known_constraint_to_domain_error(self) -> None:
        """Translate a known constraint into its configured identity error."""
        error = IntegrityError('insert failed', None, _ConstraintViolation())
        session = _FailingSession(error)

        with pytest.raises(UserEmailAlreadyExistsError) as raised:
            await flush_session(
                session=cast(AsyncSession, session),
                constraint_errors={'uq_users_email': UserEmailAlreadyExistsError},
            )

        assert raised.value.code == 'user_email_already_exists'
        assert isinstance(raised.value.__cause__, IntegrityError)

    async def test_maps_unknown_constraint_to_database_integrity_error(self) -> None:
        """Translate an unmapped integrity failure into a stable database error."""
        error = IntegrityError('insert failed', None, Exception())
        session = _FailingSession(error)

        with pytest.raises(DatabaseIntegrityError) as raised:
            await flush_session(session=cast(AsyncSession, session))

        assert raised.value.code == 'database_integrity_error'
        assert raised.value.constraint_name is None

    async def test_maps_other_sqlalchemy_failure_to_persistence_error(self) -> None:
        """Translate non-integrity SQLAlchemy failures into a persistence error."""
        error = OperationalError('flush failed', None, Exception())
        session = _FailingSession(error)

        with pytest.raises(DatabasePersistenceError) as raised:
            await flush_session(session=cast(AsyncSession, session))

        assert raised.value.code == 'database_persistence_error'
        assert isinstance(raised.value.__cause__, OperationalError)
