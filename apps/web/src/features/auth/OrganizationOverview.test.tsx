import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
    act,
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';

import type { Principal } from '../../api/contracts';
import { apiSession } from '../../api/session';
import { OrganizationOverview } from './OrganizationOverview';
import { sessionQueryKey } from './queries';

const administrator: Principal = {
    user: {
        id: 'user-morgan',
        email: 'morgan@example.com',
        display_name: 'Morgan Lee',
        status: 'active',
    },
    organization: { id: 'org-acme', name: 'Acme Cloud', status: 'active' },
    membership: {
        organization_id: 'org-acme',
        role: 'administrator',
        status: 'active',
    },
    token: {
        access_token: 'acme-token',
        token_type: 'Bearer',
        expires_at: '2099-01-01T00:00:00Z',
        organization_id: 'org-acme',
    },
};

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

test('offers code issuance only in an administrator organization', async () => {
    vi.spyOn(apiSession.client, 'GET').mockResolvedValue({
        data: [],
        response: new Response(null, { status: 200 }),
    });
    const queryClient = new QueryClient();
    queryClient.setQueryData<Principal>(sessionQueryKey, {
        ...administrator,
        membership: {
            organization_id: 'org-acme',
            role: 'deal_desk',
            status: 'active',
        },
    });

    render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter>
                <OrganizationOverview />
            </MemoryRouter>
        </QueryClientProvider>,
    );

    expect(screen.queryByRole('button', { name: 'Invite member' })).toBeNull();
    expect(screen.queryByText('Signed in as')).toBeNull();
    expect(
        screen.getByRole('button', { name: 'Sign out' }),
    ).toBeInTheDocument();

    act(() => queryClient.setQueryData(sessionQueryKey, administrator));
    expect(
        await screen.findByRole('button', { name: 'Invite member' }),
    ).toBeInTheDocument();
});

test('clears an issued code when the active organization changes', async () => {
    vi.spyOn(apiSession.client, 'GET').mockResolvedValue({
        data: [],
        response: new Response(null, { status: 200 }),
    });
    vi.spyOn(apiSession.client, 'POST').mockResolvedValue({
        data: {
            code: 'ACME7K2M',
            organization_id: 'org-acme',
            role: 'deal_desk',
            expires_at: '2026-11-22T12:00:00Z',
        },
        response: new Response(null, { status: 201 }),
    });
    const queryClient = new QueryClient();
    queryClient.setQueryData(sessionQueryKey, administrator);

    render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter>
                <OrganizationOverview />
            </MemoryRouter>
        </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Invite member' }));
    fireEvent.click(screen.getByRole('button', { name: 'Create code' }));
    expect(await screen.findByText('ACME7K2M')).toBeInTheDocument();

    act(() =>
        queryClient.setQueryData<Principal>(sessionQueryKey, {
            ...administrator,
            organization: {
                id: 'org-next',
                name: 'Next Team',
                status: 'active',
            },
            membership: {
                organization_id: 'org-next',
                role: 'administrator',
                status: 'active',
            },
        }),
    );

    await waitFor(() => expect(screen.queryByText('ACME7K2M')).toBeNull());
    expect(
        screen.getByRole('button', { name: 'Invite member' }),
    ).toBeInTheDocument();
});
