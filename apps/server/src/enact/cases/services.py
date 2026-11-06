"""Authorized case creation workflows."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from enact.customers.errors import CustomerNotFoundError
from enact.identity.authentication import Principal
from enact.identity.enums import MembershipRole

from .entities import Case
from .errors import CasePermissionDeniedError, PriorCaseNotFoundError
from .schemas import CaseType
from .unit_of_work import CaseUnitOfWork


class CaseService:
    """Create draft activation and amendment cases."""

    def __init__(self, *, uow: CaseUnitOfWork, clock: Callable[[], datetime] | None = None) -> None:
        """Initialize the case service.

        Args:
            uow: Atomic case creation transaction boundary.
            clock: Time source for audit timestamps.
        """
        self._uow = uow
        self._clock = clock or (lambda: datetime.now(UTC))

    async def create(
        self,
        *,
        principal: Principal,
        customer_id: UUID,
        title: str,
        case_type: CaseType,
        prior_case_id: UUID | None,
    ) -> Case:
        """Create a case for an active same-tenant customer.

        Args:
            principal: Freshly validated tenant principal.
            customer_id: Existing customer identifier.
            title: Case title.
            case_type: Activation or amendment.
            prior_case_id: Required predecessor for an amendment.

        Returns:
            Created draft case.

        Raises:
            CasePermissionDeniedError: If the principal cannot create cases.
            CustomerNotFoundError: If the customer is unavailable or inactive.
            PriorCaseNotFoundError: If the amendment predecessor is unavailable.
        """
        if (
            principal.organization_id is None
            or principal.membership_id is None
            or principal.role not in {MembershipRole.DEAL_DESK, MembershipRole.ADMINISTRATOR}
        ):
            raise CasePermissionDeniedError()

        organization_id = principal.organization_id
        async with self._uow:
            await self._uow.set_organization_context(organization_id)
            customer = await self._uow.customers.get(customer_id)

            if (
                customer is None
                or customer.organization_id != organization_id
                or customer.status != 'active'
            ):
                raise CustomerNotFoundError()

            if case_type == CaseType.AMENDMENT:
                prior = await self._uow.cases.get(prior_case_id) if prior_case_id else None
                if (
                    prior is None
                    or prior.organization_id != organization_id
                    or prior.customer_id != customer_id
                ):
                    raise PriorCaseNotFoundError()

            case = await self._uow.cases.create(
                organization_id=organization_id,
                customer_id=customer_id,
                title=title,
                case_type=case_type.value,
            )

            if prior_case_id is not None:
                await self._uow.lineage.create_amends(
                    organization_id=organization_id,
                    source_case_id=prior_case_id,
                    target_case_id=case.id,
                )

            await self._uow.audit_events.create(
                organization_id=organization_id,
                actor_user_id=principal.user_id,
                action='case.create',
                resource_type='case',
                resource_id=case.id,
                occurred_at=self._clock(),
                details={
                    'case_type': case_type.value,
                    'customer_id': str(customer_id),
                    'prior_case_id': str(prior_case_id) if prior_case_id else None,
                },
            )
            return case
