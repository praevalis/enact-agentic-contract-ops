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
    vi.spyOn(apiSession.client, 'GET')
        .mockResolvedValueOnce({
            data: {
                items: [
                    {
                        id: 'one',
                        user_id: 'one',
                        display_name: 'Morgan Lee',
                        email: 'morgan@example.com',
                        role: 'administrator',
                    },
                    {
                        id: 'two',
                        user_id: 'two',
                        display_name: 'Jules Park',
                        email: 'jules@example.com',
                        role: 'deal_desk',
                    },
                    {
                        id: 'three',
                        user_id: 'three',
                        display_name: 'Samira Chen',
                        email: 'samira@example.com',
                        role: 'operations_reviewer',
                    },
                ],
                total_count: 4,
                next_cursor: 'after-three',
            },
            response: new Response(null, { status: 200 }),
        })
        .mockResolvedValueOnce({
            data: {
                items: [
                    {
                        id: 'four',
                        user_id: 'four',
                        display_name: 'Elena Ruiz',
                        email: 'elena@example.com',
                        role: 'auditor',
                    },
                ],
                total_count: 4,
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

    expect(await screen.findByText('4 active members')).toBeInTheDocument();
    expect(screen.getByText('Showing 1–3 of 4 members')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Invite member' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    expect(await screen.findByText('Elena Ruiz')).toBeInTheDocument();
    expect(screen.getByText('Showing 4–4 of 4 members')).toBeInTheDocument();
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
