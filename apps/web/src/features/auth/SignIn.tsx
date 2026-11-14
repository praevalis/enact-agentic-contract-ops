import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { ApiError } from '../../api/errors';
import { AuthShell, FormError } from './AuthShell';
import { fieldError } from './fieldErrors';
import { useLogin, useSession } from './queries';

/**
 * Authenticates an account and routes it to its organization context.
 *
 * @returns The sign-in form or an authenticated redirect.
 */
export function SignIn() {
    const session = useSession();
    const login = useLogin();
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    if (session.data) {
        return (
            <Navigate
                to={session.data.organization ? '/organization' : '/setup'}
                replace
            />
        );
    }

    /**
     * Submits local credentials without discarding values after a recoverable failure.
     *
     * @param event - Native form submission.
     */
    function handleSubmit(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();

        login.mutate(
            { email, password },
            {
                onSuccess: (principal) =>
                    navigate(
                        principal.organization ? '/organization' : '/setup',
                        {
                            replace: true,
                        },
                    ),
            },
        );
    }

    const invalidCredentials =
        login.error instanceof ApiError &&
        login.error.code === 'invalid_credentials';
    const emailError = fieldError(login.error, 'email');
    const passwordError = fieldError(login.error, 'password');

    return (
        <AuthShell
            eyebrow="Welcome back"
            title="Sign in to Enact"
            lead="Continue your contract operations work."
            asideTitle="From signed agreement to verified change."
            asideText="Keep contract intent, operational decisions, and the resulting state connected in one workspace."
        >
            <form onSubmit={handleSubmit} className="grid gap-4">
                <FormField
                    label="Work email"
                    type="email"
                    autoComplete="email"
                    required
                    error={emailError}
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                />
                <FormField
                    label="Password"
                    type="password"
                    autoComplete="current-password"
                    required
                    error={passwordError}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                />
                {login.isError && !emailError && !passwordError && (
                    <FormError>
                        {invalidCredentials
                            ? 'Email or password was not recognized. Check your details and try again.'
                            : 'Sign-in could not be completed. Try again.'}
                    </FormError>
                )}
                <Button
                    variant="primary"
                    type="submit"
                    disabled={login.isPending}
                    className="mt-4 w-full"
                >
                    {login.isPending ? 'Signing in…' : 'Sign in'}
                </Button>
            </form>
            <p className="mt-6 text-sm text-secondary-text">
                New to Enact?{' '}
                <Link
                    to="/register"
                    className="font-semibold text-primary-text underline underline-offset-4"
                >
                    Create an account
                </Link>
            </p>
        </AuthShell>
    );
}
