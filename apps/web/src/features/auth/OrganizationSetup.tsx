import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { ApiError } from '../../api/errors';
import { Button } from '../../components/ui/Button';
import { FormField } from '../../components/ui/FormField';
import { cn } from '../../utils/cn';
import { AuthShell, FormError } from './AuthShell';
import { fieldError } from './fieldErrors';
import { useOrganizationSetup, useSession } from './queries';

type Choice = 'create' | 'join';

/**
 * Creates a team or redeems an administrator-issued invitation code.
 *
 * @returns The organization setup form or a sign-in redirect.
 */
export function OrganizationSetup() {
    const session = useSession();
    const setup = useOrganizationSetup();
    const navigate = useNavigate();
    const [choice, setChoice] = useState<Choice>('create');
    const [name, setName] = useState('');
    const [code, setCode] = useState('');

    if (!session.data) {
        return <Navigate to="/sign-in" replace />;
    }

    /**
     * Applies the selected organization setup action.
     *
     * @param event - Native form submission.
     */
    function handleSubmit(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();

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
    const currentFieldError =
        choice === 'create'
            ? fieldError(setup.error, 'name')
            : invalidCode
              ? 'This code is invalid, expired, or already used.'
              : fieldError(setup.error, 'code');

    return (
        <AuthShell
            eyebrow="Your workspace"
            title="Where will you work?"
            lead="Create an organization for your team or join one with an invitation code."
            asideTitle="Your work stays within its organization."
            asideText="Choose your team before opening cases or reviewing operational data."
        >
            <fieldset className="mb-5 grid grid-cols-2 gap-3">
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
            <form onSubmit={handleSubmit} className="grid gap-5">
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
                {setup.isError && !currentFieldError && (
                    <FormError>
                        Organization setup could not be completed. Check your
                        details and try again.
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
