"""SQLAlchemy case and lineage persistence."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from enact.cases.entities import Case

from ..models.cases import Case as CaseModel
from ..models.cases import CaseLineage
from ..session.flush import flush_session


class SqlAlchemyCaseRepository:
    """Create and resolve cases under tenant RLS."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Active tenant-scoped session.
        """
        self._session = session

    async def create(
        self, *, organization_id: UUID, customer_id: UUID, title: str, case_type: str
    ) -> Case:
        """Create a draft case.

        Args:
            organization_id: Owning organization.
            customer_id: Existing customer.
            title: Case title.
            case_type: Activation or amendment.

        Returns:
            Created draft case.
        """
        model = CaseModel(
            organization_id=organization_id,
            customer_id=customer_id,
            title=title,
            case_type=case_type,
        )
        self._session.add(model)
        await flush_session(self._session)
        return to_case(model)

    async def get(self, case_id: UUID) -> Case | None:
        """Resolve one case visible under the active tenant policy.

        Args:
            case_id: Case identifier.

        Returns:
            Case or ``None`` when invisible or absent.
        """
        model = await self._session.get(CaseModel, case_id)
        return to_case(model) if model is not None else None


class SqlAlchemyCaseLineageRepository:
    """Persist explicit amendment lineage edges."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Active tenant-scoped session.
        """
        self._session = session

    async def create_amends(
        self, *, organization_id: UUID, source_case_id: UUID, target_case_id: UUID
    ) -> None:
        """Link a prior case to its amendment.

        Args:
            organization_id: Organization owning both cases.
            source_case_id: Prior case.
            target_case_id: New amendment case.
        """
        self._session.add(
            CaseLineage(
                organization_id=organization_id,
                source_case_id=source_case_id,
                target_case_id=target_case_id,
                relationship_type='amends',
            )
        )
        await flush_session(self._session)


def to_case(model: CaseModel) -> Case:
    """Copy a persistence model into the case boundary."""
    return Case(
        id=model.id,
        organization_id=model.organization_id,
        customer_id=model.customer_id,
        title=model.title,
        case_type=model.case_type,
        status=model.status,
        concurrency_version=model.concurrency_version,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
