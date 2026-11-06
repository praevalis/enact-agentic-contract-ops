"""OpenAPI checks for case creation."""

import pytest
from enact.api.cases.routes import router
from fastapi import FastAPI


@pytest.mark.unit
class TestCasesApi:
    """Verify the versioned case creation route."""

    def test_openapi_exposes_case_creation(self) -> None:
        """Publish case creation under the case resource."""
        app = FastAPI()
        app.include_router(router, prefix='/api/v1')

        operation = app.openapi()['paths']['/api/v1/cases']['post']

        assert operation['responses']['201']
