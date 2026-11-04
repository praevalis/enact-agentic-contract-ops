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


class UserCreate(BaseWrite):
    """Local credentials and profile supplied during registration."""

    email: Annotated[EmailStr, StringConstraints(strip_whitespace=True, to_lower=True)]
    password: str = Field(min_length=8, max_length=1024)
    display_name: str = Field(min_length=1, max_length=200)


class TokenRead(BaseRead):
    """Short-lived access-token result returned after authentication."""

    access_token: str
    token_type: str = 'Bearer'
    expires_at: datetime
    organization_id: UUID | None


class OrganizationSwitchUpdate(BaseWrite):
    """Request to change the organization context of the current session."""

    organization_id: UUID


class PrincipalRead(BaseRead):
    """Authenticated principal and its active organization context."""

    user: UserRead
    organization: OrganizationRead | None
    membership: MembershipRead | None
    token: TokenRead


class OrganizationCreate(BaseWrite):
    """Organization details supplied during account onboarding."""

    name: str = Field(min_length=1, max_length=200)


class OrganizationJoinCreate(BaseWrite):
    """Invitation code submitted to join an existing organization."""

    code: str = Field(min_length=1, max_length=64)


class OrganizationInvitationCreate(BaseWrite):
    """Role selected by an administrator issuing an invitation."""

    role: MembershipRole


class OrganizationInvitationRead(BaseRead):
    """One-time visible invitation code and its grant."""

    code: str
    organization_id: UUID
    role: MembershipRole
    expires_at: datetime


class OrganizationContextRead(BaseRead):
    """Active context after organization creation, joining, or switching."""

    organization: OrganizationRead
    membership: MembershipRead
    token: TokenRead


class OrganizationMembershipRead(BaseRead):
    """An organization available for account context switching."""

    organization: OrganizationRead
    membership: MembershipRead


class AccessTokenClaims(BaseRead):
    """Validated claims carried by an access token."""

    sub: UUID
    sid: UUID
    org: UUID | None
    mid: UUID | None
    role: str | None
    exp: datetime
