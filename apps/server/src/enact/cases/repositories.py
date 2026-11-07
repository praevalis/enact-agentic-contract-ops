"""Case persistence contracts."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from .entities import Case, CaseCursor


class CaseRepository(Protocol):
    """Create, retrieve, and list tenant cases."""

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
        """Return a newest-first, tenant-scoped page of cases.

        Args:
            organization_id: Authorized organization whose cases are listed.
            limit: Maximum rows to retrieve, including the lookahead row.
            cursor: Last position from the preceding page, if any.
            customer_id: Optional customer filter.
            case_type: Optional activation or amendment filter.
            status: Optional lifecycle status filter.

        Returns:
            Cases ordered by creation time and identifier, both descending.
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
