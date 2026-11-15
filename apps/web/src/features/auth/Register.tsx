import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { ApiError } from '../../api/errors';
import { fieldError } from '../../utils/fieldErrors';
import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { FormError } from '../../components/ui/FormError';
import { AuthShell } from './AuthShell';
import { useRegistration, useSession } from './queries';

export function Register() {
    const session = useSession();
    const registration = useRegistration();
    const navigate = useNavigate();
    const [displayName, setDisplayName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [passwordFocused, setPasswordFocused] = useState(false);
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

        if (!displayName.trim() || !email.trim() || !password) {
            return;
        }

        registration.mutate(
            { display_name: displayName, email, password },
            { onSuccess: () => navigate('/setup', { replace: true }) },
        );
    }

    const duplicateEmail =
        registration.error instanceof ApiError &&
        registration.error.code === 'user_email_already_exists';
    const issues =
        registration.error instanceof ApiError
            ? registration.error.issues
            : undefined;
    const submittedName = registration.variables?.display_name === displayName;
    const submittedEmail = registration.variables?.email === email;
    const submittedPassword = registration.variables?.password === password;
    const nameError =
        submitted && !displayName.trim()
            ? 'Enter your name.'
            : submittedName
              ? fieldError(issues, ['body', 'display_name'], {
                    required: 'Enter your name.',
                    too_short: 'Enter your name.',
                    too_long: 'Use a shorter name.',
                })
              : undefined;
    const emailError =
        submitted && !email.trim()
            ? 'Enter your work email.'
            : submittedEmail && duplicateEmail
              ? 'An account already uses this email address.'
              : submittedEmail
                ? fieldError(issues, ['body', 'email'], {
                      required: 'Enter your work email.',
                      invalid: 'Enter a valid work email address.',
                  })
                : undefined;
    const passwordError =
        submitted && !password
            ? 'Create a password.'
            : submittedPassword
              ? fieldError(issues, ['body', 'password'], {
                    required: 'Create a password.',
                    too_short: 'Use at least 8 characters.',
                    too_long: 'Use a shorter password.',
                })
              : undefined;

    return (
        <AuthShell
            eyebrow="Get started"
            title="Create your account"
            lead="Set up your personal sign-in. You can create or join an organization next."
            asideTitle="Start with an account. Add your team next."
            asideText="Organization access is granted only after you create a workspace or redeem an invitation code."
        >
            <form
                noValidate
                onSubmit={handleSubmit}
                className="flex flex-col gap-4"
            >
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
                    hint={
                        passwordFocused && !passwordError
                            ? 'At least 8 characters.'
                            : undefined
                    }
                    error={passwordError}
                    value={password}
                    onFocus={() => setPasswordFocused(true)}
                    onBlur={() => setPasswordFocused(false)}
                    onChange={(event) => setPassword(event.target.value)}
                />
                {registration.isError &&
                    submittedName &&
                    submittedEmail &&
                    submittedPassword &&
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
