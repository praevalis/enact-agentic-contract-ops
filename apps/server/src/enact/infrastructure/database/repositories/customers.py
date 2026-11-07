"""SQLAlchemy customer persistence."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from enact.customers.entities import Customer, CustomerCursor

from ..models.customers import Customer as CustomerModel
from ..session.flush import flush_session


class SqlAlchemyCustomerRepository:
    """Create and resolve customers under tenant RLS."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Active tenant-scoped session.
        """
        self._session = session

    async def create(self, *, organization_id: UUID, display_name: str) -> Customer:
        """Create a customer in the current tenant transaction.

        Args:
            organization_id: Owning organization.
            display_name: Customer display name.

        Returns:
            Created customer.
        """
        model = CustomerModel(organization_id=organization_id, display_name=display_name)
        self._session.add(model)
        await flush_session(self._session)
        return to_customer(model)

    async def get(self, customer_id: UUID) -> Customer | None:
        """Resolve one customer visible under the active tenant policy.

        Args:
            customer_id: Customer identifier.

        Returns:
            Customer or ``None`` when invisible or absent.
        """
        model = await self._session.get(CustomerModel, customer_id)
        return to_customer(model) if model is not None else None

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int,
        cursor: CustomerCursor | None = None,
        status: str | None = None,
        name_query: str | None = None,
    ) -> Sequence[Customer]:
        """List a bounded customer page under RLS and explicit tenant scope.

        Args:
            organization_id: Authorized organization whose customers are listed.
            limit: Maximum rows to retrieve, including one lookahead row.
            cursor: Last position from the preceding page, if any.
            status: Optional lifecycle status filter.
            name_query: Optional case-insensitive display-name search text.

        Returns:
            Customers ordered by creation time and identifier, both descending.
        """
        statement = select(CustomerModel).where(CustomerModel.organization_id == organization_id)

        if status is not None:
            statement = statement.where(CustomerModel.status == status)

        if name_query is not None:
            statement = statement.where(
                CustomerModel.display_name.icontains(name_query, autoescape=True)
            )

        if cursor is not None:
            statement = statement.where(
                or_(
                    CustomerModel.created_at < cursor.created_at,
                    and_(
                        CustomerModel.created_at == cursor.created_at,
                        CustomerModel.id < cursor.id,
                    ),
                )
            )

        models = (
            await self._session.scalars(
                statement.order_by(CustomerModel.created_at.desc(), CustomerModel.id.desc()).limit(
                    limit
                )
            )
        ).all()
        return [to_customer(model) for model in models]


def to_customer(model: CustomerModel) -> Customer:
    """Copy a persistence model into the customer boundary."""
    return Customer(
        id=model.id,
        organization_id=model.organization_id,
        display_name=model.display_name,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
