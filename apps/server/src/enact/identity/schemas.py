"""Pydantic schemas for identity and authentication workflows."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import EmailStr, Field, StringConstraints

from enact.platform.schemas import BaseRead, BaseWrite

from .enums import MembershipRole, MembershipStatus


class MembershipRead(BaseRead):
    """An organization's membership exposed to the authenticated user."""

    organization_id: UUID
    role: MembershipRole
    status: MembershipStatus


class OrganizationRead(BaseRead):
    """An organization available to the authenticated user."""

    id: UUID
    name: str
    status: str


class UserRead(BaseRead):
    """The authenticated user's safe public identity."""

    id: UUID
    email: str
    display_name: str
    status: str


class LoginCreate(BaseWrite):
    """Credentials submitted to create an authenticated session."""

    email: Annotated[
        EmailStr,
        StringConstraints(strip_whitespace=True, to_lower=True),
    ]
    password: str = Field(min_length=1, max_length=1024)


class TokenRead(BaseRead):
    """Short-lived access-token result returned after authentication."""

    access_token: str
    token_type: str = 'Bearer'
    expires_at: datetime
    organization_id: UUID


class OrganizationSwitchUpdate(BaseWrite):
    """Request to change the organization context of the current session."""

    organization_id: UUID


class PrincipalRead(BaseRead):
    """Authenticated principal and its active organization context."""

    user: UserRead
    organization: OrganizationRead
    membership: MembershipRead
    token: TokenRead


class AccessTokenClaims(BaseRead):
    """Validated claims carried by an access token."""

    sub: UUID
    sid: UUID
    org: UUID
    mid: UUID
    role: str
    exp: datetime
