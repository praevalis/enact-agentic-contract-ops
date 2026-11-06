"""SQLAlchemy transaction boundary for customer creation."""

from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from enact.audit import AuditEventRepository
from enact.customers.repositories import CustomerRepository

from ..repositories.audit_events import SqlAlchemyAuditEventRepository
from ..repositories.customers import SqlAlchemyCustomerRepository


class SqlAlchemyCustomerUnitOfWork:
    """Commit customer and audit writes in one tenant transaction."""

    customers: CustomerRepository
    audit_events: AuditEventRepository

    def __init__(self, session: AsyncSession) -> None:
        """Initialize customer repositories.

        Args:
            session: Request database session.
        """
        self._session = session
        self.customers = SqlAlchemyCustomerRepository(session)
        self.audit_events = SqlAlchemyAuditEventRepository(session)

    async def set_organization_context(self, organization_id: UUID) -> None:
        """Set the tenant scope within the current transaction.

        Args:
            organization_id: Validated principal organization.
        """
        await self._session.execute(
            text("SELECT set_config('enact.organization_id', :value, true)"),
            {'value': str(organization_id)},
        )

    async def __aenter__(self) -> Self:
        """Enter this transaction.

        Returns:
            This unit of work.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit successful work or roll it back.

        Args:
            exc_type: Escaping exception type.
            exc_value: Escaping exception.
            traceback: Escaping traceback.
        """
        if exc_type is not None:
            await self.rollback()
            return

        try:
            await self.commit()
        except BaseException:
            await self.rollback()
            raise

    async def commit(self) -> None:
        """Commit all customer transaction changes."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back all customer transaction changes."""
        await self._session.rollback()
