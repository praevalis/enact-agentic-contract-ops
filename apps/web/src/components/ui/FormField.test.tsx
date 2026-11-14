import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';

import { FormField } from './FormField';

afterEach(cleanup);

test('associates a label, hint, and error with the input', () => {
    render(
        <FormField
            label="Work email"
            type="email"
            hint="Use your work address."
            error="Invalid email."
        />,
    );

    const input = screen.getByRole('textbox', { name: 'Work email' });
    const hint = screen.getByText('Use your work address.');
    const error = screen.getByRole('alert');

    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', `${hint.id} ${error.id}`);
    expect(error).toHaveTextContent('Invalid email.');
});

test('shows and hides a password without changing its value', () => {
    render(
        <FormField label="Password" type="password" defaultValue="secret" />,
    );

    const password = screen.getByLabelText('Password');
    expect(password).toHaveAttribute('type', 'password');

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(password).toHaveAttribute('type', 'text');
    expect(password).toHaveValue('secret');

    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(password).toHaveAttribute('type', 'password');
});
