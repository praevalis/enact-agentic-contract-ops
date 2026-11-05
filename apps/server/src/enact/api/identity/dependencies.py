"""FastAPI dependencies for identity endpoints."""

from datetime import timedelta
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity import (
    AccessTokenCodec,
    AuthenticationService,
    IdentityUnitOfWork,
    InvalidAccessTokenError,
    OnboardingService,
    PasswordHasher,
    Principal,
)
from enact.infrastructure.database.dependencies import get_session
from enact.infrastructure.database.uows.identity import SqlAlchemyIdentityUnitOfWork
from enact.platform.settings import Settings

from ..dependencies import get_request_settings

bearer = HTTPBearer(auto_error=False)


def get_identity_uow(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IdentityUnitOfWork:
    """Create identity repositories over the request session.

    Args:
        session: Request-scoped database session.

    Returns:
        Identity unit of work.
    """
    return SqlAlchemyIdentityUnitOfWork(session)


def get_authentication_service(
    uow: Annotated[IdentityUnitOfWork, Depends(get_identity_uow)],
    settings: Annotated[Settings, Depends(get_request_settings)],
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
    uow: Annotated[IdentityUnitOfWork, Depends(get_identity_uow)],
    settings: Annotated[Settings, Depends(get_request_settings)],
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
    request: Request, settings: Annotated[Settings, Depends(get_request_settings)]
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
