"""Customer service behavior."""

from collections.abc import Callable
from dataclasses import replace
from typing import cast
from uuid import uuid4

import pytest
from enact.customers.errors import CustomerPermissionDeniedError
from enact.customers.services import CustomerService
from enact.customers.unit_of_work import CustomerUnitOfWork
from enact.identity.authentication import Principal

from .conftest import NOW, InMemoryUnitOfWork


@pytest.mark.unit
@pytest.mark.asyncio
class TestCustomerService:
    """Verify independent customer creation and authorization."""

    async def test_customer_creation_is_separate_and_audited(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        uow = in_memory_uow
        service = CustomerService(uow=cast(CustomerUnitOfWork, uow), clock=lambda: NOW)
        principal = principal_factory('deal_desk')

        customer = await service.create(principal=principal, display_name='Redwood')

        assert customer.organization_id == principal.organization_id
        assert uow.cases.items == {}
        assert uow.audit_events.actions == [('customer.create', customer.id)]
        assert uow.contexts == [principal.organization_id]
        assert uow.commits == 1

    async def test_account_only_and_read_only_roles_cannot_write(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        uow = in_memory_uow
        service = CustomerService(uow=cast(CustomerUnitOfWork, uow))
        account_only = replace(
            principal_factory('deal_desk'), organization_id=None, membership_id=None, role=None
        )

        for principal in (
            account_only,
            principal_factory('auditor'),
            principal_factory('operations_reviewer'),
        ):
            with pytest.raises(CustomerPermissionDeniedError):
                await service.create(principal=principal, display_name='Redwood')

        assert uow.contexts == []
        assert uow.audit_events.actions == []

    @pytest.mark.parametrize(
        'role', ['deal_desk', 'administrator', 'operations_reviewer', 'auditor']
    )
    async def test_all_active_roles_can_list_customers(
        self,
        role: str,
        in_memory_uow: InMemoryUnitOfWork,
        principal_factory: Callable[[str], Principal],
    ) -> None:
        """Permit every active organization role to read its customer list."""
        principal = principal_factory(role)
        organization_id = principal.organization_id or uuid4()
        own = await in_memory_uow.customers.create(
            organization_id=organization_id, display_name='Redwood'
        )
        await in_memory_uow.customers.create(organization_id=uuid4(), display_name='Other tenant')
        service = CustomerService(uow=cast(CustomerUnitOfWork, in_memory_uow))

        page = await service.list(principal=principal, page_size=25)

        assert [item.id for item in page.items] == [own.id]
        assert page.next_cursor is None
        assert in_memory_uow.contexts == [organization_id]

    async def test_list_paginates_customers_with_tied_timestamps(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        """Use customer IDs to continue a page when creation times match."""
        principal = principal_factory('deal_desk')
        organization_id = principal.organization_id or uuid4()
        first_customer = await in_memory_uow.customers.create(
            organization_id=organization_id, display_name='Redwood'
        )
        second_customer = await in_memory_uow.customers.create(
            organization_id=organization_id, display_name='Acme'
        )
        service = CustomerService(uow=cast(CustomerUnitOfWork, in_memory_uow))

        first = await service.list(principal=principal, page_size=1)
        assert first.next_cursor is not None
        second = await service.list(principal=principal, page_size=1, cursor=first.next_cursor)

        assert [first.items[0].id, second.items[0].id] == sorted(
            (first_customer.id, second_customer.id), reverse=True
        )
        assert second.next_cursor is None

        in_memory_uow.customers.items[second_customer.id] = replace(
            second_customer, status='archived'
        )
        filtered = await service.list(
            principal=principal,
            page_size=25,
            status='active',
            name_query='WOOD',
        )
        assert [item.id for item in filtered.items] == [first_customer.id]

    async def test_account_only_principal_cannot_list_customers(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        """Reject reads without an active organization membership."""
        account_only = replace(
            principal_factory('deal_desk'), organization_id=None, membership_id=None, role=None
        )
        service = CustomerService(uow=cast(CustomerUnitOfWork, in_memory_uow))

        with pytest.raises(CustomerPermissionDeniedError):
            await service.list(principal=account_only, page_size=25)

        assert in_memory_uow.contexts == []
