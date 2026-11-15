import type { ValidationIssue } from './contracts';

/** A failed API request with a stable code. */
export class ApiError extends Error {
    constructor(
        public readonly status: number,
        public readonly code: string,
        message: string,
        public readonly issues?: ValidationIssue[],
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * Checks one untrusted validation issue against the generated API contract.
 *
 * @param value - Parsed issue from an error response.
 * @returns Whether the issue has an allowed code, location, and message.
 */
function isValidationIssue(value: unknown): value is ValidationIssue {
    if (typeof value !== 'object' || value === null) {
        return false;
    }

    if (!('location' in value) || !('code' in value) || !('message' in value)) {
        return false;
    }

    return (
        typeof value.code === 'string' &&
        ['required', 'too_short', 'too_long', 'invalid'].includes(value.code) &&
        Array.isArray(value.location) &&
        value.location.every(
            (part: unknown) =>
                typeof part === 'string' || typeof part === 'number',
        ) &&
        typeof value.message === 'string'
    );
}

/**
 * Converts a parsed API error payload into a consistent client error.
 *
 * @param response - HTTP response carrying the status.
 * @param body - Parsed error payload from the typed client.
 * @returns An error with the server code or a transport fallback code.
 */
export function apiErrorFrom(response: Response, body: unknown): ApiError {
    if (typeof body === 'object' && body !== null) {
        if ('code' in body && 'message' in body) {
            const { code, message } = body;

            if (typeof code === 'string' && typeof message === 'string') {
                const issues =
                    'issues' in body &&
                    Array.isArray(body.issues) &&
                    body.issues.every(isValidationIssue)
                        ? body.issues
                        : undefined;

                return new ApiError(response.status, code, message, issues);
            }
        }
    }

    return new ApiError(
        response.status,
        'http_error',
        response.statusText || 'Request failed.',
    );
}
