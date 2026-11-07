"""Case service and schema behavior."""

from collections.abc import Callable
from dataclasses import replace
from typing import cast
from uuid import uuid4

import pytest
from enact.cases.errors import (
    CaseNotFoundError,
    CasePermissionDeniedError,
    PriorCaseNotFoundError,
)
from enact.cases.schemas import CaseType
from enact.cases.services import CaseService
from enact.cases.unit_of_work import CaseUnitOfWork
from enact.customers.errors import CustomerNotFoundError
from enact.identity.authentication import Principal

from .conftest import NOW, InMemoryUnitOfWork


@pytest.mark.unit
@pytest.mark.asyncio
class TestCaseService:
    """Verify case authorization, tenant checks, and lineage writes."""

    async def test_activation_uses_existing_customer_and_starts_draft(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        uow = in_memory_uow
        service = CaseService(uow=cast(CaseUnitOfWork, uow), clock=lambda: NOW)
        principal = principal_factory('administrator')
        customer = await uow.customers.create(
            organization_id=principal.organization_id or uuid4(), display_name='Redwood'
        )

        case = await service.create(
            principal=principal,
            customer_id=customer.id,
            title='Baseline',
            case_type=CaseType.ACTIVATION,
            prior_case_id=None,
        )

        assert case.status == 'draft'
        assert case.concurrency_version == 1
        assert uow.lineage.edges == []
        assert uow.audit_events.actions == [('case.create', case.id)]
        assert uow.commits == 1

    async def test_amendment_links_prior_case_for_same_customer(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        uow = in_memory_uow
        service = CaseService(uow=cast(CaseUnitOfWork, uow), clock=lambda: NOW)
        principal = principal_factory('deal_desk')
        organization_id = principal.organization_id or uuid4()
        customer = await uow.customers.create(
            organization_id=organization_id, display_name='Redwood'
        )
        prior = await uow.cases.create(
            organization_id=organization_id,
            customer_id=customer.id,
            title='Baseline',
            case_type='activation',
        )

        amendment = await service.create(
            principal=principal,
            customer_id=customer.id,
            title='First amendment',
            case_type=CaseType.AMENDMENT,
            prior_case_id=prior.id,
        )

        assert uow.lineage.edges == [(organization_id, prior.id, amendment.id)]
        assert uow.commits == 1

    async def test_other_customer_prior_case_is_rejected_before_writes(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        uow = in_memory_uow
        service = CaseService(uow=cast(CaseUnitOfWork, uow))
        principal = principal_factory('deal_desk')
        organization_id = principal.organization_id or uuid4()
        customer = await uow.customers.create(
            organization_id=organization_id, display_name='Redwood'
        )
        prior = await uow.cases.create(
            organization_id=organization_id,
            customer_id=uuid4(),
            title='Unrelated',
            case_type='activation',
        )

        with pytest.raises(PriorCaseNotFoundError):
            await service.create(
                principal=principal,
                customer_id=customer.id,
                title='Amendment',
                case_type=CaseType.AMENDMENT,
                prior_case_id=prior.id,
            )

        assert len(uow.cases.items) == 1
        assert uow.audit_events.actions == []
        assert uow.rollbacks == 1

    async def test_archived_or_foreign_customer_is_rejected(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        uow = in_memory_uow
        service = CaseService(uow=cast(CaseUnitOfWork, uow))
        principal = principal_factory('deal_desk')
        foreign = await uow.customers.create(organization_id=uuid4(), display_name='Other tenant')

        with pytest.raises(CustomerNotFoundError):
            await service.create(
                principal=principal,
                customer_id=foreign.id,
                title='Baseline',
                case_type=CaseType.ACTIVATION,
                prior_case_id=None,
            )

        uow.customers.items[foreign.id] = replace(
            foreign, organization_id=principal.organization_id or uuid4(), status='archived'
        )
        with pytest.raises(CustomerNotFoundError):
            await service.create(
                principal=principal,
                customer_id=foreign.id,
                title='Baseline',
                case_type=CaseType.ACTIVATION,
                prior_case_id=None,
            )

        assert uow.cases.items == {}

    async def test_account_only_and_read_only_roles_cannot_create_cases(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        uow = in_memory_uow
        service = CaseService(uow=cast(CaseUnitOfWork, uow))
        account_only = replace(
            principal_factory('deal_desk'), organization_id=None, membership_id=None, role=None
        )

        for principal in (
            account_only,
            principal_factory('auditor'),
            principal_factory('operations_reviewer'),
        ):
            with pytest.raises(CasePermissionDeniedError):
                await service.create(
                    principal=principal,
                    customer_id=uuid4(),
                    title='Baseline',
                    case_type=CaseType.ACTIVATION,
                    prior_case_id=None,
                )

        assert uow.contexts == []
        assert uow.audit_events.actions == []

    @pytest.mark.parametrize(
        'role', ['deal_desk', 'administrator', 'operations_reviewer', 'auditor']
    )
    async def test_all_active_roles_can_read_cases(
        self,
        role: str,
        in_memory_uow: InMemoryUnitOfWork,
        principal_factory: Callable[[str], Principal],
    ) -> None:
        """Permit each active organization role to list and inspect cases."""
        principal = principal_factory(role)
        organization_id = principal.organization_id or uuid4()
        case = await in_memory_uow.cases.create(
            organization_id=organization_id,
            customer_id=uuid4(),
            title='Baseline',
            case_type='activation',
        )
        service = CaseService(uow=cast(CaseUnitOfWork, in_memory_uow))

        detail = await service.get(principal=principal, case_id=case.id)
        page = await service.list(principal=principal, page_size=25)

        assert detail.id == case.id
        assert [item.id for item in page.items] == [case.id]
        assert page.next_cursor is None
        assert in_memory_uow.contexts == [organization_id, organization_id]

    async def test_list_paginates_and_filters_cases(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        """Use a stable cursor while preserving customer, type, and status filters."""
        principal = principal_factory('deal_desk')
        organization_id = principal.organization_id or uuid4()
        customer_id = uuid4()
        activation = await in_memory_uow.cases.create(
            organization_id=organization_id,
            customer_id=customer_id,
            title='Baseline',
            case_type='activation',
        )
        amendment = await in_memory_uow.cases.create(
            organization_id=organization_id,
            customer_id=uuid4(),
            title='Amendment',
            case_type='amendment',
        )
        service = CaseService(uow=cast(CaseUnitOfWork, in_memory_uow))

        first = await service.list(principal=principal, page_size=1)
        assert first.next_cursor is not None

        second = await service.list(principal=principal, page_size=1, cursor=first.next_cursor)
        assert {first.items[0].id, second.items[0].id} == {activation.id, amendment.id}
        assert second.next_cursor is None

        filtered = await service.list(
            principal=principal,
            page_size=25,
            customer_id=customer_id,
            case_type=CaseType.ACTIVATION,
            status='draft',
        )
        assert [item.id for item in filtered.items] == [activation.id]

    async def test_foreign_and_missing_cases_are_indistinguishable(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        """Return the same not-found error for absent and other-tenant cases."""
        principal = principal_factory('auditor')
        foreign = await in_memory_uow.cases.create(
            organization_id=uuid4(),
            customer_id=uuid4(),
            title='Foreign',
            case_type='activation',
        )
        service = CaseService(uow=cast(CaseUnitOfWork, in_memory_uow))

        for case_id in (foreign.id, uuid4()):
            with pytest.raises(CaseNotFoundError):
                await service.get(principal=principal, case_id=case_id)

        assert (await service.list(principal=principal, page_size=25)).items == []

    async def test_account_only_principal_cannot_read_cases(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        """Reject case reads without an active organization membership."""
        account_only = replace(
            principal_factory('deal_desk'), organization_id=None, membership_id=None, role=None
        )
        service = CaseService(uow=cast(CaseUnitOfWork, in_memory_uow))

        with pytest.raises(CasePermissionDeniedError):
            await service.list(principal=account_only, page_size=25)

        with pytest.raises(CasePermissionDeniedError):
            await service.get(principal=account_only, case_id=uuid4())

        assert in_memory_uow.contexts == []
