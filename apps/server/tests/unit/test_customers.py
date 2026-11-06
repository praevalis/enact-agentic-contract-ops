"""Customer service behavior."""

from collections.abc import Callable
from dataclasses import replace
from typing import cast

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
