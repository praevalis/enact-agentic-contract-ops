"""SQLAlchemy persistence for organization invitation codes."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity.entities import OrganizationInvitation

from ..models.auth import OrganizationInvitation as OrganizationInvitationModel
from ..session.flush import flush_session


class SqlAlchemyOrganizationInvitationRepository:
    """Create and redeem tenant-owned invitation codes."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Session used for queries and mutations.
        """
        self._session = session

    async def create(
        self,
        *,
        organization_id: UUID,
        code_digest: str,
        role: str,
        created_by_user_id: UUID,
        expires_at: datetime,
    ) -> OrganizationInvitation:
        """Create an invitation under the current tenant scope.

        Args:
            organization_id: Organization receiving the new member.
            code_digest: SHA-256 digest of the bearer code.
            role: Role granted upon redemption.
            created_by_user_id: Administrator issuing the invitation.
            expires_at: Time after which the code cannot be used.

        Returns:
            The persisted invitation.
        """
        model = OrganizationInvitationModel(
            organization_id=organization_id,
            code_digest=code_digest,
            role=role,
            created_by_user_id=created_by_user_id,
            expires_at=expires_at,
        )
        self._session.add(model)
        await flush_session(self._session)

        return to_organization_invitation(model)

    async def redeem(
        self, *, code_digest: str, user_id: UUID, redeemed_at: datetime
    ) -> OrganizationInvitation | None:
        """Atomically redeem an unexpired, unused invitation.

        Args:
            code_digest: Digest of the presented bearer code.
            user_id: User accepting the invitation.
            redeemed_at: Redemption time.

        Returns:
            The claimed invitation or ``None`` when unavailable.
        """
        model = await self._session.scalar(
            update(OrganizationInvitationModel)
            .where(
                OrganizationInvitationModel.code_digest == code_digest,
                OrganizationInvitationModel.redeemed_at.is_(None),
                OrganizationInvitationModel.expires_at > redeemed_at,
            )
            .values(redeemed_by_user_id=user_id, redeemed_at=redeemed_at)
            .returning(OrganizationInvitationModel)
        )

        return to_organization_invitation(model) if model is not None else None


def to_organization_invitation(model: OrganizationInvitationModel) -> OrganizationInvitation:
    """Map an invitation ORM row to its domain entity.

    Args:
        model: Persisted invitation row.

    Returns:
        Invitation entity.
    """
    return OrganizationInvitation(
        id=model.id,
        organization_id=model.organization_id,
        code_digest=model.code_digest,
        role=model.role,
        created_by_user_id=model.created_by_user_id,
        expires_at=model.expires_at,
        redeemed_by_user_id=model.redeemed_by_user_id,
        redeemed_at=model.redeemed_at,
    )
