from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from enact.api.v1 import router as v1_router
from enact.platform.database import DatabaseManager
from enact.platform.settings import Settings, get_settings


def create_app(settings: Settings) -> FastAPI:
    """Create the configured FastAPI application.

    Args:
        settings: Validated process configuration.

    Returns:
        The configured FastAPI application.
    """
    database_manager = DatabaseManager(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        try:
            database_manager.initialize()
            yield
        finally:
            await database_manager.dispose()

    app = FastAPI(title='Enact API', version='0.1.0', lifespan=lifespan)

    app.state.settings = settings
    app.state.database_manager = database_manager

    app.include_router(v1_router, prefix='/api')

    return app


app = create_app(get_settings())
