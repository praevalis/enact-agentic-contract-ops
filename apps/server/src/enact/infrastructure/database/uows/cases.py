"""SQLAlchemy transaction boundary for case operations."""

from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from enact.audit import AuditEventRepository
from enact.cases.repositories import CaseLineageRepository, CaseRepository
from enact.customers.repositories import CustomerRepository

from ..repositories.audit_events import SqlAlchemyAuditEventRepository
from ..repositories.cases import SqlAlchemyCaseLineageRepository, SqlAlchemyCaseRepository
from ..repositories.customers import SqlAlchemyCustomerRepository


class SqlAlchemyCaseUnitOfWork:
    """Commit case, lineage, and audit writes atomically."""

    customers: CustomerRepository
    cases: CaseRepository
    lineage: CaseLineageRepository
    audit_events: AuditEventRepository

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repositories over one request session.

        Args:
            session: Session owned by this unit of work.
        """
        self._session = session
        self.customers = SqlAlchemyCustomerRepository(session)
        self.cases = SqlAlchemyCaseRepository(session)
        self.lineage = SqlAlchemyCaseLineageRepository(session)
        self.audit_events = SqlAlchemyAuditEventRepository(session)

    async def set_organization_context(self, organization_id: UUID) -> None:
        """Set transaction-local RLS context for case operations.

        Args:
            organization_id: Validated principal's active organization.
        """
        await self._session.execute(
            text("SELECT set_config('enact.organization_id', :value, true)"),
            {'value': str(organization_id)},
        )

    async def __aenter__(self) -> Self:
        """Enter the transaction scope.

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
        """Commit successful writes or roll back the transaction.

        Args:
            exc_type: Escaping exception type, if any.
            exc_value: Escaping exception, if any.
            traceback: Escaping traceback, if any.
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
        """Commit all case transaction changes."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back all case transaction changes."""
        await self._session.rollback()
