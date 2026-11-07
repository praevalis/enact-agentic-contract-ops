"""Authorized case creation and read workflows."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from enact.customers.errors import CustomerNotFoundError
from enact.identity.authentication import Principal
from enact.identity.enums import MembershipRole

from .entities import Case, CaseCursor, CasePage
from .errors import CaseNotFoundError, CasePermissionDeniedError, PriorCaseNotFoundError
from .schemas import CaseType
from .unit_of_work import CaseUnitOfWork


class CaseService:
    """Create and read activation and amendment cases."""

    def __init__(self, *, uow: CaseUnitOfWork, clock: Callable[[], datetime] | None = None) -> None:
        """Initialize the case service.

        Args:
            uow: Case transaction boundary.
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
            return replace(case, prior_case_id=prior_case_id)

    async def get(self, *, principal: Principal, case_id: UUID) -> Case:
        """Return one case visible to an active organization member.

        Args:
            principal: Freshly validated organization principal.
            case_id: Case identifier to look up.

        Returns:
            The case and its amendment predecessor, if any.

        Raises:
            CasePermissionDeniedError: If the principal has no case read access.
            CaseNotFoundError: If the case is absent or belongs to another organization.
        """
        organization_id = self._read_organization(principal)

        async with self._uow:
            await self._uow.set_organization_context(organization_id)
            case = await self._uow.cases.get(case_id)

            if case is None or case.organization_id != organization_id:
                raise CaseNotFoundError(case_id)

            return case

    async def list(
        self,
        *,
        principal: Principal,
        page_size: int,
        cursor: CaseCursor | None = None,
        customer_id: UUID | None = None,
        case_type: CaseType | None = None,
        status: str | None = None,
    ) -> CasePage:
        """Return a newest-first page of cases in the active organization.

        Args:
            principal: Freshly validated organization principal.
            page_size: Number of cases to include, from 1 through 100.
            cursor: Last position from a previous page.
            customer_id: Optional customer filter.
            case_type: Optional activation or amendment filter.
            status: Optional lifecycle status filter.

        Returns:
            Page of cases and an optional next position.

        Raises:
            CasePermissionDeniedError: If the principal has no case read access.
            ValueError: If the requested page size is outside the supported range.
        """
        if not 1 <= page_size <= 100:
            raise ValueError('Page size must be between 1 and 100.')

        organization_id = self._read_organization(principal)

        async with self._uow:
            await self._uow.set_organization_context(organization_id)
            rows = await self._uow.cases.list_for_organization(
                organization_id=organization_id,
                limit=page_size + 1,
                cursor=cursor,
                customer_id=customer_id,
                case_type=case_type.value if case_type is not None else None,
                status=status,
            )

            items = list(rows[:page_size])
            next_cursor = (
                CaseCursor(id=items[-1].id, created_at=items[-1].created_at)
                if len(rows) > page_size
                else None
            )
            return CasePage(items=items, next_cursor=next_cursor)

    @staticmethod
    def _read_organization(principal: Principal) -> UUID:
        """Authorize case reads for every active organization role.

        Args:
            principal: Freshly validated principal.

        Returns:
            Active organization identifier.

        Raises:
            CasePermissionDeniedError: If the principal lacks organization case access.
        """
        if (
            principal.organization_id is None
            or principal.membership_id is None
            or principal.role not in set(MembershipRole)
        ):
            raise CasePermissionDeniedError()

        return principal.organization_id
