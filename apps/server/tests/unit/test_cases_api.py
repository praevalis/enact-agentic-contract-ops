"""Case route and cursor contract checks."""

from collections.abc import Callable
from typing import cast
from uuid import uuid4

import pytest
from enact.api.cases.dependencies import get_case_service
from enact.api.cases.routes import router
from enact.api.identity.dependencies import get_principal
from enact.cases.entities import Case
from enact.cases.services import CaseService
from enact.cases.unit_of_work import CaseUnitOfWork
from enact.identity.authentication import Principal
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .conftest import NOW, InMemoryUnitOfWork


@pytest.mark.unit
class TestCasesApi:
    """Verify versioned case routes and the opaque cursor contract."""

    def test_openapi_exposes_case_create_list_and_detail(self) -> None:
        """Publish each case operation under the case resource."""
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')

        paths = app.openapi()['paths']

        assert paths['/api/v1/cases']['post']['responses']['201']
        assert paths['/api/v1/cases']['get']['responses']['200']
        assert paths['/api/v1/cases/{case_id}']['get']['responses']['200']

    def test_list_and_detail_return_case_reads(
        self, in_memory_uow: InMemoryUnitOfWork, principal_factory: Callable[[str], Principal]
    ) -> None:
        """Return a cursor page and the selected case through HTTP routes."""
        principal = principal_factory('auditor')
        organization_id = principal.organization_id or uuid4()
        older = Case(
            uuid4(), organization_id, uuid4(), 'Baseline', 'activation', 'draft', 1, NOW, NOW
        )
        newer = Case(
            uuid4(),
            organization_id,
            older.customer_id,
            'Amendment',
            'amendment',
            'draft',
            1,
            NOW,
            NOW,
            older.id,
        )
        in_memory_uow.cases.items[older.id] = older
        in_memory_uow.cases.items[newer.id] = newer
        service = CaseService(uow=cast(CaseUnitOfWork, in_memory_uow))
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')
        app.dependency_overrides[get_principal] = lambda: principal
        app.dependency_overrides[get_case_service] = lambda: service
        client = TestClient(app)

        first = client.get('/api/v1/cases', params={'page_size': 1})

        assert first.status_code == 200
        assert len(first.json()['items']) == 1
        cursor = first.json()['next_cursor']
        assert isinstance(cursor, str)

        second = client.get('/api/v1/cases', params={'page_size': 1, 'cursor': cursor})
        detail = client.get(f'/api/v1/cases/{newer.id}')

        assert second.status_code == 200
        assert {first.json()['items'][0]['id'], second.json()['items'][0]['id']} == {
            str(older.id),
            str(newer.id),
        }
        assert second.json()['next_cursor'] is None
        assert detail.status_code == 200
        assert detail.json()['prior_case_id'] == str(older.id)

        filtered = client.get(
            '/api/v1/cases',
            params={
                'customer_id': str(older.customer_id),
                'case_type': 'activation',
                'status': 'draft',
            },
        )
        assert filtered.status_code == 200
        assert [item['id'] for item in filtered.json()['items']] == [str(older.id)]

        invalid = client.get('/api/v1/cases', params={'cursor': 'not-a-cursor'})
        assert invalid.status_code == 422
