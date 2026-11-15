import { expect, test } from 'vitest';

import { fieldError } from './fieldErrors';

test('returns a message only for an exact request location', () => {
    const issues = [
        {
            location: ['body', 'email'],
            code: 'invalid',
            message: 'Raw server detail.',
        },
        {
            location: ['body', 'password'],
            code: 'too_short',
            message: 'Raw server detail.',
        },
        {
            location: ['body', 'members', 0, 'email'],
            code: 'invalid',
            message: 'Raw server detail.',
        },
    ];
    const messages = {
        invalid: 'Enter a valid email address.',
        too_short: 'Use a longer password.',
    };

    expect(fieldError(issues, ['body', 'email'], messages)).toBe(
        'Enter a valid email address.',
    );
    expect(fieldError(issues, ['body', 'members', 0, 'email'], messages)).toBe(
        'Enter a valid email address.',
    );
    expect(
        fieldError(issues, ['body', 'members', 1, 'email'], messages),
    ).toBeUndefined();
    expect(fieldError(issues, ['body', 'name'], messages)).toBeUndefined();
});

test('returns no message when issues are absent', () => {
    expect(fieldError(undefined, ['body', 'email'], {})).toBeUndefined();
});

test('does not expose an unmapped server message', () => {
    const issues = [
        {
            location: ['body', 'email'],
            code: 'unexpected',
            message: 'Raw validator internals.',
        },
    ];

    expect(fieldError(issues, ['body', 'email'], {})).toBe('Check this value.');
});
