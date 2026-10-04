"""Shared SQLAlchemy flush error translation for database sessions."""

from collections.abc import Callable, Mapping

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from enact.platform.errors import EnactError

from ..errors import DatabaseIntegrityError, DatabasePersistenceError


async def flush_session(
    session: AsyncSession,
    *,
    constraint_errors: Mapping[str, Callable[[], EnactError]] | None = None,
) -> None:
    """Flush a session and translate database failures into application errors.

    Args:
        session: SQLAlchemy session whose pending changes should be flushed.
        constraint_errors: Constraint names mapped to domain-specific error factories.

    Raises:
        EnactError: If a known constraint or database failure is encountered.

    The transaction remains failed after an exception. The caller that owns the transaction
    must roll it back before reusing the session.
    """
    try:
        await session.flush()
    except IntegrityError as error:
        constraint_name = getattr(error.orig, 'constraint_name', None)
        if not isinstance(constraint_name, str):
            constraint_name = None
        error_factory = (
            constraint_errors.get(constraint_name)
            if constraint_errors is not None and constraint_name is not None
            else None
        )

        if error_factory is not None:
            raise error_factory() from error

        raise DatabaseIntegrityError(constraint_name) from error
    except SQLAlchemyError as error:
        raise DatabasePersistenceError() from error
