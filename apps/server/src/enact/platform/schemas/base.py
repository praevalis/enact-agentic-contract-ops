"""Base classes for API request and response schemas."""

from pydantic import BaseModel, ConfigDict


class BaseWrite(BaseModel):
    """Base for client-submitted API schemas."""

    model_config = ConfigDict(extra='forbid')


class BaseRead(BaseWrite):
    """Base for API response schemas."""

    model_config = ConfigDict(extra='forbid', from_attributes=True)
