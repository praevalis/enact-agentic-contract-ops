import { useEffect, useRef, useState, type FormEvent } from 'react';
import { FiCheck, FiChevronDown, FiPlus } from 'react-icons/fi';

import type { MembershipRole } from '../../api/contracts';
import { ApiError } from '../../api/errors';
import { Button } from '../../components/ui/Button';
import { Dropdown } from '../../components/ui/Dropdown';
import { FormError } from '../../components/ui/FormError';
import { InlineError } from '../../components/ui/InlineError';
import { cn } from '../../utils/cn';
import { roleOptions, roleOrder } from './membershipRoles';
import { useIssueInvitation } from './queries';

interface InvitationIssuerProps {
    organizationId: string;
}

export function InvitationIssuer({ organizationId }: InvitationIssuerProps) {
    const [open, setOpen] = useState(false);
    const [role, setRole] = useState<MembershipRole>('deal_desk');
    const [copied, setCopied] = useState(false);
    const [copyFailed, setCopyFailed] = useState(false);
    const issue = useIssueInvitation();
    const triggerRef = useRef<HTMLButtonElement>(null);
    const editorHeadingRef = useRef<HTMLHeadingElement>(null);
    const resultHeadingRef = useRef<HTMLHeadingElement>(null);
    const wasOpened = useRef(false);

    useEffect(() => {
        if (open) {
            wasOpened.current = true;
            editorHeadingRef.current?.focus();
        } else if (wasOpened.current) {
            triggerRef.current?.focus();
            wasOpened.current = false;
        }
    }, [open]);

    useEffect(() => {
        if (issue.data) {
            resultHeadingRef.current?.focus();
        }
    }, [issue.data]);

    function closeEditor(): void {
        issue.reset();
        setRole('deal_desk');
        setCopied(false);
        setCopyFailed(false);
        setOpen(false);
    }

    function createCode(event: FormEvent<HTMLFormElement>): void {
        event.preventDefault();
        issue.mutate({ organizationId, role });
    }

    async function copyCode(): Promise<void> {
        if (!issue.data) {
            return;
        }

        try {
            await navigator.clipboard.writeText(issue.data.code);
            setCopied(true);
            setCopyFailed(false);
        } catch {
            setCopyFailed(true);
        }
    }

    const permissionDenied =
        issue.error instanceof ApiError &&
        issue.error.code === 'membership_permission_denied';
    const organizationUnavailable =
        issue.error instanceof ApiError &&
        issue.error.code === 'organization_not_found';

    return (
        <>
            <div className="mb-5 flex items-center justify-between gap-4">
                <h3 className="text-base font-semibold">Team members</h3>
                {!open && (
                    <Button
                        ref={triggerRef}
                        variant="primary"
                        size="small"
                        onClick={() => setOpen(true)}
                        className="shrink-0 gap-2"
                    >
                        <FiPlus className="size-4" aria-hidden="true" />
                        Invite member
                    </Button>
                )}
            </div>
            {open && (
                <div className="mb-6 rounded-lg bg-surface p-5 sm:p-6">
                    <div className="mb-5 flex items-start gap-3">
                        <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-umber text-white">
                            <FiPlus className="size-5" aria-hidden="true" />
                        </span>
                        <div>
                            <h4
                                ref={editorHeadingRef}
                                tabIndex={-1}
                                className="text-base font-semibold"
                            >
                                Invite a teammate
                            </h4>
                            <p className="text-sm text-secondary-text">
                                Generate a one-time code to share with the
                                person joining.
                            </p>
                        </div>
                    </div>

                    {issue.data ? (
                        <div>
                            <h5
                                ref={resultHeadingRef}
                                tabIndex={-1}
                                className="text-sm font-semibold text-status-success"
                            >
                                Your invitation code is ready
                            </h5>
                            <p className="mt-2 text-sm text-secondary-text">
                                Please copy it now. You won't be able to view it
                                again after closing this panel.
                            </p>
                            <p className="mt-4 select-all break-all rounded-lg bg-surface px-4 py-3 font-mono text-base font-medium">
                                {issue.data.code}
                            </p>
                            <p className="mt-3 text-xs text-secondary-text">
                                Expires{' '}
                                <time dateTime={issue.data.expires_at}>
                                    {new Date(
                                        issue.data.expires_at,
                                    ).toLocaleString(undefined, {
                                        dateStyle: 'medium',
                                        timeStyle: 'short',
                                    })}
                                </time>
                                . Share it through a trusted channel.
                            </p>
                            {copyFailed && (
                                <InlineError className="mt-3">
                                    Could not copy the code. Select it to copy
                                    it manually.
                                </InlineError>
                            )}
                            {copied && (
                                <p
                                    role="status"
                                    className="mt-3 text-sm text-secondary-text"
                                >
                                    Copied to clipboard.
                                </p>
                            )}
                            <div className="mt-5 flex w-full gap-3 sm:max-w-md">
                                <Button
                                    variant="raised"
                                    className="min-w-0 flex-1"
                                    onClick={() => void copyCode()}
                                >
                                    {copied ? 'Copied' : 'Copy code'}
                                </Button>
                                <Button
                                    variant="primary"
                                    className="min-w-0 flex-1"
                                    onClick={closeEditor}
                                >
                                    Done
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <form
                            onSubmit={createCode}
                            className="flex flex-wrap items-end justify-between gap-3 sm:gap-4"
                        >
                            <div className="w-full sm:w-80">
                                <p className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-secondary-text">
                                    Role for new member
                                </p>
                                <Dropdown
                                    triggerLabel={`Role for new member: ${roleOptions[role].label}`}
                                    trigger={
                                        <>
                                            {roleOptions[role].label}
                                            <FiChevronDown
                                                className="size-5"
                                                aria-hidden="true"
                                            />
                                        </>
                                    }
                                    disabled={issue.isPending}
                                    className="w-full"
                                >
                                    {(close) => (
                                        <ul className="flex flex-col gap-1">
                                            {roleOrder.map((value) => {
                                                const option =
                                                    roleOptions[value];

                                                return (
                                                    <li key={value}>
                                                        <button
                                                            type="button"
                                                            aria-label={`${option.label}. ${option.description}`}
                                                            aria-pressed={
                                                                role === value
                                                            }
                                                            onClick={() => {
                                                                setRole(value);
                                                                issue.reset();
                                                                close();
                                                            }}
                                                            className={cn(
                                                                'flex min-h-14 w-full items-center gap-3 rounded-md px-2 py-2 text-left hover:bg-control-hover focus-visible:outline-2 focus-visible:outline-focus',
                                                                role ===
                                                                    value &&
                                                                    'bg-control-hover',
                                                            )}
                                                        >
                                                            <span
                                                                aria-hidden="true"
                                                                className={cn(
                                                                    'size-3 shrink-0 rounded-full',
                                                                    option.dotClass,
                                                                )}
                                                            />
                                                            <span className="min-w-0 flex-1">
                                                                <strong className="block text-sm">
                                                                    {
                                                                        option.label
                                                                    }
                                                                </strong>
                                                                <span className="block text-xs text-secondary-text">
                                                                    {
                                                                        option.description
                                                                    }
                                                                </span>
                                                            </span>
                                                            {role === value && (
                                                                <FiCheck
                                                                    className="size-4 shrink-0"
                                                                    aria-hidden="true"
                                                                />
                                                            )}
                                                        </button>
                                                    </li>
                                                );
                                            })}
                                        </ul>
                                    )}
                                </Dropdown>
                            </div>
                            {issue.isError && (
                                <div className="order-last w-full">
                                    <FormError>
                                        {permissionDenied
                                            ? 'You no longer have permission to invite members to this organization.'
                                            : organizationUnavailable
                                              ? 'This organization is no longer available.'
                                              : 'Could not create an invitation code. Try again.'}
                                    </FormError>
                                </div>
                            )}
                            <div className="flex w-full gap-2 sm:w-56 sm:shrink-0 sm:gap-3">
                                <Button
                                    variant="primary"
                                    size="small"
                                    type="submit"
                                    disabled={issue.isPending}
                                    className="min-w-0 flex-1"
                                >
                                    {issue.isPending
                                        ? 'Creating code…'
                                        : 'Create code'}
                                </Button>
                                <Button
                                    variant="raised"
                                    size="small"
                                    type="button"
                                    onClick={closeEditor}
                                    disabled={issue.isPending}
                                    className="min-w-0 flex-1"
                                >
                                    Cancel
                                </Button>
                            </div>
                        </form>
                    )}
                </div>
            )}
        </>
    );
}
