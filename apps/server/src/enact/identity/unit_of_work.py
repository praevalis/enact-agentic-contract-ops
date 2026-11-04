"""Identity transaction boundary."""

from types import TracebackType
from typing import Protocol, Self

from enact.audit import AuditEventRepository

from .repositories import (
    AuthSessionRepository,
    MembershipRepository,
    OrganizationRepository,
    UserOrganizationPreferenceRepository,
    UserRepository,
)


class IdentityUnitOfWork(Protocol):
    """Coordinate identity repositories within one transaction."""

    users: UserRepository
    memberships: MembershipRepository
    organizations: OrganizationRepository
    preferences: UserOrganizationPreferenceRepository
    sessions: AuthSessionRepository
    audit_events: AuditEventRepository

    async def __aenter__(self) -> Self:
        """Begin a unit-of-work scope."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit successful work or roll it back after an error."""
        ...

    async def commit(self) -> None:
        """Commit all repository changes in the unit of work."""
        ...

    async def rollback(self) -> None:
        """Roll back all repository changes in the unit of work."""
        ...
