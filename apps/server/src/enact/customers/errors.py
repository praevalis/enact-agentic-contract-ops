"""Stable customer application errors."""

from enact.platform.errors import EnactError


class CustomerError(EnactError):
    """Base class for customer domain errors."""

    def __init__(
        self, message: str = 'The customer operation failed.', code: str = 'customer_error'
    ) -> None:
        """Initialize a customer error.

        Args:
            message: Human-readable description of the failure.
            code: Stable machine-readable error code.
        """
        super().__init__(message=message, code=code)


class CustomerPermissionDeniedError(CustomerError):
    """Raised when the principal cannot manage customers in the active organization."""

    def __init__(self) -> None:
        """Initialize a customer permission error."""
        super().__init__(
            message='Customer management is not allowed for this account.',
            code='customer_permission_denied',
        )


class CustomerNotFoundError(CustomerError):
    """Customer is absent or outside the active tenant."""

    def __init__(self) -> None:
        """Initialize a non-disclosing customer lookup error."""
        super().__init__(message='Customer not found.', code='customer_not_found')
