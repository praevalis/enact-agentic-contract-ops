"""SQLAlchemy organization repository implementation."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity.entities import Organization
from enact.identity.errors import OrganizationNotFoundError

from ..models.identity import Organization as OrganizationModel
from ..session.flush import flush_session


class SqlAlchemyOrganizationRepository:
    """Persist and retrieve organizations through an asynchronous SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Session used for queries and mutations.
        """
        self._session = session

    async def get(self, organization_id: UUID) -> Organization | None:
        """Return one organization by identifier.

        Args:
            organization_id: Organization identifier to look up.

        Returns:
            The matching organization, or ``None`` when it does not exist.
        """
        model = await self._session.get(OrganizationModel, organization_id)
        return to_organization(model) if model is not None else None

    async def create(self, *, name: str) -> Organization:
        """Create an organization.

        Args:
            name: Display name for the organization.

        Returns:
            The created organization.
        """
        model = OrganizationModel(name=name)
        self._session.add(model)
        await flush_session(self._session)
        return to_organization(model)

    async def update_profile(self, organization_id: UUID, *, name: str) -> Organization:
        """Update editable organization profile fields.

        Args:
            organization_id: Organization identifier to update.
            name: Replacement display name.

        Returns:
            The updated organization.

        Raises:
            OrganizationNotFoundError: If the organization does not exist.
        """
        model = await self._session.get(OrganizationModel, organization_id)

        if model is None:
            raise OrganizationNotFoundError(organization_id)

        model.name = name
        await flush_session(self._session)

        return to_organization(model)

    async def suspend(self, organization_id: UUID) -> None:
        """Suspend an organization without deleting its history.

        Args:
            organization_id: Organization identifier to suspend.

        Raises:
            OrganizationNotFoundError: If the organization does not exist.
        """
        await self._set_status(organization_id, 'suspended')

    async def archive(self, organization_id: UUID) -> None:
        """Archive an organization without deleting its history.

        Args:
            organization_id: Organization identifier to archive.

        Raises:
            OrganizationNotFoundError: If the organization does not exist.
        """
        await self._set_status(organization_id, 'archived')

    async def _set_status(self, organization_id: UUID, status: str) -> None:
        model = await self._session.get(OrganizationModel, organization_id)

        if model is None:
            raise OrganizationNotFoundError(organization_id)

        model.status = status
        await flush_session(self._session)


def to_organization(model: OrganizationModel) -> Organization:
    return Organization(
        id=model.id,
        name=model.name,
        status=model.status,
    )
