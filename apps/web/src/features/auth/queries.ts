import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiSession } from '../../api/session';
import type {
    LoginInput,
    Principal,
    RegistrationInput,
} from '../../api/contracts';
import { apiErrorFrom } from '../../api/errors';

export const sessionQueryKey = ['auth', 'session'] as const;

/**
 * Reads the authenticated principal through the refresh cookie.
 *
 * @returns The session query, including pending and error states.
 */
export function useSession() {
    return useQuery({
        queryKey: sessionQueryKey,
        queryFn: () => apiSession.restore(),
        retry: false,
        staleTime: Infinity,
    });
}

/**
 * Starts a local session from submitted credentials.
 *
 * @returns A login mutation that replaces cached identity data.
 */
export function useLogin() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (body: LoginInput) => apiSession.login(body),
        onSuccess: (principal) => {
            queryClient.clear();
            queryClient.setQueryData(sessionQueryKey, principal);
        },
    });
}

/**
 * Starts an account-only session after registration.
 *
 * @returns A registration mutation that replaces cached identity data.
 */
export function useRegistration() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (body: RegistrationInput) => apiSession.register(body),
        onSuccess: (principal) => {
            queryClient.clear();
            queryClient.setQueryData(sessionQueryKey, principal);
        },
    });
}

export type OrganizationSetup =
    { kind: 'create'; name: string } | { kind: 'join'; code: string };

/**
 * Creates or joins an organization for the current account.
 *
 * @returns A mutation that replaces the account-only context.
 */
export function useOrganizationSetup() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (input: OrganizationSetup) => {
            const principal =
                queryClient.getQueryData<Principal>(sessionQueryKey);
            if (!principal) {
                throw new Error('An account session is required.');
            }

            const result =
                input.kind === 'create'
                    ? await apiSession.client.POST('/api/v1/organizations', {
                          body: { name: input.name },
                      })
                    : await apiSession.client.POST(
                          '/api/v1/organizations/join',
                          { body: { code: input.code } },
                      );
            if (!result.data) {
                throw apiErrorFrom(result.response, result.error);
            }

            return { context: result.data, principal };
        },
        onSuccess: ({ context, principal }) => {
            apiSession.setAccessToken(context.token);
            queryClient.clear();
            queryClient.setQueryData<Principal>(sessionQueryKey, {
                ...principal,
                organization: context.organization,
                membership: context.membership,
                token: context.token,
            });
        },
    });
}

/**
 * Revokes the browser session and clears cached server state.
 *
 * @returns A sign-out mutation.
 */
export function useSignOut() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => apiSession.signOut(),
        onSuccess: () => {
            queryClient.clear();
            queryClient.setQueryData(sessionQueryKey, null);
        },
    });
}
