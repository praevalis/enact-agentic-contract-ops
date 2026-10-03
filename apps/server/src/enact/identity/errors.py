"""Identity domain errors."""


class IdentityError(Exception):
    """Base class for identity domain errors."""


class InvalidAccessTokenError(IdentityError):
    """Raised when an access token cannot be validated."""
