"""Shared FastAPI request dependencies."""

from typing import cast

from fastapi import Request

from enact.platform.settings import Settings


def get_request_settings(request: Request) -> Settings:
    """Return application settings captured by the lifespan.

    Args:
        request: Active API request.

    Returns:
        Validated application settings.
    """
    return cast(Settings, request.app.state.settings)
