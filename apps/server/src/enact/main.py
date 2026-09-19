import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from enact.api.v1 import router as v1_router
from enact.platform.database import DatabaseManager
from enact.platform.logging import configure_logging
from enact.platform.middleware.request_context import RequestContextMiddleware
from enact.platform.object_storage import ObjectStorageManager
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
    app.add_middleware(RequestContextMiddleware)
    app.include_router(v1_router, prefix='/api')
    return app


app = create_app(get_settings())
