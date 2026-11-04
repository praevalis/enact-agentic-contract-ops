"""SQLAlchemy membership repository implementation."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity.entities import Membership
from enact.identity.errors import (
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
    MembershipTransitionError,
)

from ..models.identity import Membership as MembershipModel
from ..session.flush import flush_session

_CONSTRAINT_ERRORS = {'uq_membership_organization_user': MembershipAlreadyExistsError}


class SqlAlchemyMembershipRepository:
    """Persist and resolve memberships through an asynchronous SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Session used for queries and mutations.
        """
        self._session = session

    async def get(self, membership_id: UUID) -> Membership | None:
        """Return one membership by identifier.

        Args:
            membership_id: Membership identifier to look up.

        Returns:
            The matching membership, or ``None`` when it does not exist.
        """
        model = await self._session.get(MembershipModel, membership_id)
        return to_membership(model) if model is not None else None

    async def list_for_user(self, user_id: UUID) -> Sequence[Membership]:
        """Return active memberships available to a user.

        Args:
            user_id: User whose memberships should be listed.

        Returns:
            The user's active memberships. RLS supplies the user discovery scope.
        """
        result = await self._session.scalars(
            select(MembershipModel).where(
                MembershipModel.user_id == user_id, MembershipModel.status == 'active'
            )
        )
        return [to_membership(model) for model in result.all()]

    async def get_for_user_and_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> Membership | None:
        """Return a user's membership in one organization, if present.

        Args:
            user_id: User identifier to match.
            organization_id: Organization identifier to match.

        Returns:
            The matching membership, or ``None`` when it does not exist.
        """
        model = await self._session.scalar(
            select(MembershipModel).where(
                MembershipModel.user_id == user_id,
                MembershipModel.organization_id == organization_id,
            )
        )
        return to_membership(model) if model is not None else None

    async def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        role: str,
    ) -> Membership:
        """Create an organization membership.

        Args:
            user_id: User receiving the membership.
            organization_id: Organization containing the membership.
            role: Initial membership role.

        Returns:
            The created membership.
        """
        model = MembershipModel(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
        )
        self._session.add(model)
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)
        return to_membership(model)

    async def change_role(self, membership_id: UUID, role: str) -> Membership:
        """Change a membership's role.

        Args:
            membership_id: Membership identifier to update.
            role: Replacement membership role.

        Returns:
            The updated membership.

        Raises:
            MembershipNotFoundError: If the membership does not exist.
        """
        model = await self._session.get(MembershipModel, membership_id)

        if model is None:
            raise MembershipNotFoundError(membership_id)

        model.role = role
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)

        return to_membership(model)

    async def suspend(self, membership_id: UUID) -> Membership:
        """Suspend an active membership without deleting its history.

        Args:
            membership_id: Membership identifier to suspend.

        Returns:
            The suspended membership.

        Raises:
            MembershipNotFoundError: If the membership does not exist.
            MembershipTransitionError: If the membership is not active.
        """
        return await self._set_status(membership_id, 'suspended', {'active'}, 'suspended')

    async def resume(self, membership_id: UUID) -> Membership:
        """Resume a suspended membership with its retained role.

        Args:
            membership_id: Membership identifier to resume.

        Returns:
            The active membership.

        Raises:
            MembershipNotFoundError: If the membership does not exist.
            MembershipTransitionError: If the membership is not suspended.
        """
        return await self._set_status(membership_id, 'active', {'suspended'}, 'resumed')

    async def revoke(self, membership_id: UUID) -> Membership:
        """Revoke an active or suspended membership without deleting its history.

        Args:
            membership_id: Membership identifier to revoke.

        Returns:
            The revoked membership.

        Raises:
            MembershipNotFoundError: If the membership does not exist.
            MembershipTransitionError: If the membership is already revoked.
        """
        return await self._set_status(membership_id, 'revoked', {'active', 'suspended'}, 'revoked')

    async def regrant(self, membership_id: UUID, role: str) -> Membership:
        """Restore a revoked membership with a newly selected role.

        Args:
            membership_id: Membership identifier to regrant.
            role: Role selected for the restored access.

        Returns:
            The active membership.

        Raises:
            MembershipNotFoundError: If the membership does not exist.
            MembershipTransitionError: If the membership is not revoked.
        """
        return await self._set_status(membership_id, 'active', {'revoked'}, 'regranted', role)

    async def _set_status(
        self,
        membership_id: UUID,
        status: str,
        allowed_statuses: set[str],
        action: str,
        role: str | None = None,
    ) -> Membership:
        model = await self._session.get(MembershipModel, membership_id, with_for_update=True)

        if model is None:
            raise MembershipNotFoundError(membership_id)

        if model.status not in allowed_statuses:
            raise MembershipTransitionError(membership_id, action)

        model.status = status

        if role is not None:
            model.role = role

        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)

        return to_membership(model)


def to_membership(model: MembershipModel) -> Membership:
    return Membership(
        id=model.id,
        user_id=model.user_id,
        organization_id=model.organization_id,
        role=model.role,
        status=model.status,
    )
