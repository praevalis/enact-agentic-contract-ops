import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';

import { apiSession } from '../../api/session';
import { SignIn } from './SignIn';

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

test('keeps empty field errors inline without sending a sign-in request', async () => {
    vi.spyOn(apiSession, 'restore').mockResolvedValue(null);
    const login = vi.spyOn(apiSession, 'login');

    render(
        <QueryClientProvider client={new QueryClient()}>
            <MemoryRouter>
                <SignIn />
            </MemoryRouter>
        </QueryClientProvider>,
    );

    await screen.findByRole('heading', { name: 'Sign in to Enact' });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(screen.getByText('Enter your work email.')).toBeInTheDocument();
    expect(screen.getByText('Enter your password.')).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();

    fireEvent.change(screen.getByRole('textbox', { name: 'Work email' }), {
        target: { value: 'morgan@example.com' },
    });

    expect(screen.queryByText('Enter your work email.')).toBeNull();
    expect(screen.getByText('Enter your password.')).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
});
