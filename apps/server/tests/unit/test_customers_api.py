"""OpenAPI checks for customer creation."""

import pytest
from enact.api.customers.routes import router
from fastapi import FastAPI


@pytest.mark.unit
class TestCustomersApi:
    """Verify the versioned customer creation route."""

    def test_openapi_exposes_customer_creation(self) -> None:
        """Publish customer creation under the customer resource."""
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')

        operation = app.openapi()['paths']['/api/v1/customers']['post']

        assert operation['responses']['201']
