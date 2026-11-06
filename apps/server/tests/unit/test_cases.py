"""Case service and schema behavior."""

from collections.abc import Callable
from dataclasses import replace
from typing import cast
from uuid import uuid4

import pytest
from enact.cases.errors import CasePermissionDeniedError, PriorCaseNotFoundError
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
