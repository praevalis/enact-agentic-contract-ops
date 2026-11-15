import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';

import { apiSession } from '../../api/session';
import { OrganizationMembers } from './OrganizationMembers';

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

test('shows active-member count and moves between cursor pages', async () => {
    const firstPage = Array.from({ length: 10 }, (_, index) => ({
        id: `member-${index + 1}`,
        user_id: `user-${index + 1}`,
        display_name: index === 0 ? 'Morgan Lee' : `Member ${index + 1}`,
        email: `member-${index + 1}@example.com`,
        role: 'deal_desk' as const,
    }));
    const get = vi
        .spyOn(apiSession.client, 'GET')
        .mockResolvedValueOnce({
            data: {
                items: firstPage,
                total_count: 11,
                next_cursor: 'after-ten',
            },
            response: new Response(null, { status: 200 }),
        })
        .mockResolvedValueOnce({
            data: {
                items: [
                    {
                        id: 'member-11',
                        user_id: 'user-11',
                        display_name: 'Elena Ruiz',
                        email: 'elena@example.com',
                        role: 'auditor',
                    },
                ],
                total_count: 11,
                next_cursor: null,
            },
            response: new Response(null, { status: 200 }),
        });

    render(
        <QueryClientProvider client={new QueryClient()}>
            <OrganizationMembers
                organizationId="org-acme"
                currentUserId="one"
                administrator={false}
            />
        </QueryClientProvider>,
    );

    expect(await screen.findByText('11 active members')).toBeInTheDocument();
    expect(screen.getByText('Showing 1–10 of 11 members')).toBeInTheDocument();
    expect(get).toHaveBeenCalledWith(
        '/api/v1/organizations/{organization_id}/memberships',
        {
            params: {
                path: { organization_id: 'org-acme' },
                query: { page_size: 10, cursor: undefined },
            },
        },
    );
    expect(screen.queryByRole('button', { name: 'Invite member' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    expect(await screen.findByText('Elena Ruiz')).toBeInTheDocument();
    expect(screen.getByText('Showing 11–11 of 11 members')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Previous' }));
    expect(await screen.findByText('Morgan Lee')).toBeInTheDocument();
});

test('hides pagination when all members fit on one page', async () => {
    vi.spyOn(apiSession.client, 'GET').mockResolvedValue({
        data: {
            items: [
                {
                    id: 'one',
                    user_id: 'one',
                    display_name: 'Morgan Lee',
                    email: 'morgan@example.com',
                    role: 'administrator',
                },
            ],
            total_count: 1,
            next_cursor: null,
        },
        response: new Response(null, { status: 200 }),
    });

    render(
        <QueryClientProvider client={new QueryClient()}>
            <OrganizationMembers
                organizationId="org-acme"
                currentUserId="one"
                administrator={false}
            />
        </QueryClientProvider>,
    );

    expect(await screen.findByText('Morgan Lee')).toBeInTheDocument();
    expect(screen.queryByText(/Showing 1/)).toBeNull();
    expect(screen.queryByRole('button', { name: 'Next' })).toBeNull();
});
