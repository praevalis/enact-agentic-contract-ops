"""Map identity application results into HTTP read schemas."""

from enact.identity.schemas import (
    MembershipRead,
    OrganizationContextRead,
    OrganizationRead,
    PrincipalRead,
    TokenRead,
    UserRead,
)
from enact.identity.services import AuthenticationResult, OrganizationContextResult


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
