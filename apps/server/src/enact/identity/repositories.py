"""Identity repository boundaries."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from .entities import (
    AuthSession,
    Membership,
    Organization,
    OrganizationInvitation,
    User,
    UserOrganizationPreference,
)


class UserRepository(Protocol):
    """Persist and retrieve user identities."""

    async def get(self, user_id: UUID) -> User | None:
        """Return one user by identifier.

        Args:
            user_id: User identifier to look up.

        Returns:
            The matching user, or ``None`` when it does not exist.
        """
        ...

    async def find_by_email(self, email: str) -> User | None:
        """Find one user by normalized email address.

        Args:
            email: Canonical email address to look up.

        Returns:
            The matching user, or ``None`` when it does not exist.
        """
        ...

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> User:
        """Create a user identity.

        Args:
            email: Canonical email address for the user.
            password_hash: Password hash for persistent storage.
            display_name: Name shown for the user.

        Returns:
            The created user.
        """
        ...

    async def update_profile(
        self,
        user_id: UUID,
        *,
        email: str,
        display_name: str,
    ) -> User:
        """Update editable user profile fields.

        Args:
            user_id: User identifier to update.
            email: Canonical replacement email address.
            display_name: Replacement display name.

        Returns:
            The updated user.
        """
        ...

    async def disable(self, user_id: UUID) -> None:
        """Disable a user without deleting its audit history.

        Args:
            user_id: User identifier to disable.
        """
        ...


class MembershipRepository(Protocol):
    """Persist and resolve organization memberships."""

    async def get(self, membership_id: UUID) -> Membership | None:
        """Return one membership by identifier.

        Args:
            membership_id: Membership identifier to look up.

        Returns:
            The matching membership, or ``None`` when it does not exist.
        """
        ...

    async def list_for_user(self, user_id: UUID) -> Sequence[Membership]:
        """Return memberships available to a user.

        Args:
            user_id: User whose memberships should be listed.

        Returns:
            The user's memberships.
        """
        ...

    async def get_for_user_and_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> Membership | None:
        """Return a user's membership in one organization, if present.

        Args:
            user_id: User identifier to match.
            organization_id: Organization identifier to match.

        Returns:
            The matching membership, or ``None`` when it does not exist.
        """
        ...

    async def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        role: str,
    ) -> Membership:
        """Create an organization membership.

        Args:
            user_id: User receiving the membership.
            organization_id: Organization containing the membership.
            role: Initial membership role.

        Returns:
            The created membership.
        """
        ...

    async def change_role(self, membership_id: UUID, role: str) -> Membership:
        """Change a membership's role.

        Args:
            membership_id: Membership identifier to update.
            role: Replacement membership role.

        Returns:
            The updated membership.
        """
        ...

    async def suspend(self, membership_id: UUID) -> Membership:
        """Suspend a membership without deleting its history.

        Args:
            membership_id: Membership identifier to suspend.

        Returns:
            The suspended membership.
        """
        ...

    async def resume(self, membership_id: UUID) -> Membership:
        """Resume a suspended membership with its retained role.

        Args:
            membership_id: Membership identifier to resume.

        Returns:
            The active membership.
        """
        ...

    async def revoke(self, membership_id: UUID) -> Membership:
        """Revoke a membership without deleting its history.

        Args:
            membership_id: Membership identifier to revoke.

        Returns:
            The revoked membership.
        """
        ...

    async def regrant(self, membership_id: UUID, role: str) -> Membership:
        """Restore a revoked membership with an explicitly chosen role.

        Args:
            membership_id: Membership identifier to regrant.
            role: Role selected for the restored access.

        Returns:
            The active membership.
        """
        ...


class OrganizationRepository(Protocol):
    """Persist and retrieve organizations."""

    async def get(self, organization_id: UUID) -> Organization | None:
        """Return one organization by identifier.

        Args:
            organization_id: Organization identifier to look up.

        Returns:
            The matching organization, or ``None`` when it does not exist.
        """
        ...

    async def create(self, *, name: str) -> Organization:
        """Create an organization.

        Args:
            name: Display name for the organization.

        Returns:
            The created organization.
        """
        ...

    async def update_profile(self, organization_id: UUID, *, name: str) -> Organization:
        """Update editable organization profile fields.

        Args:
            organization_id: Organization identifier to update.
            name: Replacement display name.

        Returns:
            The updated organization.
        """
        ...

    async def suspend(self, organization_id: UUID) -> None:
        """Suspend an organization without deleting its history.

        Args:
            organization_id: Organization identifier to suspend.
        """
        ...

    async def archive(self, organization_id: UUID) -> None:
        """Archive an organization without deleting its history.

        Args:
            organization_id: Organization identifier to archive.
        """
        ...


class UserOrganizationPreferenceRepository(Protocol):
    """Persist and retrieve user organization preferences."""

    async def get(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> UserOrganizationPreference | None:
        """Return one user's preference for an organization.

        Args:
            user_id: User identifier to match.
            organization_id: Organization identifier to match.

        Returns:
            The matching preference, or ``None`` when it does not exist.
        """
        ...

    async def list_for_user(self, user_id: UUID) -> Sequence[UserOrganizationPreference]:
        """Return a user's organization preferences.

        Args:
            user_id: User whose preferences should be listed.

        Returns:
            The user's organization preferences.
        """
        ...

    async def record_use(
        self,
        user_id: UUID,
        organization_id: UUID,
        used_at: datetime,
    ) -> UserOrganizationPreference:
        """Record an organization as recently used.

        Args:
            user_id: User whose preference should be updated.
            organization_id: Organization recently used.
            used_at: Timestamp of the organization use.

        Returns:
            The updated preference.
        """
        ...

    async def set_preferred(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> UserOrganizationPreference:
        """Set an organization's preference for a user.

        Args:
            user_id: User whose preference should be updated.
            organization_id: Organization to make preferred.

        Returns:
            The updated preference.
        """
        ...


class AuthSessionRepository(Protocol):
    """Persist and retrieve authentication sessions."""

    async def get(self, session_id: UUID) -> AuthSession | None:
        """Return one authentication session by identifier.

        Args:
            session_id: Session identifier to look up.

        Returns:
            The matching session, or ``None`` when it does not exist.
        """
        ...

    async def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID | None,
        token_family_id: UUID,
        refresh_token_digest: str,
        expires_at: datetime,
    ) -> AuthSession:
        """Create an authentication session.

        Args:
            user_id: User owning the session.
            organization_id: Session's current organization.
            token_family_id: Token family identifier for reuse detection.
            refresh_token_digest: Deterministic digest of the current refresh token.
            expires_at: Session expiration timestamp.

        Returns:
            The created authentication session.
        """
        ...

    async def find_by_token_digest(self, refresh_token_digest: str) -> AuthSession | None:
        """Find a session by its hashed refresh token.

        Args:
            refresh_token_digest: Deterministic digest of the refresh token to look up.

        Returns:
            The matching session, or ``None`` when it does not exist.
        """
        ...

    async def rotate(
        self,
        session_id: UUID,
        replacement_session_id: UUID,
        used_at: datetime,
    ) -> None:
        """Revoke a session and link it to its replacement.

        Args:
            session_id: Session whose refresh token was used.
            replacement_session_id: Newly created replacement session.
            used_at: Timestamp when the refresh token was used.
        """
        ...

    async def change_organization(
        self,
        session_id: UUID,
        organization_id: UUID,
    ) -> AuthSession:
        """Change the current organization stored on an authentication session.

        Args:
            session_id: Session whose organization context should change.
            organization_id: New current organization identifier.

        Returns:
            The updated authentication session.
        """
        ...

    async def revoke(self, session_id: UUID, revoked_at: datetime) -> None:
        """Revoke one authentication session.

        Args:
            session_id: Session identifier to revoke.
            revoked_at: Timestamp of revocation.
        """
        ...

    async def revoke_family(self, token_family_id: UUID, revoked_at: datetime) -> None:
        """Revoke every session in a token family.

        Args:
            token_family_id: Token family whose sessions should be revoked.
            revoked_at: Timestamp of revocation.
        """
        ...

    async def revoke_for_user_and_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
        revoked_at: datetime,
    ) -> None:
        """Revoke active sessions currently scoped to an organization.

        Args:
            user_id: User losing organization access.
            organization_id: Organization being removed from the user's context.
            revoked_at: Timestamp of revocation.
        """
        ...

    async def list_active_for_user(self, user_id: UUID) -> Sequence[AuthSession]:
        """List active sessions for account-management operations.

        Args:
            user_id: User whose sessions should be listed.

        Returns:
            The user's active authentication sessions.
        """
        ...


class OrganizationInvitationRepository(Protocol):
    """Persist and redeem organization invitation codes."""

    async def create(
        self,
        *,
        organization_id: UUID,
        code_digest: str,
        role: str,
        created_by_user_id: UUID,
        expires_at: datetime,
    ) -> OrganizationInvitation:
        """Create one invitation for an organization and role."""
        ...

    async def redeem(
        self, *, code_digest: str, user_id: UUID, redeemed_at: datetime
    ) -> OrganizationInvitation | None:
        """Atomically claim an unexpired invitation by its code digest."""
        ...
