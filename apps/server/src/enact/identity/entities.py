"""Identity domain entities used by application ports."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    """Authenticated user identity."""

    id: UUID
    email: str
    password_hash: str
    display_name: str
    status: str


@dataclass(frozen=True, slots=True)
class Membership:
    """A user's membership in an organization."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    status: str


@dataclass(frozen=True, slots=True)
class Organization:
    """An organization available to the authenticated user."""

    id: UUID
    name: str
    status: str


@dataclass(frozen=True, slots=True)
class UserOrganizationPreference:
    """A user's persisted organization context preference."""

    user_id: UUID
    organization_id: UUID
    is_preferred: bool
    last_used_at: datetime | None


@dataclass(frozen=True, slots=True)
class AuthSession:
    """Persisted state for one refresh-token session."""

    id: UUID
    user_id: UUID
    current_organization_id: UUID
    token_family_id: UUID
    refresh_token_digest: str
    expires_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None
    replaced_by_session_id: UUID | None
