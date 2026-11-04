"""Organization setup and administrator invitation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from enact.identity import OnboardingService, Principal
from enact.identity.errors import MembershipPermissionDeniedError
from enact.identity.schemas import (
    OrganizationContextRead,
    OrganizationCreate,
    OrganizationInvitationCreate,
    OrganizationInvitationRead,
    OrganizationJoinCreate,
)

from .identity_support import get_onboarding_service, get_principal, to_organization_context_read

router = APIRouter(prefix='/organizations', tags=['organizations'])


@router.post('', response_model=OrganizationContextRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    principal: Annotated[Principal, Depends(get_principal)],
    onboarding: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OrganizationContextRead:
    """Create an organization and activate its creator as administrator.

    Args:
        payload: Organization name.
        principal: Validated account principal.
        onboarding: Organization setup workflow.

    Returns:
        Active organization context.
    """
    result = await onboarding.create_organization(
        user_id=principal.user_id,
        session_id=principal.session_id,
        name=payload.name,
    )
    return to_organization_context_read(result)


@router.post('/join', response_model=OrganizationContextRead)
async def join_organization(
    payload: OrganizationJoinCreate,
    principal: Annotated[Principal, Depends(get_principal)],
    onboarding: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OrganizationContextRead:
    """Redeem a manually shared invitation code.

    Args:
        payload: Submitted invitation code.
        principal: Validated account principal.
        onboarding: Organization setup workflow.

    Returns:
        Active organization context.
    """
    result = await onboarding.join_organization(
        user_id=principal.user_id,
        session_id=principal.session_id,
        code=payload.code,
    )
    return to_organization_context_read(result)


@router.post(
    '/{organization_id}/invitations',
    response_model=OrganizationInvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    organization_id: UUID,
    payload: OrganizationInvitationCreate,
    principal: Annotated[Principal, Depends(get_principal)],
    onboarding: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OrganizationInvitationRead:
    """Issue a one-time code for an administrator to share.

    Args:
        organization_id: Organization receiving the invited user.
        payload: Role to grant upon redemption.
        principal: Validated organization principal.
        onboarding: Invitation issuing workflow.

    Returns:
        Invitation code shown once and its expiry.
    """
    if principal.organization_id != organization_id:
        raise MembershipPermissionDeniedError(organization_id)

    result = await onboarding.issue_invitation(
        actor_user_id=principal.user_id,
        organization_id=organization_id,
        role=payload.role,
    )
    return OrganizationInvitationRead.model_validate(result)
