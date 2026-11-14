import { expect, test } from 'vitest';

import { ApiError } from '../../api/errors';
import { fieldError } from './fieldErrors';

test('returns a message only for the requested field location', () => {
    const error = new ApiError(422, 'validation_error', 'Check fields.', [
        { loc: ['body', 'email'], msg: 'Invalid email address.' },
        { loc: ['body', 'password'], msg: 'Too short.' },
    ]);

    expect(fieldError(error, 'email')).toBe('Invalid email address.');
    expect(fieldError(error, 'name')).toBeUndefined();
});

test('ignores malformed validation detail', () => {
    const error = new ApiError(422, 'validation_error', 'Check fields.', [
        { loc: 'email', msg: 'Wrong shape.' },
        { loc: ['body', 'email'], msg: 4 },
    ]);

    expect(fieldError(error, 'email')).toBeUndefined();
});
