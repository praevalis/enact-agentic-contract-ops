"""Unit tests for identity schemas, authorization, and authentication."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from enact.identity.authentication import AccessTokenCodec, PasswordHasher
from enact.identity.errors import (
    AuthSessionNotFoundError,
    InvalidAccessTokenError,
    MembershipNotFoundError,
    OrganizationNotFoundError,
    UserNotFoundError,
)
from enact.identity.schemas import LoginCreate
from pydantic import ValidationError


@pytest.mark.unit
class TestIdentitySchemas:
    """Verify identity input validation."""

    def test_login_accepts_valid_email(self) -> None:
        credentials = LoginCreate(email='user@example.com', password='secret')

        assert str(credentials.email) == 'user@example.com'

    def test_login_rejects_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            LoginCreate(email='not-an-email', password='secret')

    def test_login_rejects_empty_password(self) -> None:
        with pytest.raises(ValidationError):
            LoginCreate(email='user@example.com', password='')

    def test_login_normalizes_email(self) -> None:
        credentials = LoginCreate(email='  USER@Example.COM ', password='secret')

        assert str(credentials.email) == 'user@example.com'


@pytest.mark.unit
class TestAuthentication:
    """Verify password and access-token mechanisms."""

    def test_password_hash_verifies_and_rehashes(self) -> None:
        hasher = PasswordHasher()
        password_hash = hasher.hash('correct horse battery staple')

        assert hasher.verify('correct horse battery staple', password_hash)
        assert not hasher.verify('wrong password', password_hash)
        assert not hasher.needs_rehash(password_hash)

    def test_access_token_round_trips_principal(self) -> None:
        now = datetime.now(UTC).replace(microsecond=0)
        user_id = uuid4()
        session_id = uuid4()
        organization_id = uuid4()
        membership_id = uuid4()
        codec = AccessTokenCodec('test-secret-with-at-least-32-bytes!!')

        token = codec.encode(
            user_id=user_id,
            session_id=session_id,
            organization_id=organization_id,
            membership_id=membership_id,
            role='administrator',
            expires_at=now + timedelta(minutes=5),
        )
        principal = codec.decode(token)

        assert principal.user_id == user_id
        assert principal.session_id == session_id
        assert principal.organization_id == organization_id
        assert principal.membership_id == membership_id
        assert principal.role == 'administrator'
        assert principal.access_token_expires_at == now + timedelta(minutes=5)

    def test_expired_access_token_is_rejected(self) -> None:
        codec = AccessTokenCodec('test-secret-with-at-least-32-bytes!!')
        token = codec.encode(
            user_id=uuid4(),
            session_id=uuid4(),
            organization_id=uuid4(),
            membership_id=uuid4(),
            role='administrator',
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )

        with pytest.raises(InvalidAccessTokenError, match='Invalid access token'):
            codec.decode(token)


@pytest.mark.unit
class TestIdentityErrors:
    """Verify stable identity error contracts."""

    def test_not_found_errors_have_stable_codes(self) -> None:
        """Expose entity-specific not-found codes for application handling."""
        identifier = uuid4()
        errors = (
            UserNotFoundError(identifier),
            OrganizationNotFoundError(identifier),
            MembershipNotFoundError(identifier),
            AuthSessionNotFoundError(identifier),
        )

        assert [error.code for error in errors] == [
            'user_not_found',
            'organization_not_found',
            'membership_not_found',
            'auth_session_not_found',
        ]
