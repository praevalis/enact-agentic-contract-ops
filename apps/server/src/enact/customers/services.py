"""Authorized customer workflows."""

from collections.abc import Callable
from datetime import UTC, datetime

from enact.identity.authentication import Principal
from enact.identity.enums import MembershipRole

from .entities import Customer
from .errors import CustomerPermissionDeniedError
from .unit_of_work import CustomerUnitOfWork


class CustomerService:
    """Create tenant-owned customer records."""

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
