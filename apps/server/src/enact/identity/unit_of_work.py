"""Identity transaction boundary."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from enact.audit import AuditEventRepository

from .repositories import (
    AuthSessionRepository,
    MembershipRepository,
    OrganizationInvitationRepository,
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
    invitations: OrganizationInvitationRepository

    async def set_user_context(self, user_id: UUID) -> None:
        """Scope user discovery queries to an authenticated user."""
        ...

    async def set_organization_context(self, organization_id: UUID) -> None:
        """Scope tenant-owned mutations to an authorized organization."""
        ...

    async def set_invitation_digest(self, code_digest: str) -> None:
        """Permit lookup of only the invitation matching a presented code."""
        ...

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
