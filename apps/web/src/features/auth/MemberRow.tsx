import { useEffect, useRef, useState } from 'react';
import {
    FiCheck,
    FiChevronDown,
    FiEdit2,
    FiMoreVertical,
    FiMinus,
    FiTrash2,
} from 'react-icons/fi';

import type { MembershipRole, OrganizationMember } from '../../api/contracts';
import { ApiError } from '../../api/errors';
import { Button } from '../../components/ui/Button';
import { Dropdown } from '../../components/ui/Dropdown';
import { FormError } from '../../components/ui/FormError';
import { cn } from '../../utils/cn';
import { roleOptions, roleOrder } from './membershipRoles';
import {
    useChangeMemberRole,
    useRemoveMember,
} from './organizationManagementQueries';

interface MemberRowProps {
    member: OrganizationMember;
    organizationId: string;
    administrator: boolean;
    currentUserId: string;
    colorIndex: number;
    onRemoved: () => void;
}

const avatarColors = [
    'bg-umber text-white',
    'bg-graphite text-white',
    'bg-steel text-night',
    'bg-edge text-white',
    'bg-status-processing text-white',
] as const;

export function MemberRow({
    member,
    organizationId,
    administrator,
    currentUserId,
    colorIndex,
    onRemoved,
}: MemberRowProps) {
    const [mode, setMode] = useState<'closed' | 'role' | 'remove'>('closed');
    const [selectedRole, setSelectedRole] = useState<MembershipRole>(
        member.role,
    );
    const changeRole = useChangeMemberRole();
    const remove = useRemoveMember();
    const headingRef = useRef<HTMLHeadingElement>(null);
    const actionsRef = useRef<HTMLDivElement>(null);
    const option = roleOptions[member.role];
    const initials = member.display_name
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join('');

    useEffect(() => {
        if (mode !== 'closed') {
            headingRef.current?.focus();
        }
    }, [mode]);

    function closeEditor(): void {
        changeRole.reset();
        remove.reset();
        setMode('closed');
        actionsRef.current?.querySelector('button')?.focus();
    }

    const mutationError = changeRole.error ?? remove.error;
    const lastAdministrator =
        mutationError instanceof ApiError &&
        mutationError.code === 'last_administrator_required';
    const unavailable =
        mutationError instanceof ApiError &&
        mutationError.code === 'membership_not_found';

    return (
        <li className="relative">
            <div
                className={cn(
                    'flex items-start gap-3 rounded-lg bg-member-row px-3 py-3 sm:items-center sm:gap-4 sm:px-4',
                    mode !== 'closed' && 'rounded-b-none',
                )}
            >
                <span
                    aria-hidden="true"
                    className={cn(
                        'grid size-10 shrink-0 place-items-center rounded-md text-xs font-semibold',
                        avatarColors[colorIndex % avatarColors.length],
                    )}
                >
                    {initials}
                </span>
                <div className="flex min-w-0 flex-1 flex-col gap-5 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
                    <div className="min-w-0">
                        <strong className="block truncate text-sm">
                            {member.display_name}
                        </strong>
                        <span className="block truncate text-xs text-secondary-text">
                            {member.email}
                        </span>
                    </div>
                    <span
                        className={cn(
                            'inline-flex w-fit shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold',
                            option.badgeClass,
                        )}
                    >
                        {option.label}
                    </span>
                </div>
                {administrator && (
                    <div ref={actionsRef} className="w-10 shrink-0">
                        <Dropdown
                            triggerLabel={`Actions for ${member.display_name}`}
                            trigger={
                                <FiMoreVertical
                                    className="size-4"
                                    aria-hidden="true"
                                />
                            }
                            panelWidth="menu"
                            alignment="end"
                            triggerAppearance="icon"
                        >
                            {(close) => (
                                <div className="flex flex-col gap-1">
                                    <button
                                        type="button"
                                        className="flex min-h-10 items-center gap-2 rounded-md px-3 text-left text-sm hover:bg-control-hover focus-visible:outline-2 focus-visible:outline-focus"
                                        onClick={() => {
                                            setSelectedRole(member.role);
                                            setMode('role');
                                            close();
                                        }}
                                    >
                                        <FiEdit2 aria-hidden="true" />
                                        Update role
                                    </button>
                                    <button
                                        type="button"
                                        className="flex min-h-10 items-center gap-2 rounded-md px-3 text-left text-sm hover:bg-control-hover focus-visible:outline-2 focus-visible:outline-focus"
                                        onClick={() => {
                                            setMode('remove');
                                            close();
                                        }}
                                    >
                                        <FiTrash2 aria-hidden="true" />
                                        Remove member
                                    </button>
                                </div>
                            )}
                        </Dropdown>
                    </div>
                )}
            </div>
            {mode !== 'closed' && (
                <div className="rounded-b-lg bg-surface px-4 py-5">
                    <div className="flex flex-col gap-4 md:flex-row md:items-center">
                        <div className="flex min-w-0 items-start gap-3 md:flex-1">
                            <span
                                className={cn(
                                    'grid size-7 shrink-0 place-items-center rounded-md',
                                    mode === 'role'
                                        ? 'bg-umber/15 text-umber'
                                        : 'bg-status-danger/15 text-status-danger',
                                )}
                            >
                                {mode === 'role' ? (
                                    <FiEdit2 aria-hidden="true" />
                                ) : (
                                    <FiMinus aria-hidden="true" />
                                )}
                            </span>
                            <div>
                                <h4
                                    ref={headingRef}
                                    tabIndex={-1}
                                    className="text-sm font-semibold"
                                >
                                    {mode === 'role'
                                        ? `Update role for ${member.display_name}`
                                        : `Remove ${member.display_name}?`}
                                </h4>
                                <p className="mt-1 text-xs text-secondary-text">
                                    {mode === 'role'
                                        ? 'Choose what this person can do in the organization.'
                                        : member.user_id === currentUserId
                                          ? 'Your access will end and you will be signed out.'
                                          : 'Their access to this organization will end.'}
                                </p>
                            </div>
                        </div>
                        {mode === 'role' && (
                            <Dropdown
                                triggerLabel={`New role for ${member.display_name}: ${roleOptions[selectedRole].label}`}
                                trigger={
                                    <>
                                        {roleOptions[selectedRole].label}
                                        <FiChevronDown aria-hidden="true" />
                                    </>
                                }
                                disabled={changeRole.isPending}
                                className="w-full sm:max-w-xs md:w-40 md:shrink-0 lg:w-56"
                                panelWidth="trigger"
                            >
                                {(close) => (
                                    <ul className="flex flex-col gap-1">
                                        {roleOrder.map((role) => (
                                            <li key={role}>
                                                <button
                                                    type="button"
                                                    aria-pressed={
                                                        selectedRole === role
                                                    }
                                                    onClick={() => {
                                                        setSelectedRole(role);
                                                        close();
                                                    }}
                                                    className="flex min-h-12 w-full items-center gap-3 rounded-md px-2 text-left hover:bg-control-hover focus-visible:outline-2 focus-visible:outline-focus"
                                                >
                                                    <span
                                                        aria-hidden="true"
                                                        className={cn(
                                                            'size-3 shrink-0 rounded-full',
                                                            roleOptions[role]
                                                                .dotClass,
                                                        )}
                                                    />
                                                    <span className="min-w-0 flex-1">
                                                        <strong className="block text-sm">
                                                            {
                                                                roleOptions[
                                                                    role
                                                                ].label
                                                            }
                                                        </strong>
                                                        <span className="block text-xs text-secondary-text">
                                                            {
                                                                roleOptions[
                                                                    role
                                                                ].description
                                                            }
                                                        </span>
                                                    </span>
                                                    {selectedRole === role && (
                                                        <FiCheck
                                                            className="shrink-0"
                                                            aria-hidden="true"
                                                        />
                                                    )}
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </Dropdown>
                        )}
                        <div className="flex w-full gap-2 sm:max-w-xs md:w-44 md:shrink-0 lg:w-56">
                            <Button
                                variant={mode === 'role' ? 'primary' : 'danger'}
                                size="small"
                                className="min-w-0 flex-1"
                                disabled={
                                    changeRole.isPending ||
                                    remove.isPending ||
                                    (mode === 'role' &&
                                        selectedRole === member.role)
                                }
                                onClick={() => {
                                    if (mode === 'role') {
                                        changeRole.mutate(
                                            {
                                                organizationId,
                                                membershipId: member.id,
                                                userId: member.user_id,
                                                role: selectedRole,
                                            },
                                            { onSuccess: closeEditor },
                                        );
                                    } else {
                                        remove.mutate(
                                            {
                                                organizationId,
                                                membershipId: member.id,
                                                userId: member.user_id,
                                            },
                                            { onSuccess: onRemoved },
                                        );
                                    }
                                }}
                            >
                                {mode === 'role' ? 'Save role' : 'Remove'}
                            </Button>
                            <Button
                                variant="raised"
                                size="small"
                                className="min-w-0 flex-1"
                                disabled={
                                    changeRole.isPending || remove.isPending
                                }
                                onClick={closeEditor}
                            >
                                Cancel
                            </Button>
                        </div>
                    </div>
                    {mutationError && (
                        <div className="mt-4">
                            <FormError>
                                {lastAdministrator
                                    ? 'Assign another administrator before changing this membership.'
                                    : unavailable
                                      ? 'This member is no longer available.'
                                      : 'Could not update this member. Try again.'}
                            </FormError>
                        </div>
                    )}
                </div>
            )}
        </li>
    );
}
