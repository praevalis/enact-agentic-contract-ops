"""SQLAlchemy case and lineage persistence."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from enact.cases.entities import Case, CaseCursor

from ..models.cases import Case as CaseModel
from ..models.cases import CaseLineage
from ..session.flush import flush_session


class SqlAlchemyCaseRepository:
    """Create, retrieve, and list cases under tenant RLS."""

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
        prior_case_id = (
            select(CaseLineage.source_case_id)
            .where(
                CaseLineage.target_case_id == CaseModel.id,
                CaseLineage.relationship_type == 'amends',
            )
            .correlate(CaseModel)
            .scalar_subquery()
        )
        row = (
            await self._session.execute(
                select(CaseModel, prior_case_id).where(CaseModel.id == case_id)
            )
        ).one_or_none()
        return to_case(row[0], row[1]) if row is not None else None

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int,
        cursor: CaseCursor | None = None,
        customer_id: UUID | None = None,
        case_type: str | None = None,
        status: str | None = None,
    ) -> Sequence[Case]:
        """List a bounded case page under RLS and explicit tenant scope.

        Args:
            organization_id: Authorized organization whose cases are listed.
            limit: Maximum rows to retrieve, including one lookahead row.
            cursor: Last position from the previous page.
            customer_id: Optional customer filter.
            case_type: Optional case type filter.
            status: Optional status filter.

        Returns:
            Cases sorted by creation time and identifier, both descending.
        """
        prior_case_id = (
            select(CaseLineage.source_case_id)
            .where(
                CaseLineage.target_case_id == CaseModel.id,
                CaseLineage.relationship_type == 'amends',
            )
            .correlate(CaseModel)
            .scalar_subquery()
        )
        statement = select(CaseModel, prior_case_id).where(
            CaseModel.organization_id == organization_id
        )

        if customer_id is not None:
            statement = statement.where(CaseModel.customer_id == customer_id)

        if case_type is not None:
            statement = statement.where(CaseModel.case_type == case_type)

        if status is not None:
            statement = statement.where(CaseModel.status == status)

        if cursor is not None:
            statement = statement.where(
                or_(
                    CaseModel.created_at < cursor.created_at,
                    and_(
                        CaseModel.created_at == cursor.created_at,
                        CaseModel.id < cursor.id,
                    ),
                )
            )

        rows = (
            await self._session.execute(
                statement.order_by(CaseModel.created_at.desc(), CaseModel.id.desc()).limit(limit)
            )
        ).all()
        return [to_case(model, predecessor) for model, predecessor in rows]


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


def to_case(model: CaseModel, prior_case_id: UUID | None = None) -> Case:
    """Copy a persistence model and its predecessor into the case boundary."""
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
        prior_case_id=prior_case_id,
    )
