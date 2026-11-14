import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { ApiError } from '../../api/errors';
import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { AuthShell, FormError } from './AuthShell';
import { fieldError } from './fieldErrors';
import { useRegistration, useSession } from './queries';

/**
 * Creates a local account before organization setup.
 *
 * @returns The registration form or an authenticated redirect.
 */
export function Register() {
    const session = useSession();
    const registration = useRegistration();
    const navigate = useNavigate();
    const [displayName, setDisplayName] = useState('');
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
     * Submits account details and opens organization setup on success.
     *
     * @param event - Native form submission.
     */
    function handleSubmit(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();

        registration.mutate(
            { display_name: displayName, email, password },
            { onSuccess: () => navigate('/setup', { replace: true }) },
        );
    }

    const duplicateEmail =
        registration.error instanceof ApiError &&
        registration.error.code === 'user_email_already_exists';
    const nameError = fieldError(registration.error, 'display_name');
    const emailError = duplicateEmail
        ? 'An account already uses this email address.'
        : fieldError(registration.error, 'email');
    const passwordError = fieldError(registration.error, 'password');

    return (
        <AuthShell
            eyebrow="Get started"
            title="Create your account"
            lead="Set up your personal sign-in. You can create or join an organization next."
            asideTitle="Start with an account. Add your team next."
            asideText="Organization access is granted only after you create a workspace or redeem an invitation code."
        >
            <form onSubmit={handleSubmit} className="grid gap-4">
                <FormField
                    label="Your name"
                    autoComplete="name"
                    required
                    maxLength={200}
                    error={nameError}
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                />
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
                    autoComplete="new-password"
                    required
                    minLength={8}
                    hint="At least 8 characters."
                    error={passwordError}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                />
                {registration.isError &&
                    !nameError &&
                    !emailError &&
                    !passwordError && (
                        <FormError>
                            Account creation could not be completed. Check your
                            details and try again.
                        </FormError>
                    )}
                <Button
                    variant="primary"
                    type="submit"
                    disabled={registration.isPending}
                    className="w-full"
                >
                    {registration.isPending
                        ? 'Creating account…'
                        : 'Create account'}
                </Button>
            </form>
            <p className="mt-6 text-sm text-secondary-text">
                Already have an account?{' '}
                <Link
                    to="/sign-in"
                    className="font-semibold text-primary-text underline underline-offset-4"
                >
                    Sign in
                </Link>
            </p>
        </AuthShell>
    );
}
