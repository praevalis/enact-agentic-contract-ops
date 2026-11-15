import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';

import type {
    OrganizationContext,
    OrganizationMembership,
    Principal,
} from '../../api/contracts';
import { apiSession } from '../../api/session';
import { OrganizationPicker } from './OrganizationPicker';
import { sessionQueryKey } from './queries';

const current: OrganizationMembership = {
    organization: { id: 'org-acme', name: 'Acme Cloud', status: 'active' },
    membership: {
        organization_id: 'org-acme',
        role: 'administrator',
        status: 'active',
    },
};
const next: OrganizationMembership = {
    organization: {
        id: 'org-northstar',
        name: 'Northstar Operations',
        status: 'active',
    },
    membership: {
        organization_id: 'org-northstar',
        role: 'deal_desk',
        status: 'active',
    },
};
const principal: Principal = {
    user: {
        id: 'user-morgan',
        email: 'morgan@example.com',
        display_name: 'Morgan Lee',
        status: 'active',
    },
    ...current,
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

/**
 * Mounts the picker with an authenticated principal and isolated query cache.
 *
 * @returns The query client used by the picker.
 */
function renderPicker(): QueryClient {
    const queryClient = new QueryClient();
    queryClient.setQueryData(sessionQueryKey, principal);

    render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter>
                <OrganizationPicker current={current} />
            </MemoryRouter>
        </QueryClientProvider>,
    );

    return queryClient;
}

test('switches organizations and discards the prior tenant cache', async () => {
    const context: OrganizationContext = {
        ...next,
        token: {
            access_token: 'northstar-token',
            token_type: 'Bearer',
            expires_at: '2099-01-01T00:00:00Z',
            organization_id: 'org-northstar',
        },
    };
    vi.spyOn(apiSession.client, 'GET').mockResolvedValue({
        data: [current, next],
        response: new Response(null, { status: 200 }),
    });
    const patch = vi.spyOn(apiSession.client, 'PATCH').mockResolvedValue({
        data: context,
        response: new Response(null, { status: 200 }),
    });
    const setAccessToken = vi.spyOn(apiSession, 'setAccessToken');
    const queryClient = renderPicker();
    queryClient.setQueryData(['cases', 'org-acme'], ['prior tenant case']);

    fireEvent.click(
        screen.getByRole('button', { name: 'Change organization' }),
    );
    fireEvent.click(
        await screen.findByRole('button', { name: /Northstar Operations/ }),
    );

    await waitFor(() => {
        expect(
            queryClient.getQueryData<Principal>(sessionQueryKey),
        ).toMatchObject({
            organization: next.organization,
            membership: next.membership,
            token: context.token,
        });
    });
    expect(patch).toHaveBeenCalledWith('/api/v1/users/me/organization', {
        body: { organization_id: 'org-northstar' },
    });
    expect(setAccessToken).toHaveBeenCalledWith(context.token);
    expect(queryClient.getQueryData(['cases', 'org-acme'])).toBeUndefined();
    expect(
        screen.getByRole('button', { name: 'Change organization' }),
    ).toHaveAttribute('aria-expanded', 'false');
});

test('dismisses the dropdown with Escape and an outside click', async () => {
    vi.spyOn(apiSession.client, 'GET').mockResolvedValue({
        data: [current, next],
        response: new Response(null, { status: 200 }),
    });
    renderPicker();

    const trigger = screen.getByRole('button', { name: 'Change organization' });
    trigger.focus();
    fireEvent.click(trigger);
    await screen.findByRole('button', {
        name: /Acme Cloud/,
    });
    expect(trigger).toHaveAttribute('aria-expanded', 'true');

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(trigger).toHaveFocus();
    expect(trigger).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    fireEvent.pointerDown(document.body);
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
});
