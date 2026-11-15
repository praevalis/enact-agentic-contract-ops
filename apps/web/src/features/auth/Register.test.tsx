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

import { ApiError } from '../../api/errors';
import { apiSession } from '../../api/session';
import { Register } from './Register';

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

test('shows password guidance only while the field is focused', async () => {
    vi.spyOn(apiSession, 'restore').mockResolvedValue(null);

    render(
        <QueryClientProvider client={new QueryClient()}>
            <MemoryRouter>
                <Register />
            </MemoryRouter>
        </QueryClientProvider>,
    );

    await screen.findByRole('heading', { name: 'Create your account' });
    const password = screen.getByLabelText('Password');

    expect(screen.queryByText('At least 8 characters.')).toBeNull();
    fireEvent.focus(password);
    expect(screen.getByText('At least 8 characters.')).toBeInTheDocument();
    fireEvent.blur(password);
    expect(screen.queryByText('At least 8 characters.')).toBeNull();
});

test('keeps server errors on unchanged fields while another field is edited', async () => {
    vi.spyOn(apiSession, 'restore').mockResolvedValue(null);
    const register = vi.spyOn(apiSession, 'register').mockRejectedValue(
        new ApiError(422, 'validation_error', 'Invalid request.', [
            {
                location: ['body', 'email'],
                code: 'invalid',
                message: 'Invalid value.',
            },
            {
                location: ['body', 'password'],
                code: 'too_short',
                message: 'Value is too short.',
            },
        ]),
    );

    render(
        <QueryClientProvider client={new QueryClient()}>
            <MemoryRouter>
                <Register />
            </MemoryRouter>
        </QueryClientProvider>,
    );

    await screen.findByRole('heading', { name: 'Create your account' });
    fireEvent.change(screen.getByLabelText('Your name'), {
        target: { value: 'Morgan Lee' },
    });
    fireEvent.change(screen.getByLabelText('Work email'), {
        target: { value: 'invalid' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
        target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => expect(register).toHaveBeenCalledOnce());
    expect(
        await screen.findByText('Enter a valid work email address.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Use at least 8 characters.')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Your name'), {
        target: { value: 'Morgan Avery Lee' },
    });
    expect(
        screen.getByText('Enter a valid work email address.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Use at least 8 characters.')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Work email'), {
        target: { value: 'morgan@example.com' },
    });
    expect(screen.queryByText('Enter a valid work email address.')).toBeNull();
    expect(screen.getByText('Use at least 8 characters.')).toBeInTheDocument();
});
