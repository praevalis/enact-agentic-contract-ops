"""Atomic case creation transaction boundary."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from enact.audit import AuditEventRepository
from enact.customers.repositories import CustomerRepository

from .repositories import CaseLineageRepository, CaseRepository


class CaseUnitOfWork(Protocol):
    """Coordinate customer validation, case creation, lineage, and audit."""

    customers: CustomerRepository
    cases: CaseRepository
    lineage: CaseLineageRepository
    audit_events: AuditEventRepository

    async def set_organization_context(self, organization_id: UUID) -> None:
        """Scope case creation to the authorized organization."""
        ...

    async def __aenter__(self) -> Self:
        """Begin a case creation transaction."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit all case effects or roll back on failure."""
        ...

    async def commit(self) -> None:
        """Commit all repository changes in the unit of work."""
        ...

    async def rollback(self) -> None:
        """Roll back all repository changes in the unit of work."""
        ...
