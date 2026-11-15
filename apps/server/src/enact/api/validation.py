"""Framework-neutral response details for invalid API requests."""

from typing import Literal

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel


class ValidationIssueRead(BaseModel):
    """One invalid value at a location in the HTTP request."""

    location: list[str | int]
    code: Literal['required', 'too_short', 'too_long', 'invalid']
    message: str


class ValidationErrorRead(BaseModel):
    """Stable API response for request validation failures."""

    code: Literal['validation_error'] = 'validation_error'
    message: str = 'The request contains invalid values.'
    issues: list[ValidationIssueRead]


def parse_request_validation(error: RequestValidationError) -> ValidationErrorRead:
    """Convert framework validation details without returning submitted values.

    Args:
        error: Request validation failure raised by the HTTP framework.

    Returns:
        A generic issue list without framework messages or submitted values.
    """
    issues: list[ValidationIssueRead] = []

    for issue in error.errors():
        match issue['type']:
            case 'missing':
                code = 'required'
                message = 'A value is required.'
            case 'string_too_short' | 'too_short':
                code = 'too_short'
                message = 'The value is too short.'
            case 'string_too_long' | 'too_long':
                code = 'too_long'
                message = 'The value is too long.'
            case _:
                code = 'invalid'
                message = 'Enter a valid value.'

        issues.append(ValidationIssueRead(location=list(issue['loc']), code=code, message=message))

    return ValidationErrorRead(issues=issues)
