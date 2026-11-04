"""Unit tests for identity application services."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import cast
from uuid import UUID, uuid4

import pytest
from enact.identity.authentication import AccessTokenCodec, PasswordHasher
from enact.identity.entities import (
    AuthSession,
    Membership,
    Organization,
    OrganizationInvitation,
    User,
    UserOrganizationPreference,
)
from enact.identity.enums import MembershipRole
from enact.identity.errors import (
    AuthSessionNotFoundError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidInvitationCodeError,
    InvalidRefreshTokenError,
)
from enact.identity.repositories import (
    AuthSessionRepository,
    MembershipRepository,
    OrganizationRepository,
    UserOrganizationPreferenceRepository,
    UserRepository,
)
from enact.identity.services import (
    AuthenticationService,
    OnboardingService,
    OrganizationContextService,
)
from enact.identity.unit_of_work import IdentityUnitOfWork


class _Users:
    """In-memory user persistence for service tests."""

    def __init__(self, user: User) -> None:
        self.user = user

    async def get(self, user_id: UUID) -> User | None:
        return self.user if self.user.id == user_id else None

    async def find_by_email(self, email: str) -> User | None:
        return self.user if self.user.email == email else None

    async def create(self, *, email: str, password_hash: str, display_name: str) -> User:
        self.user = User(uuid4(), email, password_hash, display_name, 'active')
        return self.user


class _Memberships:
    """In-memory membership persistence for service tests."""

    def __init__(self, *memberships: Membership) -> None:
        self.memberships = memberships

    async def list_for_user(self, user_id: UUID) -> Sequence[Membership]:
        return [membership for membership in self.memberships if membership.user_id == user_id]

    async def get_for_user_and_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> Membership | None:
        return next(
            (
                membership
                for membership in self.memberships
                if membership.user_id == user_id and membership.organization_id == organization_id
            ),
            None,
        )

    async def create(self, *, user_id: UUID, organization_id: UUID, role: str) -> Membership:
        membership = Membership(uuid4(), user_id, organization_id, role, 'active')
        self.memberships = (*self.memberships, membership)
        return membership


class _Organizations:
    """In-memory organization persistence for service tests."""

    def __init__(self, *organizations: Organization) -> None:
        self.organizations = {organization.id: organization for organization in organizations}

    async def get(self, organization_id: UUID) -> Organization | None:
        return self.organizations.get(organization_id)

    async def create(self, *, name: str) -> Organization:
        organization = Organization(uuid4(), name, 'active')
        self.organizations[organization.id] = organization
        return organization


class _Preferences:
    """In-memory organization preference persistence for service tests."""

    def __init__(self) -> None:
        self.preferences: list[UserOrganizationPreference] = []

    async def list_for_user(self, user_id: UUID) -> Sequence[UserOrganizationPreference]:
        return [preference for preference in self.preferences if preference.user_id == user_id]

    async def record_use(
        self,
        user_id: UUID,
        organization_id: UUID,
        used_at: datetime,
    ) -> UserOrganizationPreference:
        for preference in self.preferences:
            if preference.user_id == user_id and preference.organization_id == organization_id:
                updated = UserOrganizationPreference(
                    user_id=user_id,
                    organization_id=organization_id,
                    is_preferred=preference.is_preferred,
                    last_used_at=used_at,
                )
                self.preferences[self.preferences.index(preference)] = updated
                return updated
        preference = UserOrganizationPreference(user_id, organization_id, False, used_at)
        self.preferences.append(preference)
        return preference

    async def set_preferred(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> UserOrganizationPreference:
        preference = await self.record_use(user_id, organization_id, datetime.now(UTC))
        updated = UserOrganizationPreference(
            user_id=user_id,
            organization_id=organization_id,
            is_preferred=True,
            last_used_at=preference.last_used_at,
        )
        self.preferences[self.preferences.index(preference)] = updated
        return updated


class _Sessions:
    """In-memory authentication-session persistence for service tests."""

    def __init__(self) -> None:
        self.sessions: list[AuthSession] = []

    async def get(self, session_id: UUID) -> AuthSession | None:
        return next((session for session in self.sessions if session.id == session_id), None)

    async def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID | None,
        token_family_id: UUID,
        refresh_token_digest: str,
        expires_at: datetime,
    ) -> AuthSession:
        session = AuthSession(
            id=uuid4(),
            user_id=user_id,
            current_organization_id=organization_id,
            token_family_id=token_family_id,
            refresh_token_digest=refresh_token_digest,
            expires_at=expires_at,
            revoked_at=None,
            replaced_by_session_id=None,
        )
        self.sessions.append(session)
        return session

    async def find_by_token_digest(self, refresh_token_digest: str) -> AuthSession | None:
        return next(
            (
                session
                for session in self.sessions
                if session.refresh_token_digest == refresh_token_digest
            ),
            None,
        )

    async def list_active_for_user(self, user_id: UUID) -> Sequence[AuthSession]:
        return [
            session
            for session in self.sessions
            if session.user_id == user_id and session.revoked_at is None
        ]

    async def rotate(
        self,
        session_id: UUID,
        replacement_session_id: UUID,
        used_at: datetime,
    ) -> None:
        session = await self.get(session_id)
        assert session is not None
        self.sessions[self.sessions.index(session)] = AuthSession(
            id=session.id,
            user_id=session.user_id,
            current_organization_id=session.current_organization_id,
            token_family_id=session.token_family_id,
            refresh_token_digest=session.refresh_token_digest,
            expires_at=session.expires_at,
            revoked_at=used_at,
            replaced_by_session_id=replacement_session_id,
        )

    async def change_organization(self, session_id: UUID, organization_id: UUID) -> AuthSession:
        session = await self.get(session_id)
        assert session is not None
        updated = AuthSession(
            id=session.id,
            user_id=session.user_id,
            current_organization_id=organization_id,
            token_family_id=session.token_family_id,
            refresh_token_digest=session.refresh_token_digest,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
            replaced_by_session_id=session.replaced_by_session_id,
        )
        self.sessions[self.sessions.index(session)] = updated
        return updated

    async def revoke(self, session_id: UUID, revoked_at: datetime) -> None:
        session = await self.get(session_id)
        assert session is not None
        self.sessions[self.sessions.index(session)] = AuthSession(
            id=session.id,
            user_id=session.user_id,
            current_organization_id=session.current_organization_id,
            token_family_id=session.token_family_id,
            refresh_token_digest=session.refresh_token_digest,
            expires_at=session.expires_at,
            revoked_at=revoked_at,
            replaced_by_session_id=session.replaced_by_session_id,
        )

    async def revoke_family(self, token_family_id: UUID, revoked_at: datetime) -> None:
        for session in list(self.sessions):
            if session.token_family_id == token_family_id and session.revoked_at is None:
                await self.revoke(session.id, revoked_at)


class _Invitations:
    """In-memory single-use invitation persistence for service tests."""

    def __init__(self) -> None:
        self.invitations: list[OrganizationInvitation] = []

    async def create(
        self,
        *,
        organization_id: UUID,
        code_digest: str,
        role: str,
        created_by_user_id: UUID,
        expires_at: datetime,
    ) -> OrganizationInvitation:
        invitation = OrganizationInvitation(
            uuid4(), organization_id, code_digest, role, created_by_user_id, expires_at, None, None
        )
        self.invitations.append(invitation)
        return invitation

    async def redeem(
        self, *, code_digest: str, user_id: UUID, redeemed_at: datetime
    ) -> OrganizationInvitation | None:
        for invitation in self.invitations:
            if (
                invitation.code_digest == code_digest
                and invitation.redeemed_at is None
                and invitation.expires_at > redeemed_at
            ):
                redeemed = OrganizationInvitation(
                    invitation.id,
                    invitation.organization_id,
                    invitation.code_digest,
                    invitation.role,
                    invitation.created_by_user_id,
                    invitation.expires_at,
                    user_id,
                    redeemed_at,
                )
                self.invitations[self.invitations.index(invitation)] = redeemed
                return redeemed

        return None


class _AuditEvents:
    """Record audit actions issued by onboarding workflows."""

    def __init__(self) -> None:
        self.actions: list[str] = []

    async def create(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        occurred_at: datetime,
        details: dict[str, object] | None = None,
    ) -> None:
        self.actions.append(action)


class _UnitOfWork:
    """In-memory identity unit of work for service tests."""

    def __init__(
        self,
        *,
        users: _Users,
        memberships: _Memberships,
        organizations: _Organizations,
        preferences: _Preferences,
        sessions: _Sessions,
    ) -> None:
        self.users = cast(UserRepository, users)
        self.memberships = cast(MembershipRepository, memberships)
        self.organizations = cast(OrganizationRepository, organizations)
        self.preferences = cast(UserOrganizationPreferenceRepository, preferences)
        self.sessions = cast(AuthSessionRepository, sessions)
        self.invitations = _Invitations()
        self.audit_events = _AuditEvents()
        self.commit_count = 0
        self.rollback_count = 0

    async def set_user_context(self, user_id: UUID) -> None:
        self.user_context = user_id

    async def set_organization_context(self, organization_id: UUID) -> None:
        self.organization_context = organization_id

    async def set_invitation_digest(self, code_digest: str) -> None:
        self.invitation_digest = code_digest

    async def __aenter__(self) -> '_UnitOfWork':
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


def _service_fixture(
    now: datetime | None = None,
) -> tuple[
    AuthenticationService,
    OrganizationContextService,
    _UnitOfWork,
    _Users,
    _Sessions,
    User,
    Organization,
]:
    user_id = uuid4()
    organization_id = uuid4()
    user = User(user_id, 'user@example.com', '', 'User', 'active')
    organization = Organization(organization_id, 'Acme Cloud', 'active')
    membership = Membership(uuid4(), user_id, organization_id, 'administrator', 'active')
    users = _Users(user)
    memberships = _Memberships(membership)
    organizations = _Organizations(organization)
    preferences = _Preferences()
    sessions = _Sessions()
    uow = _UnitOfWork(
        users=users,
        memberships=memberships,
        organizations=organizations,
        preferences=preferences,
        sessions=sessions,
    )
    hasher = PasswordHasher()
    users.user = User(
        user_id, user.email, hasher.hash('correct-password'), user.display_name, 'active'
    )
    now = now or datetime(2026, 1, 1, tzinfo=UTC)
    codec = AccessTokenCodec('test-secret-with-at-least-32-bytes!!')
    refresh_tokens = iter(
        (
            'initial-refresh-token',
            'replacement-refresh-token',
            'third-refresh-token',
            'fourth-refresh-token',
        )
    )
    authentication = AuthenticationService(
        uow=cast(IdentityUnitOfWork, uow),
        password_hasher=hasher,
        access_token_codec=codec,
        access_token_lifetime=timedelta(minutes=5),
        refresh_token_lifetime=timedelta(days=30),
        clock=lambda: now,
        refresh_token_factory=lambda: next(refresh_tokens),
    )
    context = OrganizationContextService(
        uow=cast(IdentityUnitOfWork, uow),
        access_token_codec=codec,
        access_token_lifetime=timedelta(minutes=5),
        clock=lambda: now,
    )
    return authentication, context, uow, users, sessions, users.user, organization


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuthenticationService:
    """Verify authentication workflow orchestration."""

    @pytest.mark.parametrize('refresh_minutes', [4, 5])
    async def test_refresh_lifetime_must_exceed_access_lifetime(self, refresh_minutes: int) -> None:
        """Reject refresh sessions that cannot outlive the access token."""
        _, _, uow, _, _, _, _ = _service_fixture()

        with pytest.raises(ValueError, match='must exceed access-token lifetime'):
            AuthenticationService(
                uow=cast(IdentityUnitOfWork, uow),
                password_hasher=PasswordHasher(),
                access_token_codec=AccessTokenCodec('test-secret-with-at-least-32-bytes!!'),
                access_token_lifetime=timedelta(minutes=5),
                refresh_token_lifetime=timedelta(minutes=refresh_minutes),
            )

    async def test_login_creates_session_and_tokens(self) -> None:
        """Authenticate a user and select the only active organization."""
        service, _, uow, _, sessions, user, organization = _service_fixture()

        result = await service.login(email=user.email, password='correct-password')

        assert result.organization is not None
        assert result.user.id == user.id
        assert result.organization.id == organization.id
        assert result.access_token
        assert result.refresh_token == 'initial-refresh-token'
        assert len(sessions.sessions) == 1
        assert uow.commit_count == 1
        assert uow.rollback_count == 0

    @pytest.mark.parametrize('inactive_is_preferred', [False, True])
    async def test_login_uses_next_recent_active_organization(
        self, inactive_is_preferred: bool
    ) -> None:
        """Skip an unavailable preference before the alphabetical fallback."""
        service, _, uow, _, sessions, user, alphabetical_first = _service_fixture()
        recent = Organization(uuid4(), 'Zulu', 'active')
        inactive = Organization(uuid4(), 'Beta', 'suspended')

        sessions.sessions.append(
            AuthSession(
                id=uuid4(),
                user_id=user.id,
                current_organization_id=alphabetical_first.id,
                token_family_id=uuid4(),
                refresh_token_digest='existing-session',
                expires_at=datetime(2026, 2, 1, tzinfo=UTC),
                revoked_at=None,
                replaced_by_session_id=None,
            )
        )

        uow.memberships = cast(
            MembershipRepository,
            _Memberships(
                Membership(uuid4(), user.id, alphabetical_first.id, 'administrator', 'active'),
                Membership(uuid4(), user.id, recent.id, 'administrator', 'active'),
                Membership(uuid4(), user.id, inactive.id, 'administrator', 'active'),
            ),
        )
        uow.organizations = cast(
            OrganizationRepository,
            _Organizations(alphabetical_first, recent, inactive),
        )
        preferences = cast(_Preferences, uow.preferences)
        preferences.preferences = [
            UserOrganizationPreference(
                user.id, inactive.id, inactive_is_preferred, datetime(2026, 1, 3, tzinfo=UTC)
            ),
            UserOrganizationPreference(user.id, recent.id, False, datetime(2026, 1, 2, tzinfo=UTC)),
        ]

        result = await service.login(email=user.email, password='correct-password')

        assert result.organization is not None
        assert result.organization.id == recent.id

    async def test_login_uses_alphabetical_fallback_without_history(self) -> None:
        """Select a stable active organization when there is no usage history."""
        service, _, uow, _, _, user, alphabetical_first = _service_fixture()
        other = Organization(uuid4(), 'Zulu', 'active')
        uow.memberships = cast(
            MembershipRepository,
            _Memberships(
                Membership(uuid4(), user.id, other.id, 'administrator', 'active'),
                Membership(uuid4(), user.id, alphabetical_first.id, 'administrator', 'active'),
            ),
        )
        uow.organizations = cast(
            OrganizationRepository,
            _Organizations(other, alphabetical_first),
        )

        result = await service.login(email=user.email, password='correct-password')

        assert result.organization is not None
        assert result.organization.id == alphabetical_first.id

    async def test_refresh_rotates_session(self) -> None:
        """Rotate a refresh token and revoke the presented session."""
        service, _, uow, _, sessions, user, _ = _service_fixture()
        initial = await service.login(email=user.email, password='correct-password')

        rotated = await service.refresh(initial.refresh_token)

        assert rotated.session.id != initial.session.id
        assert sessions.sessions[0].revoked_at is not None
        assert rotated.refresh_token == 'replacement-refresh-token'
        assert uow.commit_count == 2

    async def test_reused_refresh_token_revokes_family(self) -> None:
        """Commit family revocation before rejecting a reused refresh token."""
        service, _, uow, _, sessions, user, _ = _service_fixture()
        initial = await service.login(email=user.email, password='correct-password')
        rotated = await service.refresh(initial.refresh_token)

        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh(initial.refresh_token)

        assert sessions.sessions[1].id == rotated.session.id
        assert sessions.sessions[1].revoked_at is not None
        assert uow.commit_count == 3
        assert uow.rollback_count == 0

    async def test_logout_revokes_session_and_invalidates_access_token(self) -> None:
        """Reject both token types after logging out of the current session."""
        service, _, _, _, sessions, user, _ = _service_fixture(datetime.now(UTC))
        login = await service.login(email=user.email, password='correct-password')

        principal = await service.validate_access_token(login.access_token)
        assert principal.session_id == login.session.id

        await service.logout(user_id=user.id, session_id=login.session.id)

        assert sessions.sessions[0].revoked_at is not None

        with pytest.raises(InvalidAccessTokenError):
            await service.validate_access_token(login.access_token)

        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh(login.refresh_token)

    async def test_logout_revokes_rotated_session_family(self) -> None:
        """An older session ID still identifies its active replacement family."""
        service, _, _, _, sessions, user, _ = _service_fixture()
        initial = await service.login(email=user.email, password='correct-password')
        rotated = await service.refresh(initial.refresh_token)

        await service.logout(user_id=user.id, session_id=initial.session.id)

        assert sessions.sessions[1].id == rotated.session.id
        assert sessions.sessions[1].revoked_at is not None

        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh(rotated.refresh_token)

    async def test_logout_rejects_another_users_session(self) -> None:
        """A user cannot revoke another user's token family."""
        service, _, _, _, sessions, user, _ = _service_fixture()
        login = await service.login(email=user.email, password='correct-password')

        with pytest.raises(AuthSessionNotFoundError):
            await service.logout(user_id=uuid4(), session_id=login.session.id)

        assert sessions.sessions[0].revoked_at is None

    async def test_access_token_rejects_inactive_membership(self) -> None:
        """A signed token cannot retain access after its membership is suspended."""
        service, _, uow, _, _, user, organization = _service_fixture(datetime.now(UTC))
        login = await service.login(email=user.email, password='correct-password')
        assert login.membership is not None
        uow.memberships = cast(
            MembershipRepository,
            _Memberships(
                Membership(
                    login.membership.id,
                    user.id,
                    organization.id,
                    login.membership.role,
                    'suspended',
                )
            ),
        )

        with pytest.raises(InvalidAccessTokenError):
            await service.validate_access_token(login.access_token)

    async def test_login_rejects_invalid_password(self) -> None:
        """Reject incorrect credentials without creating a session."""
        service, _, uow, _, sessions, user, _ = _service_fixture()

        with pytest.raises(InvalidCredentialsError):
            await service.login(email=user.email, password='wrong-password')

        assert sessions.sessions == []
        assert uow.commit_count == 0
        assert uow.rollback_count == 1

    async def test_register_refresh_and_login_without_membership(self) -> None:
        """Resume organization setup from an account-only session after a later login."""
        service, _, uow, _, _, _, _ = _service_fixture(datetime.now(UTC))

        registered = await service.register(
            email='new@example.com', password='long-password', display_name='New User'
        )
        principal = await service.validate_access_token(registered.access_token)
        refreshed = await service.refresh(registered.refresh_token)
        login = await service.login(email='new@example.com', password='long-password')

        assert registered.organization is None
        assert registered.membership is None
        assert registered.session.current_organization_id is None
        assert principal.organization_id is None
        assert refreshed.organization is None
        assert login.organization is None
        assert uow.commit_count == 4


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrganizationContextService:
    """Verify organization-context workflow orchestration."""

    async def test_switch_updates_session_and_access_token(self) -> None:
        """Switch an active session to an authorized organization."""
        authentication, context, uow, _, sessions, user, organization = _service_fixture()
        initial = await authentication.login(email=user.email, password='correct-password')

        result = await context.switch(
            user_id=user.id,
            session_id=initial.session.id,
            organization_id=organization.id,
        )

        assert result.session.current_organization_id == organization.id
        assert result.access_token
        assert sessions.sessions[0].current_organization_id == organization.id
        assert uow.commit_count == 2

    async def test_list_available_excludes_suspended_organizations(self) -> None:
        """Show only active organization contexts in the switcher."""
        _, context, uow, _, _, user, organization = _service_fixture()
        suspended = Organization(uuid4(), 'Unavailable', 'suspended')
        uow.organizations = cast(OrganizationRepository, _Organizations(organization, suspended))
        uow.memberships = cast(
            MembershipRepository,
            _Memberships(
                Membership(uuid4(), user.id, organization.id, 'administrator', 'active'),
                Membership(uuid4(), user.id, suspended.id, 'auditor', 'active'),
            ),
        )

        available = await context.list_available(user.id)

        assert [item[1].id for item in available] == [organization.id]


@pytest.mark.unit
@pytest.mark.asyncio
class TestOnboardingService:
    """Verify account setup and invitation workflows."""

    async def test_create_organization_grants_creator_administrator(self) -> None:
        """Activate an account-only session in a new organization."""
        authentication, _, uow, _, _, _, _ = _service_fixture(datetime.now(UTC))
        registered = await authentication.register(
            email='creator@example.com', password='long-password', display_name='Creator'
        )
        onboarding = OnboardingService(
            uow=cast(IdentityUnitOfWork, uow),
            access_token_codec=AccessTokenCodec('test-secret-with-at-least-32-bytes!!'),
            access_token_lifetime=timedelta(minutes=5),
        )

        result = await onboarding.create_organization(
            user_id=registered.user.id,
            session_id=registered.session.id,
            name='New Organization',
        )

        assert result.organization.name == 'New Organization'
        assert result.membership.role == MembershipRole.ADMINISTRATOR
        assert result.session.current_organization_id == result.organization.id
        assert uow.organization_context == result.organization.id
        assert uow.audit_events.actions == ['organization.create']

        second = await onboarding.create_organization(
            user_id=registered.user.id,
            session_id=registered.session.id,
            name='Second Organization',
        )

        assert second.organization.id != result.organization.id
        assert second.session.current_organization_id == second.organization.id
        assert second.membership.role == MembershipRole.ADMINISTRATOR

    async def test_invitation_is_single_use_and_grants_selected_role(self) -> None:
        """Issue a code, join once, and reject a second redemption."""
        authentication, _, uow, _, _, administrator, organization = _service_fixture(
            datetime.now(UTC)
        )
        onboarding = OnboardingService(
            uow=cast(IdentityUnitOfWork, uow),
            access_token_codec=AccessTokenCodec('test-secret-with-at-least-32-bytes!!'),
            access_token_lifetime=timedelta(minutes=5),
        )

        issued = await onboarding.issue_invitation(
            actor_user_id=administrator.id,
            organization_id=organization.id,
            role=MembershipRole.AUDITOR,
        )
        assert len(issued.code) == 8

        invited = await authentication.register(
            email='invited@example.com', password='long-password', display_name='Invited'
        )
        existing = await onboarding.create_organization(
            user_id=invited.user.id,
            session_id=invited.session.id,
            name='Existing Organization',
        )
        joined = await onboarding.join_organization(
            user_id=invited.user.id,
            session_id=invited.session.id,
            code=issued.code.lower(),
        )

        assert joined.membership.role == MembershipRole.AUDITOR
        assert joined.organization.id == organization.id
        assert joined.session.current_organization_id == organization.id
        assert existing.organization.id != joined.organization.id
        assert uow.audit_events.actions == [
            'organization_invitation.create',
            'organization.create',
            'membership.join',
        ]

        another = await authentication.register(
            email='another@example.com', password='long-password', display_name='Another'
        )
        with pytest.raises(InvalidInvitationCodeError):
            await onboarding.join_organization(
                user_id=another.user.id,
                session_id=another.session.id,
                code=issued.code,
            )
