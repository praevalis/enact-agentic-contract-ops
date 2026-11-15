import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';

import type { OrganizationMember, Principal } from '../../api/contracts';
import { ApiError } from '../../api/errors';
import { apiSession } from '../../api/session';
import { MemberRow } from './MemberRow';
import { sessionQueryKey } from './queries';

const member: OrganizationMember = {
    id: 'membership-jules',
    user_id: 'user-jules',
    display_name: 'Jules Park',
    email: 'jules@example.com',
    role: 'deal_desk',
};

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

/**
 * Render one manageable member with an authenticated administrator.
 *
 * @param onRemoved - Callback after a successful removal.
 * @returns The removal callback for assertions.
 */
function renderRow(onRemoved = vi.fn()) {
    const queryClient = new QueryClient();
    queryClient.setQueryData<Principal>(sessionQueryKey, {
        user: {
            id: 'user-admin',
            email: 'admin@example.com',
            display_name: 'Admin',
            status: 'active',
        },
        organization: { id: 'org-acme', name: 'Acme Cloud', status: 'active' },
        membership: {
            organization_id: 'org-acme',
            role: 'administrator',
            status: 'active',
        },
        token: {
            access_token: 'token',
            token_type: 'Bearer',
            expires_at: '2099-01-01T00:00:00Z',
            organization_id: 'org-acme',
        },
    });
    render(
        <QueryClientProvider client={queryClient}>
            <ul>
                <MemberRow
                    member={member}
                    organizationId="org-acme"
                    administrator
                    currentUserId="user-admin"
                    colorIndex={1}
                    onRemoved={onRemoved}
                />
            </ul>
        </QueryClientProvider>,
    );
    return onRemoved;
}

test('an administrator changes a member role from the inline editor', async () => {
    const patch = vi.spyOn(apiSession.client, 'PATCH').mockResolvedValue({
        data: {
            organization_id: 'org-acme',
            role: 'auditor',
            status: 'active',
        },
        response: new Response(null, { status: 200 }),
    });
    renderRow();

    fireEvent.click(
        screen.getByRole('button', { name: 'Actions for Jules Park' }),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Update role' }));
    expect(screen.getByRole('button', { name: 'Save role' })).toBeDisabled();
    fireEvent.click(
        screen.getByRole('button', {
            name: 'New role for Jules Park: Deal desk',
        }),
    );
    fireEvent.click(screen.getByRole('button', { name: /Auditor/ }));
    expect(screen.getByRole('button', { name: 'Save role' })).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: 'Save role' }));

    await waitFor(() => expect(patch).toHaveBeenCalledOnce());
    expect(patch).toHaveBeenCalledWith(
        '/api/v1/organizations/{organization_id}/memberships/{membership_id}',
        {
            params: {
                path: { organization_id: 'org-acme', membership_id: member.id },
            },
            body: { role: 'auditor' },
        },
    );
    await waitFor(() =>
        expect(
            screen.queryByRole('heading', {
                name: 'Update role for Jules Park',
            }),
        ).toBeNull(),
    );
});

test('removal uses the revoke endpoint and closes the row', async () => {
    const deleteMember = vi
        .spyOn(apiSession.client, 'DELETE')
        .mockResolvedValue({
            data: undefined,
            response: new Response(null, { status: 204 }),
        });
    const onRemoved = renderRow();

    fireEvent.click(
        screen.getByRole('button', { name: 'Actions for Jules Park' }),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Remove member' }));
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    await waitFor(() => expect(deleteMember).toHaveBeenCalledOnce());
    expect(deleteMember).toHaveBeenCalledWith(
        '/api/v1/organizations/{organization_id}/memberships/{membership_id}',
        {
            params: {
                path: { organization_id: 'org-acme', membership_id: member.id },
            },
        },
    );
    await waitFor(() => expect(onRemoved).toHaveBeenCalledOnce());
});

test('last-administrator rejection explains how to keep access available', async () => {
    vi.spyOn(apiSession.client, 'DELETE').mockRejectedValue(
        new ApiError(409, 'last_administrator_required', 'Internal identifier'),
    );
    renderRow();

    fireEvent.click(
        screen.getByRole('button', { name: 'Actions for Jules Park' }),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Remove member' }));
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(
        await screen.findByText(
            'Assign another administrator before changing this membership.',
        ),
    ).toBeInTheDocument();
    expect(screen.queryByText('Internal identifier')).toBeNull();
});
