import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { FormError } from '../../components/ui/FormError';
import { ApiError } from '../../api/errors';
import { fieldError } from '../../utils/fieldErrors';
import { AuthShell } from './AuthShell';
import { useLogin, useSession } from './queries';

export function SignIn() {
    const session = useSession();
    const login = useLogin();
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [submitted, setSubmitted] = useState(false);

    if (session.data) {
        return (
            <Navigate
                to={session.data.organization ? '/organization' : '/setup'}
                replace
            />
        );
    }

    function handleSubmit(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();
        setSubmitted(true);

        if (!email.trim() || !password) {
            return;
        }

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
    const issues =
        login.error instanceof ApiError ? login.error.issues : undefined;
    const submittedEmail = login.variables?.email === email;
    const submittedPassword = login.variables?.password === password;
    const emailError =
        submitted && !email.trim()
            ? 'Enter your work email.'
            : submittedEmail
              ? fieldError(issues, ['body', 'email'], {
                    required: 'Enter your work email.',
                    invalid: 'Enter a valid work email address.',
                })
              : undefined;
    const passwordError =
        submitted && !password
            ? 'Enter your password.'
            : submittedPassword
              ? fieldError(issues, ['body', 'password'], {
                    required: 'Enter your password.',
                    too_short: 'Enter your password.',
                })
              : undefined;

    return (
        <AuthShell
            eyebrow="Welcome back"
            title="Sign in to Enact"
            lead="Continue your contract operations work."
            asideTitle="From signed agreement to verified change."
            asideText="Keep contract intent, operational decisions, and the resulting state connected in one workspace."
        >
            <form
                noValidate
                onSubmit={handleSubmit}
                className="flex flex-col gap-4"
            >
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
                {login.isError &&
                    submittedEmail &&
                    submittedPassword &&
                    !emailError &&
                    !passwordError && (
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
