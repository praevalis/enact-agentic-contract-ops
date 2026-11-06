"""Customer transaction boundary."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from enact.audit import AuditEventRepository

from .repositories import CustomerRepository


class CustomerUnitOfWork(Protocol):
    """Coordinate customer and audit writes atomically."""

    customers: CustomerRepository
    audit_events: AuditEventRepository

    async def set_organization_context(self, organization_id: UUID) -> None:
        """Scope customer creation to the authorized organization."""
        ...

    async def __aenter__(self) -> Self:
        """Begin a customer transaction."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit customer and audit writes or roll back on failure."""
        ...

    async def commit(self) -> None:
        """Commit all repository changes in the unit of work."""
        ...

    async def rollback(self) -> None:
        """Roll back all repository changes in the unit of work."""
        ...
