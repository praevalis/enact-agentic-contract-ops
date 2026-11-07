"""Map application errors to stable HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from enact.cases.errors import CaseError, CaseNotFoundError, PriorCaseNotFoundError
from enact.customers.errors import (
    CustomerError,
    CustomerNotFoundError,
)
from enact.identity.errors import (
    AuthSessionInactiveError,
    AuthSessionNotFoundError,
    IdentityError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidInvitationCodeError,
    InvalidRefreshTokenError,
    MembershipAlreadyExistsError,
    OrganizationNotFoundError,
    UserEmailAlreadyExistsError,
    UserNotFoundError,
)


def register_error_handlers(app: FastAPI) -> None:
    """Install HTTP mappings for expected application failures.

    Args:
        app: FastAPI application receiving the handlers.
    """

    @app.exception_handler(IdentityError)
    async def handle_identity_error(_request: Request, error: IdentityError) -> JSONResponse:
        """Return the established status and stable code for identity errors."""
        if isinstance(
            error,
            (
                InvalidAccessTokenError,
                InvalidCredentialsError,
                InvalidRefreshTokenError,
                AuthSessionInactiveError,
                AuthSessionNotFoundError,
            ),
        ):
            response_status = 401
        elif isinstance(error, (MembershipAlreadyExistsError, UserEmailAlreadyExistsError)):
            response_status = 409
        elif isinstance(error, (OrganizationNotFoundError, UserNotFoundError)):
            response_status = 404
        elif isinstance(error, InvalidInvitationCodeError):
            response_status = 400
        else:
            response_status = 403

        return JSONResponse(
            status_code=response_status,
            content={'code': error.code, 'message': error.message},
        )

    @app.exception_handler(CaseError)
    async def handle_case_error(_request: Request, error: CaseError) -> JSONResponse:
        """Return the status and stable code for case errors."""
        response_status = (
            404 if isinstance(error, (CaseNotFoundError, PriorCaseNotFoundError)) else 403
        )

        return JSONResponse(
            status_code=response_status,
            content={'code': error.code, 'message': error.message},
        )

    @app.exception_handler(CustomerError)
    async def handle_customer_error(_request: Request, error: CustomerError) -> JSONResponse:
        """Return the status and stable code for customer errors."""
        response_status = 404 if isinstance(error, CustomerNotFoundError) else 403

        return JSONResponse(
            status_code=response_status,
            content={'code': error.code, 'message': error.message},
        )
