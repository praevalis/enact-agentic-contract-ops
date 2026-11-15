import { useNavigate } from 'react-router-dom';
import { FiChevronDown, FiHome, FiPlus } from 'react-icons/fi';

import type { OrganizationMembership } from '../../api/contracts';
import { ApiError } from '../../api/errors';
import { Button } from '../../components/ui/Button';
import { Dropdown } from '../../components/ui/Dropdown';
import { InlineError } from '../../components/ui/InlineError';
import { cn } from '../../utils/cn';
import { useOrganizations, useSwitchOrganization } from './queries';

const roleLabels: Record<OrganizationMembership['membership']['role'], string> =
    {
        administrator: 'Administrator',
        deal_desk: 'Deal desk',
        operations_reviewer: 'Operations reviewer',
        auditor: 'Auditor',
    };

interface OrganizationPickerProps {
    current: OrganizationMembership;
}

export function OrganizationPicker({ current }: OrganizationPickerProps) {
    const organizations = useOrganizations();
    const switchOrganization = useSwitchOrganization();
    const navigate = useNavigate();

    function selectOrganization(
        organizationId: string,
        close: () => void,
    ): void {
        if (organizationId === current.organization.id) {
            close();
            return;
        }

        switchOrganization.mutate(organizationId, { onSuccess: close });
    }

    const unavailable =
        switchOrganization.error instanceof ApiError &&
        [
            'organization_membership_not_found',
            'organization_not_found',
        ].includes(switchOrganization.error.code);

    return (
        <section
            aria-label="Selected organization"
            className="mb-12 rounded-lg bg-inset p-5 sm:flex sm:items-center sm:justify-between sm:gap-5 sm:px-6"
        >
            <div className="flex min-w-0 items-center gap-4">
                <span className="grid size-11 shrink-0 place-items-center rounded-lg bg-umber text-white">
                    <FiHome className="size-6" aria-hidden="true" />
                </span>
                <div className="min-w-0">
                    <p className="text-xs font-semibold uppercase tracking-widest text-secondary-text">
                        Working in
                    </p>
                    <strong className="block truncate text-lg">
                        {current.organization.name}
                    </strong>
                    <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-secondary-text">
                        <span>{roleLabels[current.membership.role]}</span>
                        <span className="inline-flex items-center gap-1.5">
                            <span
                                aria-hidden="true"
                                className="size-1.5 rounded-full bg-status-success"
                            />
                            Active membership
                        </span>
                    </p>
                </div>
            </div>

            <Dropdown
                triggerLabel="Change organization"
                trigger={
                    <>
                        Change organization
                        <FiChevronDown className="size-5" aria-hidden="true" />
                    </>
                }
                disabled={switchOrganization.isPending}
                className="mt-5 sm:mt-0 sm:w-56 sm:shrink-0"
                panelWidth="wide"
                alignment="end"
            >
                {(close) => (
                    <>
                        <p className="px-2 py-2 text-xs font-semibold text-secondary-text">
                            Your organizations
                        </p>
                        {organizations.isPending && (
                            <p role="status" className="px-2 py-3 text-sm">
                                Loading organizations…
                            </p>
                        )}
                        {organizations.isError && (
                            <div className="px-2 py-3 text-sm">
                                <InlineError>
                                    Could not load organizations.
                                </InlineError>
                                <Button
                                    variant="quiet"
                                    type="button"
                                    onClick={() => void organizations.refetch()}
                                    className="mt-2 px-0"
                                >
                                    Try again
                                </Button>
                            </div>
                        )}
                        {organizations.data?.length === 0 && (
                            <p className="px-2 py-3 text-sm text-secondary-text">
                                No active organizations are available.
                            </p>
                        )}
                        {organizations.data && (
                            <ul className="flex flex-col gap-1">
                                {organizations.data.map((entry) => {
                                    const isCurrent =
                                        entry.organization.id ===
                                        current.organization.id;

                                    return (
                                        <li key={entry.organization.id}>
                                            <button
                                                type="button"
                                                aria-current={
                                                    isCurrent || undefined
                                                }
                                                disabled={
                                                    switchOrganization.isPending
                                                }
                                                onClick={() =>
                                                    selectOrganization(
                                                        entry.organization.id,
                                                        close,
                                                    )
                                                }
                                                className={cn(
                                                    'flex min-h-14 w-full items-center gap-3 rounded-md px-2 text-left text-sm hover:bg-control-hover focus-visible:outline-2 focus-visible:outline-focus disabled:opacity-60',
                                                    isCurrent && 'bg-inset',
                                                )}
                                            >
                                                <span
                                                    aria-hidden="true"
                                                    className="grid size-8 place-items-center rounded-md bg-umber text-xs font-semibold text-white"
                                                >
                                                    {entry.organization.name
                                                        .charAt(0)
                                                        .toUpperCase()}
                                                </span>
                                                <span className="min-w-0 flex-1">
                                                    <strong className="block truncate">
                                                        {
                                                            entry.organization
                                                                .name
                                                        }
                                                    </strong>
                                                    <span className="block text-xs text-secondary-text">
                                                        {
                                                            roleLabels[
                                                                entry.membership
                                                                    .role
                                                            ]
                                                        }
                                                    </span>
                                                </span>
                                                {isCurrent && (
                                                    <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-control-hover px-2 py-1 text-xs font-semibold text-status-success">
                                                        <span
                                                            aria-hidden="true"
                                                            className="size-1.5 rounded-full bg-status-success"
                                                        />
                                                        Current
                                                    </span>
                                                )}
                                            </button>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                        <button
                            type="button"
                            disabled={switchOrganization.isPending}
                            onClick={() => navigate('/setup')}
                            className="mt-1 flex min-h-14 w-full items-center gap-3 rounded-md px-2 text-left text-sm hover:bg-control-hover focus-visible:outline-2 focus-visible:outline-focus disabled:opacity-60"
                        >
                            <span
                                aria-hidden="true"
                                className="grid size-8 place-items-center rounded-md bg-inset"
                            >
                                <FiPlus className="size-5" aria-hidden="true" />
                            </span>
                            <span className="min-w-0 flex-1">
                                <strong className="block">
                                    Join or create organization
                                </strong>
                                <span className="block text-xs text-secondary-text">
                                    Use a code or start a new team
                                </span>
                            </span>
                        </button>
                        {switchOrganization.isError && (
                            <InlineError className="px-2 py-3">
                                {unavailable
                                    ? 'This organization is no longer available. Choose another.'
                                    : 'Could not change organization. Try again.'}
                            </InlineError>
                        )}
                    </>
                )}
            </Dropdown>
        </section>
    );
}
