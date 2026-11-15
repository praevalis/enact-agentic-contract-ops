import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';

import { ApiError } from '../../api/errors';
import { apiSession } from '../../api/session';
import { InvitationIssuer } from './InvitationIssuer';

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
});

test('issues a code for the selected role and clears it when done', async () => {
    const post = vi.spyOn(apiSession.client, 'POST').mockResolvedValue({
        data: {
            code: 'ACME7K2M',
            organization_id: 'org-acme',
            role: 'auditor',
            expires_at: '2026-11-22T12:00:00Z',
        },
        response: new Response(null, { status: 201 }),
    });
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    render(
        <QueryClientProvider client={new QueryClient()}>
            <InvitationIssuer organizationId="org-acme" />
        </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Invite member' }));
    expect(
        screen.getByRole('heading', { name: 'Invite a teammate' }),
    ).toHaveFocus();
    fireEvent.click(
        screen.getByRole('button', { name: 'Role for new member: Deal desk' }),
    );
    fireEvent.click(
        screen.getByRole('button', {
            name: /Auditor/,
        }),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Create code' }));

    await waitFor(() =>
        expect(post).toHaveBeenCalledWith(
            '/api/v1/organizations/{organization_id}/invitations',
            {
                params: { path: { organization_id: 'org-acme' } },
                body: { role: 'auditor' },
            },
        ),
    );
    expect(await screen.findByText('ACME7K2M')).toBeInTheDocument();
    expect(
        screen.getByRole('heading', {
            name: 'Your invitation code is ready',
        }),
    ).toHaveFocus();
    expect(screen.getByText(/Please copy it now/)).toBeInTheDocument();
    expect(
        screen.getByText(/Share it through a trusted channel/),
    ).toHaveTextContent('Expires');

    fireEvent.click(screen.getByRole('button', { name: 'Copy code' }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith('ACME7K2M'));
    expect(screen.getByRole('button', { name: 'Copied' })).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent(
        'Copied to clipboard.',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Done' }));
    expect(screen.queryByText('ACME7K2M')).toBeNull();
    expect(screen.getByRole('button', { name: 'Invite member' })).toHaveFocus();
});

test('shows a safe permission error without exposing the server message', async () => {
    vi.spyOn(apiSession.client, 'POST').mockRejectedValue(
        new ApiError(
            403,
            'membership_permission_denied',
            'Internal organization identifier.',
        ),
    );

    render(
        <QueryClientProvider client={new QueryClient()}>
            <InvitationIssuer organizationId="org-acme" />
        </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Invite member' }));
    fireEvent.click(screen.getByRole('button', { name: 'Create code' }));

    expect(
        await screen.findByText(
            'You no longer have permission to invite members to this organization.',
        ),
    ).toBeInTheDocument();
    expect(screen.queryByText('Internal organization identifier.')).toBeNull();
});

test('prevents another submission while a code is being created', async () => {
    const post = vi
        .spyOn(apiSession.client, 'POST')
        .mockReturnValue(new Promise<never>(() => {}));

    render(
        <QueryClientProvider client={new QueryClient()}>
            <InvitationIssuer organizationId="org-acme" />
        </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Invite member' }));
    fireEvent.click(screen.getByRole('button', { name: 'Create code' }));

    await waitFor(() => expect(post).toHaveBeenCalledOnce());
    expect(
        screen.getByRole('button', { name: 'Creating code…' }),
    ).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
    expect(
        screen.getByRole('button', { name: 'Role for new member: Deal desk' }),
    ).toBeDisabled();
});

test('keeps the code available to select when clipboard access fails', async () => {
    vi.spyOn(apiSession.client, 'POST').mockResolvedValue({
        data: {
            code: 'ACME7K2M',
            organization_id: 'org-acme',
            role: 'deal_desk',
            expires_at: '2026-11-22T12:00:00Z',
        },
        response: new Response(null, { status: 201 }),
    });
    vi.stubGlobal('navigator', {
        clipboard: {
            writeText: vi.fn().mockRejectedValue(new Error('Denied')),
        },
    });

    render(
        <QueryClientProvider client={new QueryClient()}>
            <InvitationIssuer organizationId="org-acme" />
        </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Invite member' }));
    fireEvent.click(screen.getByRole('button', { name: 'Create code' }));
    expect(await screen.findByText('ACME7K2M')).toHaveClass('select-all');

    fireEvent.click(screen.getByRole('button', { name: 'Copy code' }));
    expect(
        await screen.findByText(
            'Could not copy the code. Select it to copy it manually.',
        ),
    ).toBeInTheDocument();
    expect(screen.getByText('ACME7K2M')).toBeInTheDocument();
});
