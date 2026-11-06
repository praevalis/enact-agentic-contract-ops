"""SQLAlchemy customer persistence."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from enact.customers.entities import Customer

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
