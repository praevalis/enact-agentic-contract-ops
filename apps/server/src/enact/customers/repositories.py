"""Customer persistence boundary."""

from typing import Protocol
from uuid import UUID

from .entities import Customer


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
