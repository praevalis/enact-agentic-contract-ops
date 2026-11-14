/** A failed API request with a stable code. */
export class ApiError extends Error {
    constructor(
        public readonly status: number,
        public readonly code: string,
        message: string,
        public readonly detail?: unknown,
    ) {
        super(message);
        this.name = 'ApiError';
    }
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
                return new ApiError(response.status, code, message);
            }
        }

        if (response.status === 422 && 'detail' in body) {
            return new ApiError(
                response.status,
                'validation_error',
                'Check the submitted fields.',
                body.detail,
            );
        }
    }

    return new ApiError(
        response.status,
        'http_error',
        response.statusText || 'Request failed.',
    );
}
