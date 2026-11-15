import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { ApiError } from '../../api/errors';
import { fieldError } from '../../utils/fieldErrors';
import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { FormError } from '../../components/ui/FormError';
import { cn } from '../../utils/cn';
import { AuthShell } from './AuthShell';
import { useOrganizationSetup, useSession } from './queries';

type Choice = 'create' | 'join';

export function OrganizationSetup() {
    const session = useSession();
    const setup = useOrganizationSetup();
    const navigate = useNavigate();
    const [choice, setChoice] = useState<Choice>('create');
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [submitted, setSubmitted] = useState(false);

    if (!session.data) {
        return <Navigate to="/sign-in" replace />;
    }

    function handleSubmit(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();
        setSubmitted(true);

        if (choice === 'create' ? !name.trim() : !code.trim()) {
            return;
        }

        setup.mutate(
            choice === 'create'
                ? { kind: 'create', name }
                : { kind: 'join', code },
            { onSuccess: () => navigate('/organization', { replace: true }) },
        );
    }

    const invalidCode =
        setup.error instanceof ApiError &&
        setup.error.code === 'invalid_invitation_code';
    const issues =
        setup.error instanceof ApiError ? setup.error.issues : undefined;
    const submittedChoice = setup.variables?.kind === choice;
    const submittedName =
        setup.variables?.kind === 'create' && setup.variables.name === name;
    const submittedCode =
        setup.variables?.kind === 'join' && setup.variables.code === code;
    let currentFieldError: string | undefined;

    if (choice === 'create') {
        currentFieldError =
            submitted && !name.trim()
                ? 'Enter an organization name.'
                : submittedName
                  ? fieldError(issues, ['body', 'name'], {
                        required: 'Enter an organization name.',
                        too_short: 'Enter an organization name.',
                        too_long: 'Use a shorter organization name.',
                    })
                  : undefined;
    } else if (submitted && !code.trim()) {
        currentFieldError = 'Enter an invitation code.';
    } else if (submittedCode && invalidCode) {
        currentFieldError = 'This code is invalid, expired, or already used.';
    } else if (submittedCode) {
        currentFieldError = fieldError(issues, ['body', 'code'], {
            required: 'Enter an invitation code.',
            too_short: 'Enter an invitation code.',
            too_long: 'Check the invitation code and try again.',
        });
    }

    return (
        <AuthShell
            eyebrow="Your workspace"
            title="Where will you work?"
            lead="Create an organization for your team or join one with an invitation code."
            asideTitle="Your work stays within its organization."
            asideText="Choose your team before opening cases or reviewing operational data."
        >
            <fieldset className="mb-5 grid gap-3 sm:grid-cols-2">
                <legend className="sr-only">
                    Choose how to join a workspace
                </legend>
                <input
                    className="peer/create sr-only"
                    id="choice-create"
                    type="radio"
                    name="organization-choice"
                    checked={choice === 'create'}
                    onChange={() => {
                        setChoice('create');
                        setSubmitted(false);
                        setup.reset();
                    }}
                />
                <label
                    htmlFor="choice-create"
                    className={cn(
                        'min-h-32 cursor-pointer rounded-lg bg-surface p-4 text-left peer-focus-visible/create:ring-2 peer-focus-visible/create:ring-focus',
                        choice === 'create' && 'bg-inset shadow-md',
                    )}
                >
                    <strong className="mb-2 block text-sm">
                        Create an organization
                    </strong>
                    <span className="block text-xs leading-5 text-secondary-text">
                        Start a new team workspace. You’ll be its administrator.
                    </span>
                    {choice === 'create' && (
                        <span className="mt-3 block text-xs font-semibold">
                            ✓ Selected
                        </span>
                    )}
                </label>
                <input
                    className="peer/join sr-only"
                    id="choice-join"
                    type="radio"
                    name="organization-choice"
                    checked={choice === 'join'}
                    onChange={() => {
                        setChoice('join');
                        setSubmitted(false);
                        setup.reset();
                    }}
                />
                <label
                    htmlFor="choice-join"
                    className={cn(
                        'min-h-32 cursor-pointer rounded-lg bg-surface p-4 text-left peer-focus-visible/join:ring-2 peer-focus-visible/join:ring-focus',
                        choice === 'join' && 'bg-inset shadow-md',
                    )}
                >
                    <strong className="mb-2 block text-sm">
                        Join an organization
                    </strong>
                    <span className="block text-xs leading-5 text-secondary-text">
                        Use a one-time code shared by an administrator.
                    </span>
                    {choice === 'join' && (
                        <span className="mt-3 block text-xs font-semibold">
                            ✓ Selected
                        </span>
                    )}
                </label>
            </fieldset>
            <form
                noValidate
                onSubmit={handleSubmit}
                className="flex flex-col gap-5"
            >
                {choice === 'create' ? (
                    <FormField
                        label="Organization name"
                        required
                        maxLength={200}
                        hint="Use the name your team will recognize in the workspace."
                        error={currentFieldError}
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                    />
                ) : (
                    <FormField
                        label="Invitation code"
                        required
                        maxLength={64}
                        hint="Ask your organization administrator for a code."
                        error={currentFieldError}
                        value={code}
                        onChange={(event) => setCode(event.target.value)}
                    />
                )}
                {setup.isError &&
                    submittedChoice &&
                    (choice === 'create' ? submittedName : submittedCode) &&
                    !currentFieldError && (
                        <FormError>
                            Organization setup could not be completed. Check
                            your details and try again.
                        </FormError>
                    )}
                <Button
                    variant="primary"
                    type="submit"
                    disabled={setup.isPending}
                    className="w-full"
                >
                    {setup.isPending
                        ? 'Saving…'
                        : choice === 'create'
                          ? 'Create organization'
                          : 'Join organization'}
                </Button>
            </form>
        </AuthShell>
    );
}
