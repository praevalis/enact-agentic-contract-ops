import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';

import type { Principal } from '../../api/contracts';
import { ApiError } from '../../api/errors';
import { apiSession } from '../../api/session';
import { OrganizationIdentity } from './OrganizationIdentity';
import { sessionQueryKey } from './queries';

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

test('an administrator renames the organization and updates the active context', async () => {
    const organizationId = 'org-acme';
    const queryClient = new QueryClient();
    queryClient.setQueryData<Principal>(sessionQueryKey, {
        user: {
            id: 'user-one',
            email: 'one@example.com',
            display_name: 'One',
            status: 'active',
        },
        organization: {
            id: organizationId,
            name: 'Acme Cloud',
            status: 'active',
        },
        membership: {
            organization_id: organizationId,
            role: 'administrator',
            status: 'active',
        },
        token: {
            access_token: 'token',
            token_type: 'Bearer',
            expires_at: '2099-01-01T00:00:00Z',
            organization_id: organizationId,
        },
    });
    const patch = vi.spyOn(apiSession.client, 'PATCH').mockResolvedValue({
        data: { id: organizationId, name: 'Acme Operations', status: 'active' },
        response: new Response(null, { status: 200 }),
    });

    render(
        <QueryClientProvider client={queryClient}>
            <OrganizationIdentity
                organizationId={organizationId}
                name="Acme Cloud"
                administrator
            />
        </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    const name = screen.getByRole('textbox', { name: 'Organization name' });
    expect(name).toHaveFocus();
    expect(screen.getByRole('button', { name: 'Save name' })).toBeDisabled();
    fireEvent.change(name, { target: { value: 'Acme Operations' } });
    expect(screen.getByRole('button', { name: 'Save name' })).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: 'Save name' }));

    await waitFor(() => expect(patch).toHaveBeenCalledOnce());
    expect(patch).toHaveBeenCalledWith(
        '/api/v1/organizations/{organization_id}',
        {
            params: { path: { organization_id: organizationId } },
            body: { name: 'Acme Operations' },
        },
    );
    await waitFor(() =>
        expect(
            queryClient.getQueryData<Principal>(sessionQueryKey)?.organization
                ?.name,
        ).toBe('Acme Operations'),
    );
    expect(screen.getByRole('button', { name: 'Edit' })).toHaveFocus();
});

test('a non-administrator can read the name but cannot edit it', () => {
    render(
        <QueryClientProvider client={new QueryClient()}>
            <OrganizationIdentity
                organizationId="org-acme"
                name="Acme Cloud"
                administrator={false}
            />
        </QueryClientProvider>,
    );

    expect(
        screen.getByRole('textbox', { name: 'Organization name' }),
    ).toBeDisabled();
    expect(screen.queryByRole('button', { name: 'Edit' })).toBeNull();
});

test('shows server name issues inline and clears them when the name changes', async () => {
    vi.spyOn(apiSession.client, 'PATCH').mockRejectedValue(
        new ApiError(422, 'validation_error', 'Invalid request.', [
            {
                location: ['body', 'name'],
                code: 'invalid',
                message: 'Internal validation detail.',
            },
        ]),
    );

    render(
        <QueryClientProvider client={new QueryClient()}>
            <OrganizationIdentity
                organizationId="org-acme"
                name="Acme Cloud"
                administrator
            />
        </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    const name = screen.getByRole('textbox', { name: 'Organization name' });
    fireEvent.change(name, { target: { value: 'Acme Operations' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save name' }));

    expect(
        await screen.findByText('Check the organization name.'),
    ).toBeInTheDocument();
    expect(name).toHaveAttribute('aria-invalid', 'true');
    expect(screen.queryByText('Internal validation detail.')).toBeNull();
    expect(
        screen.queryByText('Could not save the organization name. Try again.'),
    ).toBeNull();

    fireEvent.change(name, { target: { value: 'Acme Team' } });
    expect(screen.queryByText('Check the organization name.')).toBeNull();
    expect(name).not.toHaveAttribute('aria-invalid', 'true');
});
