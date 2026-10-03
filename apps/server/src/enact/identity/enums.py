"""Identity domain enumerations."""

from enum import StrEnum


class MembershipRole(StrEnum):
    """Roles assigned to organization memberships."""

    DEAL_DESK = 'deal_desk'
    ADMINISTRATOR = 'administrator'
    OPERATIONS_REVIEWER = 'operations_reviewer'
    AUDITOR = 'auditor'


class MembershipStatus(StrEnum):
    """Lifecycle states that affect membership authorization."""

    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    REVOKED = 'revoked'
