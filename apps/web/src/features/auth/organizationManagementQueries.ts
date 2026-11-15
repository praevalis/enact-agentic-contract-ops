import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { MembershipRole, Principal } from '../../api/contracts';
import { apiErrorFrom } from '../../api/errors';
import { apiSession } from '../../api/session';
import { organizationsQueryKey, sessionQueryKey } from './queries';

export const memberPageSize = 3;

/**
 * Names a member page within one organization context.
 *
 * @param organizationId - Active organization identifier.
 * @param cursor - Page position, or null for the first page.
 * @returns Stable cache key for the member page.
 */
const memberQueryKey = (organizationId: string, cursor: string | null) =>
    ['organization', organizationId, 'members', cursor] as const;

/**
 * Loads one cursor page of active organization members.
 *
 * @param organizationId - Active organization identifier.
 * @param cursor - Position after the preceding page.
 * @returns Query containing member details, count, and next cursor.
 */
export function useOrganizationMembers(
    organizationId: string,
    cursor: string | null,
) {
    return useQuery({
        queryKey: memberQueryKey(organizationId, cursor),
        queryFn: async () => {
            const result = await apiSession.client.GET(
                '/api/v1/organizations/{organization_id}/memberships',
                {
                    params: {
                        path: { organization_id: organizationId },
                        query: {
                            page_size: memberPageSize,
                            cursor: cursor ?? undefined,
                        },
                    },
                },
            );
            if (!result.data) {
                throw apiErrorFrom(result.response, result.error);
            }

            return result.data;
        },
        retry: false,
    });
}

/**
 * Renames the active organization and updates visible context caches.
 *
 * @returns Organization rename mutation.
 */
export function useRenameOrganization() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            organizationId,
            name,
        }: {
            organizationId: string;
            name: string;
        }) => {
            const result = await apiSession.client.PATCH(
                '/api/v1/organizations/{organization_id}',
                {
                    params: { path: { organization_id: organizationId } },
                    body: { name },
                },
            );
            if (!result.data) {
                throw apiErrorFrom(result.response, result.error);
            }

            return result.data;
        },
        onSuccess: (organization) => {
            queryClient.setQueryData<Principal>(sessionQueryKey, (principal) =>
                principal?.organization?.id === organization.id
                    ? { ...principal, organization }
                    : principal,
            );
            void queryClient.invalidateQueries({
                queryKey: organizationsQueryKey,
            });
        },
    });
}

/**
 * Changes an active member's role and refreshes the actor's context if needed.
 *
 * @returns Role-change mutation.
 */
export function useChangeMemberRole() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            organizationId,
            membershipId,
            role,
        }: {
            organizationId: string;
            membershipId: string;
            userId: string;
            role: MembershipRole;
        }) => {
            const result = await apiSession.client.PATCH(
                '/api/v1/organizations/{organization_id}/memberships/{membership_id}',
                {
                    params: {
                        path: {
                            organization_id: organizationId,
                            membership_id: membershipId,
                        },
                    },
                    body: { role },
                },
            );
            if (!result.data) {
                throw apiErrorFrom(result.response, result.error);
            }

            return result.data;
        },
        onSuccess: async (_, variables) => {
            const principal =
                queryClient.getQueryData<Principal>(sessionQueryKey);
            if (principal?.user.id === variables.userId) {
                const refreshed = await apiSession.restore();
                queryClient.clear();
                queryClient.setQueryData(sessionQueryKey, refreshed);
                return;
            }

            await queryClient.invalidateQueries({
                queryKey: ['organization', variables.organizationId, 'members'],
            });
        },
    });
}

/**
 * Revokes a membership and updates the current session when the actor removes themselves.
 *
 * @returns Member-removal mutation.
 */
export function useRemoveMember() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            organizationId,
            membershipId,
        }: {
            organizationId: string;
            membershipId: string;
            userId: string;
        }) => {
            const result = await apiSession.client.DELETE(
                '/api/v1/organizations/{organization_id}/memberships/{membership_id}',
                {
                    params: {
                        path: {
                            organization_id: organizationId,
                            membership_id: membershipId,
                        },
                    },
                },
            );
            if (!result.response.ok) {
                throw apiErrorFrom(result.response, result.error);
            }
        },
        onSuccess: async (_, variables) => {
            const principal =
                queryClient.getQueryData<Principal>(sessionQueryKey);
            if (principal?.user.id === variables.userId) {
                const refreshed = await apiSession.restore();
                queryClient.clear();
                queryClient.setQueryData(sessionQueryKey, refreshed);
                return;
            }

            await queryClient.invalidateQueries({
                queryKey: ['organization', variables.organizationId, 'members'],
            });
        },
    });
}
