"""Local registration, login, refresh, and logout endpoints."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from enact.identity import AuthenticationService, Principal
from enact.identity.errors import InvalidRefreshTokenError
from enact.identity.schemas import LoginCreate, PrincipalRead, UserCreate
from enact.platform.settings import Settings

from .identity_support import (
    get_authentication_service,
    get_identity_settings,
    get_principal,
    require_browser_origin,
    to_principal_read,
)

router = APIRouter(prefix='/auth', tags=['auth'])
REFRESH_COOKIE = 'enact_refresh'
REFRESH_PATH = '/api/v1/auth'


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    """Place the opaque refresh token in a browser-only cookie.

    Args:
        response: HTTP response receiving the cookie.
        token: Newly issued opaque refresh token.
        settings: Runtime environment controlling cookie transport security.
    """
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=30 * 24 * 60 * 60,
        path=REFRESH_PATH,
        secure=settings.environment == 'production',
        httponly=True,
        samesite='lax',
    )


@router.post('/register', response_model=PrincipalRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    response: Response,
    authentication: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_identity_settings)],
) -> PrincipalRead:
    """Register an account and issue an account-only session.

    Args:
        payload: New account credentials and profile.
        response: HTTP response receiving the refresh cookie.
        authentication: Local authentication workflow.
        settings: Runtime cookie settings.

    Returns:
        Account context and short-lived access token.
    """
    result = await authentication.register(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    set_refresh_cookie(response, result.refresh_token, settings)
    return to_principal_read(result)


@router.post('/login', response_model=PrincipalRead)
async def login(
    payload: LoginCreate,
    response: Response,
    authentication: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_identity_settings)],
) -> PrincipalRead:
    """Authenticate and select an available organization when one exists.

    Args:
        payload: Submitted local credentials.
        response: HTTP response receiving the refresh cookie.
        authentication: Local authentication workflow.
        settings: Runtime cookie settings.

    Returns:
        Account or organization context and access token.
    """
    result = await authentication.login(email=payload.email, password=payload.password)
    set_refresh_cookie(response, result.refresh_token, settings)
    return to_principal_read(result)


@router.post('/refresh', response_model=PrincipalRead)
async def refresh(
    response: Response,
    _: Annotated[None, Depends(require_browser_origin)],
    authentication: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_identity_settings)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> PrincipalRead:
    """Rotate the refresh cookie and renew the current access context.

    Args:
        response: HTTP response receiving the replacement cookie.
        _: Browser Origin validation dependency.
        authentication: Local authentication workflow.
        settings: Runtime cookie settings.
        refresh_token: Opaque refresh token from the browser cookie.

    Returns:
        Renewed account or organization context.

    Raises:
        InvalidRefreshTokenError: If the cookie is absent or unusable.
    """
    if refresh_token is None:
        raise InvalidRefreshTokenError()

    result = await authentication.refresh(refresh_token)
    set_refresh_cookie(response, result.refresh_token, settings)
    return to_principal_read(result)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    _: Annotated[None, Depends(require_browser_origin)],
    principal: Annotated[Principal, Depends(get_principal)],
    authentication: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> None:
    """Revoke the current token family and clear its browser cookie.

    Args:
        response: HTTP response whose cookie will be cleared.
        _: Browser Origin validation dependency.
        principal: Validated current account principal.
        authentication: Local authentication workflow.
    """
    await authentication.logout(user_id=principal.user_id, session_id=principal.session_id)
    response.delete_cookie(key=REFRESH_COOKIE, path=REFRESH_PATH)
