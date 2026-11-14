import { describe, expect, test, vi } from 'vitest';

import type { Principal } from './contracts';
import { ApiError } from './errors';
import { ApiSession } from './session';

/**
 * Creates an identity response with a configurable bearer token.
 *
 * @param token - Access token included in the response.
 * @param expiresAt - Access token expiry.
 * @returns A generated-contract principal for tests.
 */
function principal(
    token: string,
    expiresAt = '2099-01-01T00:00:00Z',
): Principal {
    return {
        user: {
            id: 'user-1',
            email: 'user@example.com',
            display_name: 'Test User',
            status: 'active',
        },
        organization: null,
        membership: null,
        token: {
            access_token: token,
            expires_at: expiresAt,
            organization_id: null,
            token_type: 'Bearer',
        },
    };
}

/**
 * Creates the JSON response used by the fake transport.
 *
 * @param body - Response payload.
 * @param status - HTTP response status.
 * @returns A JSON response for the fake transport.
 */
function json(body: unknown, status = 200): Response {
    return Response.json(body, { status });
}

describe('ApiSession', () => {
    test('restores from the refresh cookie without persisting the access token', async () => {
        const fetcher = vi.fn(async (request: Request) => {
            expect(request.url).toBe(
                'http://localhost:8000/api/v1/auth/refresh',
            );
            expect(request.credentials).toBe('include');
            expect(request.headers.has('Authorization')).toBe(false);
            return json(principal('restored'));
        });
        const session = new ApiSession('http://localhost:8000', fetcher);

        expect(await session.restore()).toEqual(principal('restored'));
        expect(fetcher).toHaveBeenCalledOnce();
    });

    test('treats an invalid refresh cookie as an anonymous session', async () => {
        const session = new ApiSession('http://localhost:8000', async () =>
            json({ code: 'invalid_refresh_token', message: 'Expired.' }, 401),
        );

        expect(await session.restore()).toBeNull();
    });

    test('returns an anonymous 401 without attempting refresh', async () => {
        const fetcher = vi.fn(async (request: Request) => {
            expect(request.url).toBe('http://localhost:8000/api/v1/users/me');
            return json({ code: 'invalid_access_token' }, 401);
        });
        const session = new ApiSession('http://localhost:8000', fetcher);

        const result = await session.client.GET('/api/v1/users/me');

        expect(result.response.status).toBe(401);
        expect(fetcher).toHaveBeenCalledOnce();
    });

    test('reports a transient restoration failure without discarding session state', async () => {
        const fetcher = vi
            .fn<(request: Request) => Promise<Response>>()
            .mockResolvedValueOnce(json(principal('first')))
            .mockResolvedValueOnce(
                json(
                    { code: 'temporarily_unavailable', message: 'Retry.' },
                    503,
                ),
            )
            .mockImplementationOnce(async (request: Request) => {
                expect(request.headers.get('Authorization')).toBe(
                    'Bearer first',
                );
                return json({ status: 'ok' });
            });
        const session = new ApiSession('http://localhost:8000', fetcher);
        await session.restore();

        await expect(session.restore()).rejects.toMatchObject({
            status: 503,
            code: 'temporarily_unavailable',
        });
        expect((await session.client.GET('/api/v1/health/live')).data).toEqual({
            status: 'ok',
        });
    });

    test('uses a fresh bearer token and retries an unauthorized request once', async () => {
        const seen: string[] = [];
        const fetcher = vi.fn(async (request: Request) => {
            const path = new URL(request.url).pathname;
            seen.push(
                `${path}:${request.headers.get('Authorization') ?? 'none'}`,
            );
            if (path.endsWith('/refresh')) {
                return json(principal(seen.length === 1 ? 'old' : 'new'));
            }
            return seen.length === 2
                ? json(
                      { code: 'invalid_access_token', message: 'Expired.' },
                      401,
                  )
                : json({ status: 'ok' });
        });
        const session = new ApiSession('http://localhost:8000', fetcher);
        await session.restore();

        const result = await session.client.GET('/api/v1/health/live');

        expect(result.data).toEqual({ status: 'ok' });
        expect(seen).toEqual([
            '/api/v1/auth/refresh:none',
            '/api/v1/health/live:Bearer old',
            '/api/v1/auth/refresh:none',
            '/api/v1/health/live:Bearer new',
        ]);
    });

    test('shares one refresh across concurrent expired requests', async () => {
        let refreshes = 0;
        const fetcher = vi.fn(async (request: Request) => {
            if (request.url.endsWith('/refresh')) {
                refreshes += 1;
                return json(
                    principal(
                        refreshes === 1 ? 'old' : 'new',
                        '2000-01-01T00:00:00Z',
                    ),
                );
            }
            return json({ status: 'ok' });
        });
        const session = new ApiSession('http://localhost:8000', fetcher);
        await session.restore();

        await Promise.all([
            session.client.GET('/api/v1/health/live'),
            session.client.GET('/api/v1/health/ready'),
        ]);

        expect(refreshes).toBe(2);
    });

    test('signs out with the bearer token and retains the session if revocation fails', async () => {
        let logoutStatus = 503;
        const fetcher = vi.fn(async (request: Request) => {
            if (request.url.endsWith('/refresh')) {
                return json(principal('active'));
            }
            expect(request.url).toBe(
                'http://localhost:8000/api/v1/auth/logout',
            );
            expect(request.headers.get('Authorization')).toBe('Bearer active');
            expect(request.credentials).toBe('include');
            return new Response(null, { status: logoutStatus });
        });
        const session = new ApiSession('http://localhost:8000', fetcher);
        await session.restore();

        await expect(session.signOut()).rejects.toBeInstanceOf(ApiError);

        logoutStatus = 204;
        await session.signOut();
        await session.signOut();
        expect(fetcher).toHaveBeenCalledTimes(3);
    });

    test('keeps stable server error codes for sign-in failures', async () => {
        const session = new ApiSession('http://localhost:8000', async () =>
            json(
                {
                    code: 'invalid_credentials',
                    message: 'Incorrect email or password.',
                },
                401,
            ),
        );

        await expect(
            session.login({ email: 'user@example.com', password: 'wrong' }),
        ).rejects.toMatchObject({
            status: 401,
            code: 'invalid_credentials',
        });
    });

    test('classifies request validation failures', async () => {
        const session = new ApiSession('http://localhost:8000', async () =>
            json(
                {
                    detail: [
                        {
                            loc: ['body', 'email'],
                            msg: 'Invalid email address.',
                        },
                    ],
                },
                422,
            ),
        );

        await expect(
            session.register({
                email: 'invalid',
                password: 'password123',
                display_name: 'Test User',
            }),
        ).rejects.toMatchObject({
            code: 'validation_error',
            detail: [{ loc: ['body', 'email'], msg: 'Invalid email address.' }],
        });
    });
});
