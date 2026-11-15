"""Organization setup and administrator invitation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from enact.identity import MembershipService, OnboardingService, Principal
from enact.identity.entities import MemberCursor
from enact.identity.errors import MembershipPermissionDeniedError
from enact.identity.schemas import (
    MembershipRead,
    MembershipUpdate,
    OrganizationContextRead,
    OrganizationCreate,
    OrganizationInvitationCreate,
    OrganizationInvitationRead,
    OrganizationJoinCreate,
    OrganizationMemberListRead,
    OrganizationMemberRead,
    OrganizationRead,
    OrganizationUpdate,
)
from enact.identity.services import OrganizationManagementService
from enact.identity.unit_of_work import IdentityUnitOfWork

from ..pagination import decode_cursor, encode_cursor
from .dependencies import get_identity_uow, get_onboarding_service, get_principal
from .mappers import to_organization_context_read

router = APIRouter(prefix='/organizations', tags=['organizations'])


def get_membership_service(
    uow: Annotated[IdentityUnitOfWork, Depends(get_identity_uow)],
) -> MembershipService:
    """Build the organization membership workflow for a request.

    Args:
        uow: Request identity transaction boundary.

    Returns:
        Membership service.
    """
    return MembershipService(uow=uow)


def get_organization_management_service(
    uow: Annotated[IdentityUnitOfWork, Depends(get_identity_uow)],
) -> OrganizationManagementService:
    """Build the organization profile workflow for a request.

    Args:
        uow: Request identity transaction boundary.

    Returns:
        Organization management service.
    """
    return OrganizationManagementService(uow=uow)


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


@router.patch('/{organization_id}', response_model=OrganizationRead)
async def rename_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    principal: Annotated[Principal, Depends(get_principal)],
    management: Annotated[
        OrganizationManagementService, Depends(get_organization_management_service)
    ],
) -> OrganizationRead:
    """Rename the active organization as an administrator.

    Args:
        organization_id: Organization to rename.
        payload: Replacement display name.
        principal: Validated organization principal.
        management: Organization profile workflow.

    Returns:
        Updated organization.
    """
    if principal.organization_id != organization_id:
        raise MembershipPermissionDeniedError(organization_id)

    organization = await management.rename(
        actor_user_id=principal.user_id, organization_id=organization_id, name=payload.name
    )
    return OrganizationRead.model_validate(organization)


@router.get('/{organization_id}/memberships', response_model=OrganizationMemberListRead)
async def list_memberships(
    organization_id: UUID,
    principal: Annotated[Principal, Depends(get_principal)],
    memberships: Annotated[MembershipService, Depends(get_membership_service)],
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> OrganizationMemberListRead:
    """List a cursor page of active members in the selected organization.

    Args:
        organization_id: Organization to list.
        principal: Validated organization principal.
        memberships: Membership workflow.
        page_size: Maximum members to return.
        cursor: Opaque position after the previous page.

    Returns:
        Active members, total count, and next cursor.

    Raises:
        HTTPException: If the supplied cursor is invalid.
    """
    if principal.organization_id != organization_id:
        raise MembershipPermissionDeniedError(organization_id)

    try:
        if cursor is not None:
            created_at, identifier = decode_cursor(cursor)
            position = MemberCursor(id=identifier, created_at=created_at)
        else:
            position = None
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    page = await memberships.list_active(
        actor_user_id=principal.user_id,
        organization_id=organization_id,
        page_size=page_size,
        cursor=position,
    )
    return OrganizationMemberListRead(
        items=[OrganizationMemberRead.model_validate(item) for item in page.items],
        total_count=page.total_count,
        next_cursor=(
            encode_cursor(page.next_cursor.created_at, page.next_cursor.id)
            if page.next_cursor is not None
            else None
        ),
    )


@router.patch('/{organization_id}/memberships/{membership_id}', response_model=MembershipRead)
async def change_membership_role(
    organization_id: UUID,
    membership_id: UUID,
    payload: MembershipUpdate,
    principal: Annotated[Principal, Depends(get_principal)],
    memberships: Annotated[MembershipService, Depends(get_membership_service)],
) -> MembershipRead:
    """Change one active member's role as an administrator.

    Args:
        organization_id: Organization containing the membership.
        membership_id: Membership to update.
        payload: Replacement role.
        principal: Validated organization principal.
        memberships: Membership workflow.

    Returns:
        Updated membership.
    """
    if principal.organization_id != organization_id:
        raise MembershipPermissionDeniedError(organization_id)

    changed = await memberships.change_role(
        actor_user_id=principal.user_id,
        organization_id=organization_id,
        membership_id=membership_id,
        role=payload.role,
    )
    return MembershipRead.model_validate(changed)


@router.delete(
    '/{organization_id}/memberships/{membership_id}', status_code=status.HTTP_204_NO_CONTENT
)
async def remove_membership(
    organization_id: UUID,
    membership_id: UUID,
    principal: Annotated[Principal, Depends(get_principal)],
    memberships: Annotated[MembershipService, Depends(get_membership_service)],
) -> None:
    """Revoke one member's access as an administrator.

    Args:
        organization_id: Organization containing the membership.
        membership_id: Membership to revoke.
        principal: Validated organization principal.
        memberships: Membership workflow.
    """
    if principal.organization_id != organization_id:
        raise MembershipPermissionDeniedError(organization_id)

    await memberships.revoke(
        actor_user_id=principal.user_id,
        organization_id=organization_id,
        membership_id=membership_id,
    )
