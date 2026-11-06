"""Case domain errors."""

from enact.platform.errors import EnactError


class CaseError(EnactError):
    """Base class for case domain errors."""

    def __init__(
        self, message: str = 'The case operation failed.', code: str = 'case_error'
    ) -> None:
        """Initialize a case error.

        Args:
            message: Human-readable description of the failure.
            code: Stable machine-readable error code.
        """
        super().__init__(message=message, code=code)


class CasePermissionDeniedError(CaseError):
    """Raised when the principal cannot manage cases in the active organization."""

    def __init__(self) -> None:
        """Initialize a case permission error."""
        super().__init__(
            message='Case management is not allowed for this account.',
            code='case_permission_denied',
        )


class PriorCaseNotFoundError(CaseError):
    """Raised when an amendment's prior case is unavailable or belongs to another customer."""

    def __init__(self) -> None:
        """Initialize a prior-case lookup error without revealing other tenants."""
        super().__init__(
            message='Prior case not found for this customer.', code='prior_case_not_found'
        )
