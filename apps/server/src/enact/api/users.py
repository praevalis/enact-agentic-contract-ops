"""Authenticated user and organization preference endpoints."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends

from enact.identity import AccessTokenCodec, OrganizationContextService, Principal
from enact.identity.errors import UserNotFoundError
from enact.identity.schemas import (
    MembershipRead,
    OrganizationContextRead,
    OrganizationMembershipRead,
    OrganizationRead,
    OrganizationSwitchUpdate,
    UserRead,
)
from enact.infrastructure.database.uows.identity import SqlAlchemyIdentityUnitOfWork
from enact.platform.settings import Settings

from .identity_support import (
    get_identity_settings,
    get_identity_uow,
    get_principal,
    to_organization_context_read,
)

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserRead)
async def read_me(
    principal: Annotated[Principal, Depends(get_principal)],
    uow: Annotated[SqlAlchemyIdentityUnitOfWork, Depends(get_identity_uow)],
) -> UserRead:
    """Return the authenticated user's public profile.

    Args:
        principal: Validated account principal.
        uow: Identity transaction boundary.

    Returns:
        Public user profile.
    """
    async with uow:
        user = await uow.users.get(principal.user_id)

    if user is None:
        raise UserNotFoundError(principal.user_id)

    return UserRead.model_validate(user)


@router.get('/me/organizations', response_model=list[OrganizationMembershipRead])
async def list_organizations(
    principal: Annotated[Principal, Depends(get_principal)],
    uow: Annotated[SqlAlchemyIdentityUnitOfWork, Depends(get_identity_uow)],
    settings: Annotated[Settings, Depends(get_identity_settings)],
) -> list[OrganizationMembershipRead]:
    """List the user's active organizations for the context switcher.

    Account organization lists are returned in full so the switcher is complete.

    Args:
        principal: Validated account principal.
        uow: Identity transaction boundary.
        settings: Access-token signing configuration.

    Returns:
        Active organization and membership pairs.
    """
    service = OrganizationContextService(
        uow=uow,
        access_token_codec=AccessTokenCodec(settings.auth_secret_key.get_secret_value()),
        access_token_lifetime=timedelta(minutes=15),
    )
    available = await service.list_available(principal.user_id)

    return [
        OrganizationMembershipRead(
            organization=OrganizationRead.model_validate(organization),
            membership=MembershipRead.model_validate(membership),
        )
        for membership, organization in available
    ]


@router.patch('/me/organization', response_model=OrganizationContextRead)
async def switch_organization(
    payload: OrganizationSwitchUpdate,
    principal: Annotated[Principal, Depends(get_principal)],
    uow: Annotated[SqlAlchemyIdentityUnitOfWork, Depends(get_identity_uow)],
    settings: Annotated[Settings, Depends(get_identity_settings)],
) -> OrganizationContextRead:
    """Switch the current session to another active membership.

    Args:
        payload: Target organization identifier.
        principal: Validated account principal.
        uow: Identity transaction boundary.
        settings: Access-token signing configuration.

    Returns:
        New organization context and access token.
    """
    service = OrganizationContextService(
        uow=uow,
        access_token_codec=AccessTokenCodec(settings.auth_secret_key.get_secret_value()),
        access_token_lifetime=timedelta(minutes=15),
    )
    result = await service.switch(
        user_id=principal.user_id,
        session_id=principal.session_id,
        organization_id=payload.organization_id,
    )
    return to_organization_context_read(result)
