import createClient from 'openapi-fetch';

import type { paths } from './generated/types';
import type {
    AccessToken,
    LoginInput,
    Principal,
    RegistrationInput,
} from './contracts';
import { apiErrorFrom } from './errors';

/** Coordinates typed API requests and the browser's in-memory access token. */
export class ApiSession {
    readonly client;
    private readonly authClient;
    private token: AccessToken | null = null;
    private refreshPromise: Promise<Principal | null> | null = null;

    constructor(
        baseUrl: string,
        fetcher: (request: Request) => Promise<Response> = fetch,
    ) {
        this.authClient = createClient<paths>({
            baseUrl,
            credentials: 'include',
            fetch: fetcher,
        });

        this.client = createClient<paths>({
            baseUrl,
            credentials: 'include',
            fetch: (request) => this.authorizedFetch(request, fetcher),
        });
    }

    /**
     * Authenticates credentials and stores the returned access token.
     *
     * @param body - Submitted login credentials.
     * @returns The authenticated principal.
     * @throws An ApiError when the API rejects the credentials or request.
     */
    login(body: LoginInput): Promise<Principal> {
        return this.establishSession(() =>
            this.authClient.POST('/api/v1/auth/login', { body }),
        );
    }

    /**
     * Registers an account and stores its account-only access token.
     *
     * @param body - New account details and credentials.
     * @returns The account-only principal.
     * @throws An ApiError when the API rejects the registration.
     */
    register(body: RegistrationInput): Promise<Principal> {
        return this.establishSession(() =>
            this.authClient.POST('/api/v1/auth/register', { body }),
        );
    }

    /**
     * Restores the session from the browser's HttpOnly refresh cookie.
     *
     * @returns The renewed principal, or null when the cookie is invalid.
     * @throws An ApiError when the refresh request fails for another reason.
     */
    restore(): Promise<Principal | null> {
        return this.refresh();
    }

    /**
     * Revokes the server session before clearing the local access token.
     *
     * @returns A promise that resolves after revocation or when no token is present.
     * @throws An ApiError when the API does not confirm revocation.
     */
    async signOut(): Promise<void> {
        if (this.refreshPromise) {
            await this.refreshPromise;
        }

        if (!this.token) {
            return;
        }

        const result = await this.client.POST('/api/v1/auth/logout');
        if (!result.response.ok) {
            throw apiErrorFrom(result.response, result.error);
        }

        this.token = null;
    }

    /**
     * Starts a session from a typed login or registration request.
     *
     * @param send - Endpoint-specific request returning a principal.
     * @returns The authenticated principal after storing its access token.
     * @throws An ApiError when the API rejects the request.
     */
    private async establishSession(
        send: () => Promise<{
            data?: Principal;
            error?: unknown;
            response: Response;
        }>,
    ): Promise<Principal> {
        if (this.refreshPromise) {
            await this.refreshPromise;
        }

        const result = await send();
        if (!result.data) {
            throw apiErrorFrom(result.response, result.error);
        }

        this.token = result.data.token;
        return result.data;
    }

    /**
     * Shares one cookie rotation among concurrent callers.
     *
     * @returns The renewed principal, or null when no session remains.
     * @throws An ApiError when the refresh request fails for another reason.
     */
    private refresh(): Promise<Principal | null> {
        if (!this.refreshPromise) {
            this.refreshPromise = this.performRefresh().finally(() => {
                this.refreshPromise = null;
            });
        }

        return this.refreshPromise;
    }

    /**
     * Rotates the cookie and distinguishes an absent session from a failed request.
     *
     * @returns The renewed principal, or null after a 401 response.
     * @throws An ApiError for other API failures.
     */
    private async performRefresh(): Promise<Principal | null> {
        const result = await this.authClient.POST('/api/v1/auth/refresh');
        if (result.data) {
            this.token = result.data.token;
            return result.data;
        }

        if (result.response.status === 401) {
            this.token = null;
            return null;
        }

        throw apiErrorFrom(result.response, result.error);
    }

    /**
     * Adds the bearer token and retries once after a 401 response.
     *
     * @param request - Request created by the typed client.
     * @param fetcher - Browser transport used to send the request.
     * @returns The initial response or its single retry response.
     * @throws An ApiError when a required refresh fails.
     */
    private async authorizedFetch(
        request: Request,
        fetcher: (request: Request) => Promise<Response>,
    ): Promise<Response> {
        if (this.token && Date.parse(this.token.expires_at) <= Date.now()) {
            await this.refresh();
        }

        const token = this.token?.access_token;
        if (!token) {
            return fetcher(request);
        }

        const retry = request.clone();
        request.headers.set('Authorization', `Bearer ${token}`);

        const response = await fetcher(request);
        if (response.status !== 401) {
            return response;
        }

        // A concurrent request may have already rotated the cookie and token.
        const renewed =
            this.token?.access_token !== token
                ? this.token
                : (await this.refresh())?.token;
        if (!renewed) {
            return response;
        }

        retry.headers.set('Authorization', `Bearer ${renewed.access_token}`);

        return fetcher(retry);
    }
}

export const apiSession = new ApiSession(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
);
