"""Identity application services that orchestrate authentication workflows."""

import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

from .authentication import AccessTokenCodec, PasswordHasher, Principal
from .entities import AuthSession, Membership, Organization, User
from .enums import MembershipRole, MembershipStatus
from .errors import (
    AuthSessionInactiveError,
    AuthSessionNotFoundError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    MembershipNotFoundError,
    MembershipPermissionDeniedError,
    NoActiveMembershipError,
    OrganizationMembershipNotFoundError,
    OrganizationNotFoundError,
)
from .unit_of_work import IdentityUnitOfWork


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    """Result returned after creating or rotating an authenticated session."""

    user: User
    organization: Organization
    membership: Membership
    session: AuthSession
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime


@dataclass(frozen=True, slots=True)
class OrganizationContextResult:
    """Result returned after changing a session's organization context."""

    session: AuthSession
    organization: Organization
    membership: Membership
    access_token: str
    access_token_expires_at: datetime


class AuthenticationService:
    """Coordinate local credentials, memberships, sessions, and tokens."""

    def __init__(
        self,
        *,
        uow: IdentityUnitOfWork,
        password_hasher: PasswordHasher,
        access_token_codec: AccessTokenCodec,
        access_token_lifetime: timedelta,
        refresh_token_lifetime: timedelta,
        clock: Callable[[], datetime] | None = None,
        refresh_token_factory: Callable[[], str] | None = None,
    ) -> None:
        """Initialize the authentication application service.

        Args:
            uow: Unit of work containing all identity repositories for one transaction.
            password_hasher: Credential hashing and verification mechanism.
            access_token_codec: Access-token encoding mechanism.
            access_token_lifetime: Lifetime of issued access tokens.
            refresh_token_lifetime: Lifetime of issued refresh sessions.
            clock: Time source used for expiry and audit timestamps.
            refresh_token_factory: Factory for opaque refresh-token values.

        Raises:
            ValueError: If either lifetime is non-positive or refresh expires no later than access.
        """
        if access_token_lifetime <= timedelta(0):
            raise ValueError('Access-token lifetime must be positive.')

        if refresh_token_lifetime <= timedelta(0):
            raise ValueError('Refresh-token lifetime must be positive.')

        if refresh_token_lifetime <= access_token_lifetime:
            raise ValueError('Refresh-token lifetime must exceed access-token lifetime.')

        self._uow = uow
        self._password_hasher = password_hasher
        self._access_token_codec = access_token_codec
        self._access_token_lifetime = access_token_lifetime
        self._refresh_token_lifetime = refresh_token_lifetime
        self._clock = clock or (lambda: datetime.now(UTC))
        self._refresh_token_factory = refresh_token_factory or (lambda: secrets.token_urlsafe(48))

    async def register(self, *, email: str, password: str, display_name: str) -> User:
        """Register a local user identity.

        Args:
            email: Normalized email address for the user.
            password: Plaintext password supplied during registration.
            display_name: Name shown for the user.

        Returns:
            The created user.
        """
        async with self._uow:
            password_hash = self._password_hasher.hash(password)

            # TODO: Issue an account-only session for organization onboarding.
            return await self._uow.users.create(
                email=email,
                password_hash=password_hash,
                display_name=display_name,
            )

    async def login(self, *, email: str, password: str) -> AuthenticationResult:
        """Authenticate credentials and create an authentication session.

        Args:
            email: Normalized email address supplied by the user.
            password: Plaintext password supplied by the user.

        Returns:
            The authenticated context and issued tokens.

        Raises:
            InvalidCredentialsError: If the credentials are invalid or the user is disabled.
            NoActiveMembershipError: If the user has no active organization membership.
        """
        async with self._uow:
            user = await self._uow.users.find_by_email(email)

            if user is None or user.status != 'active':
                raise InvalidCredentialsError()

            if not self._password_hasher.verify(password, user.password_hash):
                raise InvalidCredentialsError()

            memberships = list(await self._uow.memberships.list_for_user(user.id))
            membership, organization = await self._select_context(user.id, memberships)

            now = self._clock()
            refresh_token = self._refresh_token_factory()
            session = await self._uow.sessions.create(
                user_id=user.id,
                organization_id=organization.id,
                token_family_id=uuid4(),
                refresh_token_digest=self.digest_refresh_token(refresh_token),
                expires_at=now + self._refresh_token_lifetime,
            )

            await self._uow.preferences.record_use(user.id, organization.id, now)

            access_token_expires_at = now + self._access_token_lifetime
            access_token = self._access_token_codec.encode(
                user_id=user.id,
                session_id=session.id,
                organization_id=membership.organization_id,
                membership_id=membership.id,
                role=membership.role,
                expires_at=access_token_expires_at,
            )

            return AuthenticationResult(
                user=user,
                organization=organization,
                membership=membership,
                session=session,
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expires_at=access_token_expires_at,
            )

    async def refresh(self, refresh_token: str) -> AuthenticationResult:
        """Rotate a refresh token and issue a new authenticated context.

        Args:
            refresh_token: Opaque refresh token presented by the client.

        Returns:
            The rotated context and replacement tokens.

        Raises:
            InvalidRefreshTokenError: If the token is unknown, expired, revoked, or unusable.
        """
        async with self._uow:
            session = await self._uow.sessions.find_by_token_digest(
                self.digest_refresh_token(refresh_token)
            )

            if session is None:
                raise InvalidRefreshTokenError()

            now = self._clock()

            if session.revoked_at is not None:
                await self._uow.sessions.revoke_family(session.token_family_id, now)
            else:
                if session.expires_at <= now:
                    raise InvalidRefreshTokenError()

                user = await self._uow.users.get(session.user_id)
                if user is None:
                    raise InvalidRefreshTokenError()

                context = await self._get_active_context(user, session.current_organization_id)
                if context is None:
                    raise InvalidRefreshTokenError()

                membership, organization = context

                replacement_refresh_token = self._refresh_token_factory()
                replacement = await self._uow.sessions.create(
                    user_id=session.user_id,
                    organization_id=organization.id,
                    token_family_id=session.token_family_id,
                    refresh_token_digest=self.digest_refresh_token(replacement_refresh_token),
                    expires_at=now + self._refresh_token_lifetime,
                )

                await self._uow.sessions.rotate(session.id, replacement.id, now)
                await self._uow.preferences.record_use(user.id, organization.id, now)

                access_token_expires_at = now + self._access_token_lifetime
                access_token = self._access_token_codec.encode(
                    user_id=user.id,
                    session_id=replacement.id,
                    organization_id=membership.organization_id,
                    membership_id=membership.id,
                    role=membership.role,
                    expires_at=access_token_expires_at,
                )

                return AuthenticationResult(
                    user=user,
                    organization=organization,
                    membership=membership,
                    session=replacement,
                    access_token=access_token,
                    refresh_token=replacement_refresh_token,
                    access_token_expires_at=access_token_expires_at,
                )

        raise InvalidRefreshTokenError()

    async def logout(self, *, user_id: UUID, session_id: UUID) -> None:
        """Revoke the authenticated user's complete refresh-token family.

        Args:
            user_id: Authenticated user requesting logout.
            session_id: Session identifying the device's token family.

        Raises:
            AuthSessionNotFoundError: If the session does not belong to the user.
        """
        async with self._uow:
            session = await self._uow.sessions.get(session_id)

            if session is None or session.user_id != user_id:
                raise AuthSessionNotFoundError(session_id)

            await self._uow.sessions.revoke_family(session.token_family_id, self._clock())

    async def validate_access_token(self, access_token: str) -> Principal:
        """Resolve a token against current user, session, and membership state.

        Args:
            access_token: Signed access token presented by the caller.

        Returns:
            The principal when its entire authorization context remains active.

        Raises:
            InvalidAccessTokenError: If the token or its persisted context is no longer valid.
        """
        principal = self._access_token_codec.decode(access_token)

        async with self._uow:
            session = await self._uow.sessions.get(principal.session_id)

            if (
                session is None
                or session.user_id != principal.user_id
                or session.current_organization_id != principal.organization_id
                or session.revoked_at is not None
                or session.expires_at <= self._clock()
            ):
                raise InvalidAccessTokenError()

            user = await self._uow.users.get(principal.user_id)
            context = await self._get_active_context(user, principal.organization_id)

            if context is None:
                raise InvalidAccessTokenError()

            membership, _ = context

            if membership.id != principal.membership_id or membership.role != principal.role:
                raise InvalidAccessTokenError()

        return principal

    @staticmethod
    def digest_refresh_token(refresh_token: str) -> str:
        """Return the deterministic digest used to persist a refresh token.

        Args:
            refresh_token: Opaque refresh token value.

        Returns:
            Hexadecimal SHA-256 digest of the token.
        """
        return sha256(refresh_token.encode('utf-8')).hexdigest()

    async def _select_context(
        self,
        user_id: UUID,
        memberships: Sequence[Membership],
    ) -> tuple[Membership, Organization]:
        active_by_organization = {
            membership.organization_id: membership
            for membership in memberships
            if membership.status == MembershipStatus.ACTIVE
        }

        preferences = await self._uow.preferences.list_for_user(user_id)
        ranked_preferences = sorted(
            (
                preference
                for preference in preferences
                if preference.is_preferred or preference.last_used_at is not None
            ),
            key=lambda preference: (
                preference.is_preferred,
                preference.last_used_at or datetime.min.replace(tzinfo=UTC),
                str(preference.organization_id),
            ),
            reverse=True,
        )

        for preference in ranked_preferences:
            membership = active_by_organization.get(preference.organization_id)
            if membership is None:
                continue

            organization = await self._uow.organizations.get(membership.organization_id)
            if organization is not None and organization.status == 'active':
                return membership, organization

        organization_contexts: list[tuple[Membership, Organization]] = []
        for membership in memberships:
            if membership.status != MembershipStatus.ACTIVE:
                continue

            organization = await self._uow.organizations.get(membership.organization_id)
            if organization is not None and organization.status == 'active':
                organization_contexts.append((membership, organization))

        if not organization_contexts:
            raise NoActiveMembershipError(user_id)

        return min(
            organization_contexts,
            key=lambda context: (context[1].name.casefold(), str(context[1].id)),
        )

    async def _get_active_context(
        self,
        user: User | None,
        organization_id: UUID,
    ) -> tuple[Membership, Organization] | None:
        if user is None or user.status != 'active':
            return None

        membership = await self._uow.memberships.get_for_user_and_organization(
            user.id,
            organization_id,
        )
        if membership is None or membership.status != MembershipStatus.ACTIVE:
            return None

        organization = await self._uow.organizations.get(organization_id)
        if organization is None or organization.status != 'active':
            return None

        return membership, organization


class OrganizationContextService:
    """Coordinate authenticated organization switching."""

    def __init__(
        self,
        *,
        uow: IdentityUnitOfWork,
        access_token_codec: AccessTokenCodec,
        access_token_lifetime: timedelta,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize the organization-context application service.

        Args:
            uow: Unit of work containing all identity repositories for one transaction.
            access_token_codec: Access-token encoding mechanism.
            access_token_lifetime: Lifetime of issued access tokens.
            clock: Time source used for expiry and preference timestamps.
        """
        if access_token_lifetime <= timedelta(0):
            raise ValueError('Access-token lifetime must be positive.')

        self._uow = uow
        self._access_token_codec = access_token_codec
        self._access_token_lifetime = access_token_lifetime
        self._clock = clock or (lambda: datetime.now(UTC))

    async def switch(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        organization_id: UUID,
    ) -> OrganizationContextResult:
        """Switch an active session to another organization.

        Args:
            user_id: Authenticated user requesting the switch.
            session_id: Active session whose context should change.
            organization_id: Organization to activate.

        Returns:
            The updated context and replacement access token.

        Raises:
            AuthSessionNotFoundError: If the session does not exist or belongs to another user.
            AuthSessionInactiveError: If the session is expired or revoked.
            OrganizationMembershipNotFoundError: If the user lacks active membership.
            OrganizationNotFoundError: If the organization does not exist or is unavailable.
        """
        async with self._uow:
            session = await self._uow.sessions.get(session_id)

            if session is None or session.user_id != user_id:
                raise AuthSessionNotFoundError(session_id)

            now = self._clock()

            if session.revoked_at is not None or session.expires_at <= now:
                raise AuthSessionInactiveError(session_id)

            membership = await self._uow.memberships.get_for_user_and_organization(
                user_id,
                organization_id,
            )
            if membership is None or membership.status != MembershipStatus.ACTIVE:
                raise OrganizationMembershipNotFoundError(user_id, organization_id)

            organization = await self._uow.organizations.get(organization_id)
            if organization is None or organization.status != 'active':
                raise OrganizationNotFoundError(organization_id)

            updated_session = await self._uow.sessions.change_organization(
                session_id,
                organization_id,
            )

            await self._uow.preferences.record_use(user_id, organization_id, now)

            access_token_expires_at = now + self._access_token_lifetime
            access_token = self._access_token_codec.encode(
                user_id=user_id,
                session_id=updated_session.id,
                organization_id=organization.id,
                membership_id=membership.id,
                role=membership.role,
                expires_at=access_token_expires_at,
            )

            return OrganizationContextResult(
                session=updated_session,
                organization=organization,
                membership=membership,
                access_token=access_token,
                access_token_expires_at=access_token_expires_at,
            )


class MembershipService:
    """Apply authorized membership changes and record their effects."""

    def __init__(
        self,
        *,
        uow: IdentityUnitOfWork,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize membership lifecycle operations.

        Args:
            uow: Unit of work containing membership, session, and audit repositories.
            clock: Time source for revocation and audit timestamps.
        """
        self._uow = uow
        self._clock = clock or (lambda: datetime.now(UTC))

    async def suspend(
        self, *, actor_user_id: UUID, organization_id: UUID, membership_id: UUID
    ) -> Membership:
        """Pause an active membership and revoke its organization sessions.

        Args:
            actor_user_id: Administrator performing the action.
            organization_id: Organization containing the membership.
            membership_id: Membership to suspend.

        Returns:
            The suspended membership.

        Raises:
            MembershipPermissionDeniedError: If the actor is not an active administrator.
            MembershipNotFoundError: If the membership is outside the organization or absent.
            MembershipTransitionError: If the membership is not active.
        """
        return await self._change(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            membership_id=membership_id,
            action='suspend',
        )

    async def resume(
        self, *, actor_user_id: UUID, organization_id: UUID, membership_id: UUID
    ) -> Membership:
        """Restore a suspended membership with its retained role.

        Args:
            actor_user_id: Administrator performing the action.
            organization_id: Organization containing the membership.
            membership_id: Membership to resume.

        Returns:
            The active membership.

        Raises:
            MembershipPermissionDeniedError: If the actor is not an active administrator.
            MembershipNotFoundError: If the membership is outside the organization or absent.
            MembershipTransitionError: If the membership is not suspended.
        """
        return await self._change(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            membership_id=membership_id,
            action='resume',
        )

    async def revoke(
        self, *, actor_user_id: UUID, organization_id: UUID, membership_id: UUID
    ) -> Membership:
        """End an active or suspended membership and revoke its sessions.

        Args:
            actor_user_id: Administrator performing the action.
            organization_id: Organization containing the membership.
            membership_id: Membership to revoke.

        Returns:
            The revoked membership.

        Raises:
            MembershipPermissionDeniedError: If the actor is not an active administrator.
            MembershipNotFoundError: If the membership is outside the organization or absent.
            MembershipTransitionError: If the membership is already revoked.
        """
        return await self._change(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            membership_id=membership_id,
            action='revoke',
        )

    async def regrant(
        self,
        *,
        actor_user_id: UUID,
        organization_id: UUID,
        membership_id: UUID,
        role: MembershipRole,
    ) -> Membership:
        """Restore a revoked membership with an explicitly selected role.

        Args:
            actor_user_id: Administrator performing the action.
            organization_id: Organization containing the membership.
            membership_id: Membership to regrant.
            role: Role selected for restored access.

        Returns:
            The regranted active membership.

        Raises:
            MembershipPermissionDeniedError: If the actor is not an active administrator.
            MembershipNotFoundError: If the membership is outside the organization or absent.
            MembershipTransitionError: If the membership is not revoked.
        """
        return await self._change(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            membership_id=membership_id,
            action='regrant',
            role=role,
        )

    async def _change(
        self,
        *,
        actor_user_id: UUID,
        organization_id: UUID,
        membership_id: UUID,
        action: str,
        role: MembershipRole | None = None,
    ) -> Membership:
        """Authorize and atomically persist one membership transition and its audit event."""
        async with self._uow:
            actor = await self._uow.memberships.get_for_user_and_organization(
                actor_user_id, organization_id
            )

            if (
                actor is None
                or actor.status != MembershipStatus.ACTIVE
                or actor.role != MembershipRole.ADMINISTRATOR
            ):
                raise MembershipPermissionDeniedError(organization_id)

            target = await self._uow.memberships.get(membership_id)

            if target is None or target.organization_id != organization_id:
                raise MembershipNotFoundError(membership_id)

            match action:
                case 'suspend':
                    changed = await self._uow.memberships.suspend(membership_id)
                case 'resume':
                    changed = await self._uow.memberships.resume(membership_id)
                case 'revoke':
                    changed = await self._uow.memberships.revoke(membership_id)
                case 'regrant' if role is not None:
                    changed = await self._uow.memberships.regrant(membership_id, role.value)
                case _:
                    raise ValueError(f'Unsupported membership action: {action}.')

            now = self._clock()

            if action in {'suspend', 'revoke'}:
                await self._uow.sessions.revoke_for_user_and_organization(
                    target.user_id, organization_id, now
                )

            await self._uow.audit_events.create(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=f'membership.{action}',
                resource_type='membership',
                resource_id=membership_id,
                occurred_at=now,
                details={'user_id': str(target.user_id), 'role': changed.role},
            )

            return changed
