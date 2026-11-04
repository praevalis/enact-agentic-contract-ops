"""SQLAlchemy identity unit-of-work implementation."""

from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from enact.audit import AuditEventRepository
from enact.identity.repositories import (
    AuthSessionRepository,
    MembershipRepository,
    OrganizationInvitationRepository,
    OrganizationRepository,
    UserOrganizationPreferenceRepository,
    UserRepository,
)

from ..repositories import (
    SqlAlchemyAuditEventRepository,
    SqlAlchemyAuthSessionRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyOrganizationInvitationRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyUserOrganizationPreferenceRepository,
    SqlAlchemyUserRepository,
)


class SqlAlchemyIdentityUnitOfWork:
    """Coordinate identity repositories over one asynchronous SQLAlchemy session."""

    users: UserRepository
    memberships: MembershipRepository
    organizations: OrganizationRepository
    preferences: UserOrganizationPreferenceRepository
    sessions: AuthSessionRepository
    audit_events: AuditEventRepository
    invitations: OrganizationInvitationRepository

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repositories for one database transaction.

        Args:
            session: SQLAlchemy session whose transaction this unit owns.
        """
        self._session = session
        self.users = SqlAlchemyUserRepository(session)
        self.memberships = SqlAlchemyMembershipRepository(session)
        self.organizations = SqlAlchemyOrganizationRepository(session)
        self.preferences = SqlAlchemyUserOrganizationPreferenceRepository(session)
        self.sessions = SqlAlchemyAuthSessionRepository(session)
        self.audit_events = SqlAlchemyAuditEventRepository(session)
        self.invitations = SqlAlchemyOrganizationInvitationRepository(session)

    async def set_user_context(self, user_id: UUID) -> None:
        """Set the transaction-local user scope for membership discovery."""
        await self._session.execute(
            text("SELECT set_config('enact.user_id', :value, true)"), {'value': str(user_id)}
        )

    async def set_organization_context(self, organization_id: UUID) -> None:
        """Set the transaction-local organization scope for tenant mutations."""
        await self._session.execute(
            text("SELECT set_config('enact.organization_id', :value, true)"),
            {'value': str(organization_id)},
        )

    async def set_invitation_digest(self, code_digest: str) -> None:
        """Restrict invitation lookup to a presented bearer code."""
        await self._session.execute(
            text("SELECT set_config('enact.invitation_digest', :value, true)"),
            {'value': code_digest},
        )

    async def __aenter__(self) -> Self:
        """Enter a unit-of-work scope.

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
        """Commit successful work or roll it back after an error.

        Args:
            exc_type: Exception type raised inside the scope, if any.
            exc_value: Exception raised inside the scope, if any.
            traceback: Exception traceback, if any.
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
        """Commit the unit-of-work transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the unit-of-work transaction."""
        await self._session.rollback()
