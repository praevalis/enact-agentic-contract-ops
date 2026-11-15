import { useEffect, useRef, useState, type FormEvent } from 'react';
import { FiEdit2 } from 'react-icons/fi';

import { ApiError } from '../../api/errors';
import { Button } from '../../components/ui/Button';
import { FormError } from '../../components/ui/FormError';
import { InlineError } from '../../components/ui/InlineError';
import { Input } from '../../components/ui/Input';
import { fieldError } from '../../utils/fieldErrors';
import { useRenameOrganization } from './organizationManagementQueries';

interface OrganizationIdentityProps {
    organizationId: string;
    name: string;
    administrator: boolean;
}

export function OrganizationIdentity({
    organizationId,
    name,
    administrator,
}: OrganizationIdentityProps) {
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState(name);
    const [localNameError, setLocalNameError] = useState<string>();
    const rename = useRenameOrganization();
    const inputRef = useRef<HTMLInputElement>(null);
    const editRef = useRef<HTMLButtonElement>(null);
    const wasEditing = useRef(false);

    useEffect(() => {
        if (editing) {
            wasEditing.current = true;
            inputRef.current?.focus();
        } else if (wasEditing.current) {
            editRef.current?.focus();
            wasEditing.current = false;
        }
    }, [editing]);

    function closeEditor(): void {
        setDraft(name);
        setLocalNameError(undefined);
        rename.reset();
        setEditing(false);
    }

    function saveName(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();
        const normalized = draft.trim();
        if (normalized === name) {
            return;
        }

        if (!normalized || normalized.length > 200) {
            setLocalNameError('Enter a name between 1 and 200 characters.');
            inputRef.current?.focus();
            return;
        }

        setLocalNameError(undefined);
        rename.mutate(
            { organizationId, name: draft },
            { onSuccess: () => setEditing(false) },
        );
    }

    const unavailable =
        rename.error instanceof ApiError &&
        rename.error.code === 'organization_not_found';
    const serverNameError =
        rename.error instanceof ApiError && rename.variables?.name === draft
            ? fieldError(rename.error.issues, ['body', 'name'], {
                  required: 'Enter an organization name.',
                  too_short: 'Enter an organization name.',
                  too_long: 'Use 200 characters or fewer.',
                  invalid: 'Check the organization name.',
              })
            : undefined;
    const nameError = localNameError ?? serverNameError;
    const nameChanged = draft.trim() !== name;

    return (
        <section
            aria-labelledby="identity-heading"
            className="mt-12 grid gap-5 lg:grid-cols-4 lg:gap-14"
        >
            <div>
                <span className="font-mono text-xs tracking-wider text-umber">
                    01
                </span>
                <h2
                    id="identity-heading"
                    className="mt-3 text-xl font-semibold"
                >
                    Organization identity
                </h2>
                <p className="mt-2 text-sm text-secondary-text">
                    Keep the team name recognizable for everyone who works here.
                </p>
            </div>
            <div className="min-w-0 lg:col-span-3">
                <form onSubmit={saveName} className="max-w-lg">
                    <label
                        htmlFor="organization-name"
                        className="mb-3 block text-base font-semibold"
                    >
                        Organization name
                    </label>
                    <div className="flex items-center gap-3">
                        <Input
                            ref={inputRef}
                            id="organization-name"
                            value={editing ? draft : name}
                            disabled={!editing || rename.isPending}
                            className="disabled:opacity-100"
                            invalid={Boolean(nameError)}
                            aria-describedby={
                                nameError
                                    ? 'organization-name-error'
                                    : undefined
                            }
                            onChange={(event) => {
                                setDraft(event.target.value);
                                setLocalNameError(undefined);
                                rename.reset();
                            }}
                        />
                        {administrator && !editing && (
                            <Button
                                ref={editRef}
                                variant="quiet"
                                size="small"
                                className="shrink-0 gap-2"
                                onClick={() => {
                                    setDraft(name);
                                    setEditing(true);
                                }}
                            >
                                <FiEdit2 aria-hidden="true" />
                                Edit
                            </Button>
                        )}
                    </div>
                    {nameError && (
                        <InlineError
                            id="organization-name-error"
                            className="mt-2"
                        >
                            {nameError}
                        </InlineError>
                    )}
                    {rename.isError && !serverNameError && (
                        <FormError>
                            {unavailable
                                ? 'This organization is no longer available.'
                                : 'Could not save the organization name. Try again.'}
                        </FormError>
                    )}
                    {editing && (
                        <div className="mt-5 flex w-full gap-3 sm:w-64">
                            <Button
                                variant="primary"
                                type="submit"
                                className="min-w-0 flex-1"
                                disabled={rename.isPending || !nameChanged}
                            >
                                {rename.isPending ? 'Saving…' : 'Save name'}
                            </Button>
                            <Button
                                variant="raised"
                                className="min-w-0 flex-1"
                                disabled={rename.isPending}
                                onClick={closeEditor}
                            >
                                Cancel
                            </Button>
                        </div>
                    )}
                </form>
            </div>
        </section>
    );
}
