"""Authorized customer workflows."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from enact.identity.authentication import Principal
from enact.identity.enums import MembershipRole

from .entities import Customer, CustomerCursor, CustomerPage
from .errors import CustomerPermissionDeniedError
from .unit_of_work import CustomerUnitOfWork


class CustomerService:
    """Create and list tenant-owned customer records."""

    def __init__(
        self, *, uow: CustomerUnitOfWork, clock: Callable[[], datetime] | None = None
    ) -> None:
        """Initialize the service.

        Args:
            uow: Customer transaction boundary.
            clock: Time source for audit timestamps.
        """
        self._uow = uow
        self._clock = clock or (lambda: datetime.now(UTC))

    async def create(self, *, principal: Principal, display_name: str) -> Customer:
        """Create and audit a customer independently of case creation.

        Args:
            principal: Freshly validated tenant principal.
            display_name: Customer display name.

        Returns:
            Created customer.

        Raises:
            CustomerPermissionDeniedError: If principal cannot create customers.
        """
        if (
            principal.organization_id is None
            or principal.membership_id is None
            or principal.role not in {MembershipRole.DEAL_DESK, MembershipRole.ADMINISTRATOR}
        ):
            raise CustomerPermissionDeniedError()

        organization_id = principal.organization_id
        async with self._uow:
            await self._uow.set_organization_context(organization_id)
            customer = await self._uow.customers.create(
                organization_id=organization_id, display_name=display_name
            )

            await self._uow.audit_events.create(
                organization_id=organization_id,
                actor_user_id=principal.user_id,
                action='customer.create',
                resource_type='customer',
                resource_id=customer.id,
                occurred_at=self._clock(),
                details={},
            )

            return customer

    async def list(
        self,
        *,
        principal: Principal,
        page_size: int,
        cursor: CustomerCursor | None = None,
        status: str | None = None,
        name_query: str | None = None,
    ) -> CustomerPage:
        """Return a newest-first page of customers in the active organization.

        Args:
            principal: Freshly validated organization principal.
            page_size: Number of customers to include, from 1 through 100.
            cursor: Last position from a previous page.
            status: Optional lifecycle status filter.
            name_query: Optional case-insensitive display-name search text.

        Returns:
            Page of customers and an optional next position.

        Raises:
            CustomerPermissionDeniedError: If the principal has no customer read access.
            ValueError: If the requested page size is outside the supported range.
        """
        if not 1 <= page_size <= 100:
            raise ValueError('Page size must be between 1 and 100.')

        organization_id = self._read_organization(principal)

        async with self._uow:
            await self._uow.set_organization_context(organization_id)
            rows = await self._uow.customers.list_for_organization(
                organization_id=organization_id,
                limit=page_size + 1,
                cursor=cursor,
                status=status,
                name_query=name_query,
            )

            items = list(rows[:page_size])
            next_cursor = (
                CustomerCursor(id=items[-1].id, created_at=items[-1].created_at)
                if len(rows) > page_size
                else None
            )
            return CustomerPage(items=items, next_cursor=next_cursor)

    @staticmethod
    def _read_organization(principal: Principal) -> UUID:
        """Authorize customer reads for every active organization role.

        Args:
            principal: Freshly validated principal.

        Returns:
            Active organization identifier.

        Raises:
            CustomerPermissionDeniedError: If the principal lacks organization customer access.
        """
        if (
            principal.organization_id is None
            or principal.membership_id is None
            or principal.role not in set(MembershipRole)
        ):
            raise CustomerPermissionDeniedError()

        return principal.organization_id
