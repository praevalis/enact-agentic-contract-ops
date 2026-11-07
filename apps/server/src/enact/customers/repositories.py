"""Customer persistence boundary."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from .entities import Customer, CustomerCursor


class CustomerRepository(Protocol):
    """Persist and resolve tenant-owned customers."""

    async def create(self, *, organization_id: UUID, display_name: str) -> Customer:
        """Create a customer in the active tenant.

        Args:
            organization_id: Organization that owns the customer.
            display_name: Human-readable customer name.

        Returns:
            The created customer.
        """
        ...

    async def get(self, customer_id: UUID) -> Customer | None:
        """Resolve a customer under tenant RLS.

        Args:
            customer_id: Customer identifier to look up.

        Returns:
            The visible customer, or ``None`` when it is unavailable.
        """
        ...

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int,
        cursor: CustomerCursor | None = None,
        status: str | None = None,
        name_query: str | None = None,
    ) -> Sequence[Customer]:
        """Return a newest-first page of customers under tenant RLS.

        Args:
            organization_id: Authorized organization whose customers are listed.
            limit: Maximum rows to retrieve, including the lookahead row.
            cursor: Last position from the preceding page, if any.
            status: Optional lifecycle status filter.
            name_query: Optional case-insensitive display-name search text.

        Returns:
            Customers ordered by creation time and identifier, both descending.
        """
        ...
