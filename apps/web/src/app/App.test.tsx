import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';

import type { Principal } from '../api/contracts';
import { apiSession } from '../api/session';

import { App } from './App';

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

test('opens sign-in when no session can be restored', async () => {
    vi.spyOn(apiSession, 'restore').mockResolvedValue(null);
    render(<App />);

    expect(
        await screen.findByRole('heading', { name: 'Sign in to Enact' }),
    ).toBeInTheDocument();
});

test('routes an account-only sign-in to organization setup', async () => {
    const principal: Principal = {
        user: {
            id: 'user-1',
            email: 'morgan@example.com',
            display_name: 'Morgan Lee',
            status: 'active',
        },
        organization: null,
        membership: null,
        token: {
            access_token: 'access-token',
            token_type: 'Bearer',
            expires_at: '2099-01-01T00:00:00Z',
            organization_id: null,
        },
    };
    vi.spyOn(apiSession, 'restore').mockResolvedValue(null);
    vi.spyOn(apiSession, 'login').mockResolvedValue(principal);
    render(<App />);

    fireEvent.change(
        await screen.findByRole('textbox', { name: 'Work email' }),
        {
            target: { value: 'morgan@example.com' },
        },
    );
    fireEvent.change(screen.getByLabelText('Password'), {
        target: { value: 'secret-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(
        await screen.findByRole('heading', { name: 'Where will you work?' }),
    ).toBeInTheDocument();
});
