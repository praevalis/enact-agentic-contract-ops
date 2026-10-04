"""SQLAlchemy user organization preference repository implementation."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity.entities import UserOrganizationPreference

from ..models.auth import UserOrganizationPreference as UserOrganizationPreferenceModel
from ..session.flush import flush_session


class SqlAlchemyUserOrganizationPreferenceRepository:
    """Persist organization preferences through an asynchronous SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Session used for queries and mutations.
        """
        self._session = session

    async def get(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> UserOrganizationPreference | None:
        """Return one user's preference for an organization.

        Args:
            user_id: User identifier to match.
            organization_id: Organization identifier to match.

        Returns:
            The matching preference, or ``None`` when it does not exist.
        """
        model = await self._session.get(
            UserOrganizationPreferenceModel,
            (user_id, organization_id),
        )
        return to_preference(model) if model is not None else None

    async def list_for_user(self, user_id: UUID) -> Sequence[UserOrganizationPreference]:
        """Return a user's organization preferences.

        Args:
            user_id: User whose preferences should be listed.

        Returns:
            The user's organization preferences, most recently used first.
        """
        result = await self._session.scalars(
            select(UserOrganizationPreferenceModel)
            .where(UserOrganizationPreferenceModel.user_id == user_id)
            .order_by(UserOrganizationPreferenceModel.last_used_at.desc().nullslast())
        )
        return [to_preference(model) for model in result.all()]

    async def record_use(
        self,
        user_id: UUID,
        organization_id: UUID,
        used_at: datetime,
    ) -> UserOrganizationPreference:
        """Record an organization as recently used.

        Args:
            user_id: User whose preference should be updated.
            organization_id: Organization recently used.
            used_at: Timestamp of the organization use.

        Returns:
            The updated preference.
        """
        model = await self._get_or_create(user_id, organization_id)
        model.last_used_at = used_at
        await flush_session(self._session)
        return to_preference(model)

    async def set_preferred(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> UserOrganizationPreference:
        """Set an organization's preference for a user.

        Args:
            user_id: User whose preference should be updated.
            organization_id: Organization to make preferred.

        Returns:
            The updated preference.
        """
        await self._session.execute(
            update(UserOrganizationPreferenceModel)
            .where(UserOrganizationPreferenceModel.user_id == user_id)
            .values(is_preferred=False)
        )
        model = await self._get_or_create(user_id, organization_id)
        model.is_preferred = True
        await flush_session(self._session)
        return to_preference(model)

    async def _get_or_create(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> UserOrganizationPreferenceModel:
        model = await self._session.get(
            UserOrganizationPreferenceModel,
            (user_id, organization_id),
        )

        if model is None:
            model = UserOrganizationPreferenceModel(
                user_id=user_id,
                organization_id=organization_id,
            )
            self._session.add(model)
            await flush_session(self._session)

        return model


def to_preference(model: UserOrganizationPreferenceModel) -> UserOrganizationPreference:
    return UserOrganizationPreference(
        user_id=model.user_id,
        organization_id=model.organization_id,
        is_preferred=model.is_preferred,
        last_used_at=model.last_used_at,
    )
