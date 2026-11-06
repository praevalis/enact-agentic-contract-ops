"""Persistence contracts required by case intake."""

from typing import Protocol
from uuid import UUID

from .entities import Case


class CaseRepository(Protocol):
    """Create and resolve tenant cases."""

    async def create(
        self, *, organization_id: UUID, customer_id: UUID, title: str, case_type: str
    ) -> Case:
        """Create a draft case for an existing customer.

        Args:
            organization_id: Organization that owns the case.
            customer_id: Existing customer receiving the case.
            title: Human-readable case title.
            case_type: Activation or amendment case type.

        Returns:
            The created draft case.
        """
        ...

    async def get(self, case_id: UUID) -> Case | None:
        """Get a case visible in the active tenant context.

        Args:
            case_id: Case identifier to look up.

        Returns:
            The visible case, or ``None`` when it is unavailable.
        """
        ...


class CaseLineageRepository(Protocol):
    """Persist explicit case predecessor links."""

    async def create_amends(
        self, *, organization_id: UUID, source_case_id: UUID, target_case_id: UUID
    ) -> None:
        """Link the prior case to its new amendment.

        Args:
            organization_id: Organization that owns both cases.
            source_case_id: Prior case being amended.
            target_case_id: Newly created amendment case.
        """
        ...
