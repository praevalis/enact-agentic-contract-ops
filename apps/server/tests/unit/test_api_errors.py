"""HTTP mappings for domain errors."""

from uuid import uuid4

import pytest
from enact.api.errors import register_error_handlers
from enact.cases.errors import CaseNotFoundError, CasePermissionDeniedError, PriorCaseNotFoundError
from enact.customers.errors import CustomerNotFoundError, CustomerPermissionDeniedError
from enact.identity.errors import InvalidAccessTokenError
from enact.platform.errors import EnactError
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestErrorHandlers:
    """Keep domain error codes and HTTP statuses stable."""

    @pytest.mark.parametrize(
        ('error', 'expected_status'),
        [
            (InvalidAccessTokenError(), 401),
            (CasePermissionDeniedError(), 403),
            (CaseNotFoundError(uuid4()), 404),
            (PriorCaseNotFoundError(), 404),
            (CustomerPermissionDeniedError(), 403),
            (CustomerNotFoundError(), 404),
        ],
    )
    def test_domain_error_response(self, error: EnactError, expected_status: int) -> None:
        """Map each domain error to its stable code and expected status."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get('/error')
        async def raise_error() -> None:
            raise error

        response = TestClient(app).get('/error')

        assert response.status_code == expected_status
        assert response.json() == {'code': error.code, 'message': error.message}
