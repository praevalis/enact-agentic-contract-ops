import {
    useMutation,
    useQuery,
    useQueryClient,
    type QueryClient,
} from '@tanstack/react-query';

import { apiSession } from '../../api/session';
import type {
    LoginInput,
    MembershipRole,
    OrganizationContext,
    Principal,
    RegistrationInput,
} from '../../api/contracts';
import { apiErrorFrom } from '../../api/errors';

export const sessionQueryKey = ['auth', 'session'] as const;
export const organizationsQueryKey = ['auth', 'organizations'] as const;

/**
 * Activates a replacement organization context and discards prior tenant data.
 *
 * @param queryClient - Cache containing the authenticated principal.
 * @param principal - Principal before the context change.
 * @param context - Context and token returned by the API.
 */
function activateOrganizationContext(
    queryClient: QueryClient,
    principal: Principal,
    context: OrganizationContext,
): void {
    apiSession.setAccessToken(context.token);
    queryClient.clear();
    queryClient.setQueryData<Principal>(sessionQueryKey, {
        ...principal,
        organization: context.organization,
        membership: context.membership,
        token: context.token,
    });
}

export function useSession() {
    return useQuery({
        queryKey: sessionQueryKey,
        queryFn: () => apiSession.restore(),
        retry: false,
        staleTime: Infinity,
    });
}

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
            activateOrganizationContext(queryClient, principal, context);
        },
    });
}

export function useOrganizations() {
    return useQuery({
        queryKey: organizationsQueryKey,
        queryFn: async () => {
            const result = await apiSession.client.GET(
                '/api/v1/users/me/organizations',
            );
            if (!result.data) {
                throw apiErrorFrom(result.response, result.error);
            }

            return result.data;
        },
        retry: false,
    });
}

export function useSwitchOrganization() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (organizationId: string) => {
            const principal =
                queryClient.getQueryData<Principal>(sessionQueryKey);
            if (!principal) {
                throw new Error('An account session is required.');
            }

            const result = await apiSession.client.PATCH(
                '/api/v1/users/me/organization',
                { body: { organization_id: organizationId } },
            );
            if (!result.data) {
                throw apiErrorFrom(result.response, result.error);
            }

            return { context: result.data, principal };
        },
        onSuccess: ({ context, principal }) => {
            activateOrganizationContext(queryClient, principal, context);
        },
        onError: () => {
            void queryClient.invalidateQueries({
                queryKey: organizationsQueryKey,
            });
        },
    });
}

/**
 * Issues a one-time invitation code in the selected organization.
 *
 * @returns A mutation containing the code and its expiry.
 */
export function useIssueInvitation() {
    return useMutation({
        mutationFn: async ({
            organizationId,
            role,
        }: {
            organizationId: string;
            role: MembershipRole;
        }) => {
            const result = await apiSession.client.POST(
                '/api/v1/organizations/{organization_id}/invitations',
                {
                    params: { path: { organization_id: organizationId } },
                    body: { role },
                },
            );
            if (!result.data) {
                throw apiErrorFrom(result.response, result.error);
            }

            return result.data;
        },
        gcTime: 0,
    });
}

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
