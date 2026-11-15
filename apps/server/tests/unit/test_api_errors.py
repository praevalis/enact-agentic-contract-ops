"""HTTP mappings for domain errors."""

from uuid import uuid4

import pytest
from enact.api.errors import register_error_handlers
from enact.api.v1 import router as v1_router
from enact.cases.errors import CaseNotFoundError, CasePermissionDeniedError, PriorCaseNotFoundError
from enact.customers.errors import CustomerNotFoundError, CustomerPermissionDeniedError
from enact.identity.errors import InvalidAccessTokenError
from enact.platform.errors import EnactError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, EmailStr, Field


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

    def test_request_validation_exposes_locations_without_submitted_values(self) -> None:
        class Payload(BaseModel):
            members: list[int]

        app = FastAPI()
        register_error_handlers(app)

        @app.post('/validate')
        async def validate(_payload: Payload) -> None:
            return None

        response = TestClient(app).post('/validate', json={'members': ['secret-value']})
        body = response.json()

        assert response.status_code == 422
        assert body['code'] == 'validation_error'
        assert body['message'] == 'The request contains invalid values.'
        assert body['issues'][0]['location'] == ['body', 'members', 0]
        assert body['issues'][0]['code'] == 'invalid'
        assert body['issues'][0]['message'] == 'Enter a valid value.'
        assert 'secret-value' not in response.text
        assert 'input' not in body['issues'][0]
        assert 'ctx' not in body['issues'][0]

    def test_request_validation_uses_stable_codes_and_safe_messages(self) -> None:
        class Payload(BaseModel):
            email: EmailStr
            name: str = Field(min_length=1)
            password: str = Field(min_length=8)

        app = FastAPI()
        register_error_handlers(app)

        @app.post('/validate')
        async def validate(_payload: Payload) -> None:
            return None

        response = TestClient(app).post('/validate', json={'email': 'bad', 'name': ''})

        assert response.status_code == 422
        assert response.json()['issues'] == [
            {'location': ['body', 'email'], 'code': 'invalid', 'message': 'Enter a valid value.'},
            {
                'location': ['body', 'name'],
                'code': 'too_short',
                'message': 'The value is too short.',
            },
            {
                'location': ['body', 'password'],
                'code': 'required',
                'message': 'A value is required.',
            },
        ]
        assert 'email address must have an @-sign' not in response.text
        assert 'String should have at least' not in response.text

    def test_versioned_routes_document_validation_response(self) -> None:
        app = FastAPI()
        app.include_router(v1_router, prefix='/api')

        response_schema = app.openapi()['paths']['/api/v1/auth/register']['post']['responses'][
            '422'
        ]
        assert response_schema['content']['application/json']['schema'] == {
            '$ref': '#/components/schemas/ValidationErrorRead'
        }
