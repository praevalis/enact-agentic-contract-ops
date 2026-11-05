"""Unit checks for the organization onboarding API contract."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from enact.api.identity.mappers import to_principal_read
from enact.api.v1 import router
from enact.identity.entities import AuthSession, User
from enact.identity.services import AuthenticationResult
from fastapi import FastAPI


@pytest.mark.unit
class TestIdentityApi:
    """Verify account-only responses and versioned onboarding routes."""

    def test_account_only_authentication_response(self) -> None:
        """Expose onboarding state without an organization or refresh token in JSON."""
        now = datetime.now(UTC)
        user = User(uuid4(), 'new@example.com', 'stored-hash', 'New User', 'active')
        session = AuthSession(
            id=uuid4(),
            user_id=user.id,
            current_organization_id=None,
            token_family_id=uuid4(),
            refresh_token_digest='stored-digest',
            expires_at=now + timedelta(days=30),
            revoked_at=None,
            replaced_by_session_id=None,
        )
        result = AuthenticationResult(
            user=user,
            organization=None,
            membership=None,
            session=session,
            access_token='signed-token',
            refresh_token='opaque-refresh-token',
            access_token_expires_at=now + timedelta(minutes=15),
        )

        payload = to_principal_read(result).model_dump(mode='json')

        assert payload['organization'] is None
        assert payload['membership'] is None
        assert payload['token']['organization_id'] is None
        assert 'opaque-refresh-token' not in str(payload)
        assert 'stored-hash' not in str(payload)

    def test_openapi_exposes_versioned_onboarding_routes(self) -> None:
        """Keep account and organization operations under their resource prefixes."""
        app = FastAPI()
        app.include_router(router, prefix='/api')

        paths = app.openapi()['paths']

        assert '/api/v1/auth/register' in paths
        assert '/api/v1/auth/refresh' in paths
        assert '/api/v1/organizations' in paths
        assert '/api/v1/organizations/join' in paths
        assert '/api/v1/organizations/{organization_id}/invitations' in paths
        assert '/api/v1/users/me/organization' in paths
