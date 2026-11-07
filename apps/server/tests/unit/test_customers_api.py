"""Customer route and cursor contract checks."""

from collections.abc import Callable
from typing import cast
from uuid import uuid4

import pytest
from enact.api.customers.dependencies import get_customer_service
from enact.api.customers.routes import router
from enact.api.identity.dependencies import get_principal
from enact.customers.entities import Customer
from enact.customers.services import CustomerService
from enact.customers.unit_of_work import CustomerUnitOfWork
from enact.identity.authentication import Principal
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .conftest import NOW, InMemoryUnitOfWork


@pytest.mark.unit
class TestCustomersApi:
    """Verify versioned customer routes and the opaque list cursor."""

    def test_openapi_exposes_customer_creation_and_list(self) -> None:
        """Publish customer creation and list under the same resource."""
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')

        operations = app.openapi()['paths']['/api/v1/customers']

        assert operations['post']['responses']['201']
        assert operations['get']['responses']['200']

    def test_list_returns_customer_reads(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        """Return a cursor page through the HTTP route."""
        principal = principal_factory('auditor')
        organization_id = principal.organization_id or uuid4()
        first_customer = Customer(uuid4(), organization_id, 'Redwood', 'active', NOW, NOW)
        second_customer = Customer(uuid4(), organization_id, 'Acme', 'active', NOW, NOW)
        in_memory_uow.customers.items[first_customer.id] = first_customer
        in_memory_uow.customers.items[second_customer.id] = second_customer
        service = CustomerService(uow=cast(CustomerUnitOfWork, in_memory_uow))
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')
        app.dependency_overrides[get_principal] = lambda: principal
        app.dependency_overrides[get_customer_service] = lambda: service
        client = TestClient(app)

        first = client.get('/api/v1/customers', params={'page_size': 1})

        assert first.status_code == 200
        assert len(first.json()['items']) == 1
        cursor = first.json()['next_cursor']
        assert isinstance(cursor, str)

        second = client.get('/api/v1/customers', params={'page_size': 1, 'cursor': cursor})

        assert second.status_code == 200
        assert {first.json()['items'][0]['id'], second.json()['items'][0]['id']} == {
            str(first_customer.id),
            str(second_customer.id),
        }
        assert second.json()['next_cursor'] is None

        filtered = client.get(
            '/api/v1/customers', params={'status': 'active', 'name_query': 'WOOD'}
        )
        assert filtered.status_code == 200
        assert [item['id'] for item in filtered.json()['items']] == [str(first_customer.id)]

        invalid = client.get('/api/v1/customers', params={'cursor': 'not-a-cursor'})
        assert invalid.status_code == 422
