"""Request dependencies and response mapping for identity endpoints."""

from datetime import timedelta
from typing import Annotated, cast
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity import (
    AccessTokenCodec,
    AuthenticationService,
    InvalidAccessTokenError,
    OnboardingService,
    PasswordHasher,
    Principal,
)
from enact.identity.schemas import (
    MembershipRead,
    OrganizationContextRead,
    OrganizationRead,
    PrincipalRead,
    TokenRead,
    UserRead,
)
from enact.identity.services import AuthenticationResult, OrganizationContextResult
from enact.infrastructure.database.dependencies import get_session
from enact.infrastructure.database.uows.identity import SqlAlchemyIdentityUnitOfWork
from enact.platform.settings import Settings

bearer = HTTPBearer(auto_error=False)


def get_identity_settings(request: Request) -> Settings:
    """Return settings captured by the application lifespan.

    Args:
        request: Active API request.

    Returns:
        Validated application settings.
    """
    return cast(Settings, request.app.state.settings)


def get_identity_uow(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyIdentityUnitOfWork:
    """Create identity repositories over the request session.

    Args:
        session: Request-scoped database session.

    Returns:
        Identity unit of work.
    """
    return SqlAlchemyIdentityUnitOfWork(session)


def get_authentication_service(
    uow: Annotated[SqlAlchemyIdentityUnitOfWork, Depends(get_identity_uow)],
    settings: Annotated[Settings, Depends(get_identity_settings)],
) -> AuthenticationService:
    """Build the authentication service for one request.

    Args:
        uow: Request identity transaction boundary.
        settings: Validated application settings.

    Returns:
        Configured authentication service.
    """
    return AuthenticationService(
        uow=uow,
        password_hasher=PasswordHasher(),
        access_token_codec=AccessTokenCodec(settings.auth_secret_key.get_secret_value()),
        access_token_lifetime=timedelta(minutes=15),
        refresh_token_lifetime=timedelta(days=30),
    )


def get_onboarding_service(
    uow: Annotated[SqlAlchemyIdentityUnitOfWork, Depends(get_identity_uow)],
    settings: Annotated[Settings, Depends(get_identity_settings)],
) -> OnboardingService:
    """Build the organization setup service for one request.

    Args:
        uow: Request identity transaction boundary.
        settings: Validated application settings.

    Returns:
        Configured onboarding service.
    """
    return OnboardingService(
        uow=uow,
        access_token_codec=AccessTokenCodec(settings.auth_secret_key.get_secret_value()),
        access_token_lifetime=timedelta(minutes=15),
    )


async def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    authentication: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> Principal:
    """Validate a bearer token against current persisted state.

    Args:
        credentials: Optional bearer credentials from the Authorization header.
        authentication: Authentication service for this request.

    Returns:
        Validated account or organization principal.

    Raises:
        InvalidAccessTokenError: If no bearer token was supplied.
    """
    if credentials is None:
        raise InvalidAccessTokenError('Bearer token required.')

    return await authentication.validate_access_token(credentials.credentials)


def require_browser_origin(
    request: Request, settings: Annotated[Settings, Depends(get_identity_settings)]
) -> None:
    """Require the configured browser origin for cookie-bearing mutations.

    Args:
        request: Incoming HTTP request.
        settings: Validated application settings.

    Raises:
        HTTPException: If the Origin header does not match the configured web origin.
    """
    expected = urlsplit(str(settings.web_url))
    actual = urlsplit(request.headers.get('origin', ''))
    if (actual.scheme, actual.netloc) != (expected.scheme, expected.netloc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid request origin.')


def to_principal_read(result: AuthenticationResult) -> PrincipalRead:
    """Map authentication output to the public account context.

    Args:
        result: Newly issued authentication session and context.

    Returns:
        Public user, optional organization, and access-token details.
    """
    organization = (
        OrganizationRead.model_validate(result.organization)
        if result.organization is not None
        else None
    )
    membership = (
        MembershipRead.model_validate(result.membership) if result.membership is not None else None
    )

    return PrincipalRead(
        user=UserRead.model_validate(result.user),
        organization=organization,
        membership=membership,
        token=TokenRead(
            access_token=result.access_token,
            expires_at=result.access_token_expires_at,
            organization_id=result.session.current_organization_id,
        ),
    )


def to_organization_context_read(result: OrganizationContextResult) -> OrganizationContextRead:
    """Map an activated organization context to the public response.

    Args:
        result: Updated session, membership, and access token.

    Returns:
        Public organization context.
    """
    return OrganizationContextRead(
        organization=OrganizationRead.model_validate(result.organization),
        membership=MembershipRead.model_validate(result.membership),
        token=TokenRead(
            access_token=result.access_token,
            expires_at=result.access_token_expires_at,
            organization_id=result.organization.id,
        ),
    )
