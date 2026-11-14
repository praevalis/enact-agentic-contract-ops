import { ApiError } from '../../api/errors';

/**
 * Finds a FastAPI validation message for one form field.
 *
 * @param error - Failed form mutation.
 * @param field - Field name in the request body.
 * @returns The matching message, if the server supplied one.
 */
export function fieldError(error: unknown, field: string): string | undefined {
    if (!(error instanceof ApiError) || !Array.isArray(error.detail)) {
        return undefined;
    }

    for (const issue of error.detail) {
        if (!issue || typeof issue !== 'object') {
            continue;
        }

        if (
            !('loc' in issue) ||
            !Array.isArray(issue.loc) ||
            issue.loc.at(-1) !== field
        ) {
            continue;
        }

        if ('msg' in issue && typeof issue.msg === 'string') {
            return issue.msg;
        }
    }

    return undefined;
}
