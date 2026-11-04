import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from enact.api.v1 import router as v1_router
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
from enact.infrastructure.database import DatabaseManager
from enact.infrastructure.object_storage import ObjectStorageManager
from enact.platform.logging import configure_logging
from enact.platform.middleware.request_context import RequestContextMiddleware
from enact.platform.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    """Create the configured FastAPI application.

    Args:
        settings: Validated process configuration.

    Returns:
        The configured FastAPI application.
    """
    configure_logging(settings.log_level)

    database_manager = DatabaseManager(settings.database.database_url)
    object_storage_manager = ObjectStorageManager(
        endpoint_url=str(settings.object_storage.endpoint_url),
        access_key=settings.object_storage.access_key.get_secret_value(),
        secret_key=settings.object_storage.secret_key.get_secret_value(),
        bucket=settings.object_storage.bucket,
        region=settings.object_storage.region,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None]:
        """Publish initialized resources captured from the application factory closure.

        The closure retains the validated settings and managers constructed by ``create_app``.
        They are exposed through application state only after initialization succeeds.

        Args:
            application: FastAPI application entering or leaving its active lifespan.

        Yields:
            Control while the initialized application is serving requests.
        """
        try:
            database_manager.initialize()
            await object_storage_manager.initialize()

            application.state.settings = settings
            application.state.database_manager = database_manager
            application.state.object_storage_manager = object_storage_manager

            yield
        finally:
            logger.info('Application resource cleanup started')
            await object_storage_manager.dispose()
            await database_manager.dispose()

    app = FastAPI(title='Enact API', version='0.1.0', lifespan=lifespan)
    web_url = urlsplit(str(settings.web_url))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f'{web_url.scheme}://{web_url.netloc}'],
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PATCH'],
        allow_headers=['Authorization', 'Content-Type'],
    )
    app.add_middleware(RequestContextMiddleware)

    @app.exception_handler(IdentityError)
    async def handle_identity_error(_request: Request, error: IdentityError) -> JSONResponse:
        """Return a stable error code for expected identity failures.

        Args:
            _request: Request that raised the domain error.
            error: Expected identity failure.

        Returns:
            Public error response with a stable code.
        """
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

    app.include_router(v1_router, prefix='/api')
    return app


app = create_app(get_settings())
