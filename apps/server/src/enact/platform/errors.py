"""Common application exception contract."""


class EnactError(Exception):
    """Base class for domain and infrastructure errors defined by Enact."""

    def __init__(self, message: str, code: str) -> None:
        """Initialize an application error.

        Args:
            message: Human-readable description of the failure.
            code: Stable machine-readable error code.
        """
        super().__init__(message)
        self.message = message
        self.code = code
