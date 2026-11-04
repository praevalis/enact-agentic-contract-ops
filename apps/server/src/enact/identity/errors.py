"""Identity domain errors."""

from uuid import UUID

from enact.platform.errors import EnactError


class IdentityError(EnactError):
    """Base class for identity domain errors."""

    def __init__(
        self, message: str = 'The identity operation failed.', code: str = 'identity_error'
    ) -> None:
        """Initialize an identity error.

        Args:
            message: Human-readable description of the failure.
            code: Stable machine-readable error code.
        """
        super().__init__(message=message, code=code)


class InvalidAccessTokenError(IdentityError):
    """Raised when an access token cannot be validated."""

    def __init__(self, message: str = 'Invalid access token.') -> None:
        """Initialize an invalid access-token error.

        Args:
            message: Human-readable description of the token failure.
        """
        super().__init__(message=message, code='invalid_access_token')


class UserEmailAlreadyExistsError(IdentityError):
    """Raised when a user email address is already registered."""

    def __init__(self) -> None:
        """Initialize a duplicate user-email error."""
        super().__init__(
            message='A user with this email address already exists.',
            code='user_email_already_exists',
        )


class MembershipAlreadyExistsError(IdentityError):
    """Raised when a user already belongs to an organization."""

    def __init__(self) -> None:
        """Initialize a duplicate-membership error."""
        super().__init__(
            message='The user already belongs to this organization.',
            code='membership_already_exists',
        )


class AuthSessionAlreadyExistsError(IdentityError):
    """Raised when an authentication session token digest already exists."""

    def __init__(self) -> None:
        """Initialize a duplicate-authentication-session error."""
        super().__init__(
            message='The authentication session already exists.',
            code='auth_session_already_exists',
        )


class InvalidCredentialsError(IdentityError):
    """Raised when supplied credentials cannot authenticate a user."""

    def __init__(self) -> None:
        """Initialize an invalid-credentials error."""
        super().__init__(
            message='The supplied credentials are invalid.',
            code='invalid_credentials',
        )


class InvalidRefreshTokenError(IdentityError):
    """Raised when a refresh token cannot create a new session."""

    def __init__(self) -> None:
        """Initialize an invalid-refresh-token error."""
        super().__init__(
            message='The refresh token is invalid or expired.',
            code='invalid_refresh_token',
        )


class OrganizationMembershipNotFoundError(IdentityError):
    """Raised when a user is not a member of an organization."""

    def __init__(self, user_id: UUID, organization_id: UUID) -> None:
        """Initialize a missing-organization-membership error.

        Args:
            user_id: User whose membership was requested.
            organization_id: Organization whose membership was requested.
        """
        super().__init__(
            message=f'User {user_id} is not a member of organization {organization_id}.',
            code='organization_membership_not_found',
        )


class AuthSessionInactiveError(IdentityError):
    """Raised when an authentication session cannot be used."""

    def __init__(self, session_id: UUID) -> None:
        """Initialize an inactive-session error.

        Args:
            session_id: Identifier of the inactive authentication session.
        """
        super().__init__(
            message=f'Authentication session {session_id} is no longer active.',
            code='auth_session_inactive',
        )


class UserNotFoundError(IdentityError):
    """Raised when a requested user does not exist."""

    def __init__(self, user_id: UUID) -> None:
        """Initialize a missing-user error.

        Args:
            user_id: Identifier of the missing user.
        """
        super().__init__(message=f'User {user_id} does not exist.', code='user_not_found')


class OrganizationNotFoundError(IdentityError):
    """Raised when a requested organization does not exist."""

    def __init__(self, organization_id: UUID) -> None:
        """Initialize a missing-organization error.

        Args:
            organization_id: Identifier of the missing organization.
        """
        super().__init__(
            message=f'Organization {organization_id} does not exist.',
            code='organization_not_found',
        )


class MembershipNotFoundError(IdentityError):
    """Raised when a requested membership does not exist."""

    def __init__(self, membership_id: UUID) -> None:
        """Initialize a missing-membership error.

        Args:
            membership_id: Identifier of the missing membership.
        """
        super().__init__(
            message=f'Membership {membership_id} does not exist.',
            code='membership_not_found',
        )


class MembershipTransitionError(IdentityError):
    """Raised when a membership cannot make the requested status transition."""

    def __init__(self, membership_id: UUID, action: str) -> None:
        """Initialize an invalid-membership-transition error.

        Args:
            membership_id: Membership whose status cannot be changed.
            action: Requested membership action.
        """
        super().__init__(
            message=f'Membership {membership_id} cannot be {action} from its current status.',
            code='membership_invalid_transition',
        )


class MembershipPermissionDeniedError(IdentityError):
    """Raised when the actor cannot manage organization memberships."""

    def __init__(self, organization_id: UUID) -> None:
        """Initialize a membership-permission error.

        Args:
            organization_id: Organization whose memberships the actor cannot manage.
        """
        super().__init__(
            message=f'Membership management is not allowed in organization {organization_id}.',
            code='membership_permission_denied',
        )


class AuthSessionNotFoundError(IdentityError):
    """Raised when a requested authentication session does not exist."""

    def __init__(self, session_id: UUID) -> None:
        """Initialize a missing-authentication-session error.

        Args:
            session_id: Identifier of the missing authentication session.
        """
        super().__init__(
            message=f'Authentication session {session_id} does not exist.',
            code='auth_session_not_found',
        )


class InvalidInvitationCodeError(IdentityError):
    """Raised when an invitation code is invalid, expired, or already used."""

    def __init__(self) -> None:
        """Initialize an invitation-code error."""
        super().__init__(
            message='The invitation code is invalid or no longer available.',
            code='invalid_invitation_code',
        )
