import { useRef, useState } from 'react';
import { FiArrowLeft, FiArrowRight } from 'react-icons/fi';

import { Button } from '../../components/ui/Button';
import { InlineError } from '../../components/ui/InlineError';
import { InvitationIssuer } from './InvitationIssuer';
import { MemberRow } from './MemberRow';
import {
    memberPageSize,
    useOrganizationMembers,
} from './organizationManagementQueries';

interface OrganizationMembersProps {
    organizationId: string;
    currentUserId: string;
    administrator: boolean;
}

export function OrganizationMembers({
    organizationId,
    currentUserId,
    administrator,
}: OrganizationMembersProps) {
    const [cursors, setCursors] = useState<(string | null)[]>([null]);
    const currentCursor = cursors[cursors.length - 1] ?? null;
    const page = useOrganizationMembers(organizationId, currentCursor);
    const sectionHeadingRef = useRef<HTMLHeadingElement>(null);
    const pageIndex = cursors.length - 1;
    const count = page.data?.total_count;
    const pageStart =
        count && page.data?.items.length ? pageIndex * memberPageSize + 1 : 0;
    const pageEnd = pageStart
        ? pageStart + (page.data?.items.length ?? 0) - 1
        : 0;

    return (
        <section
            aria-labelledby="members-heading"
            className="mt-12 grid gap-5 lg:grid-cols-4 lg:gap-14"
        >
            <div>
                <span className="font-mono text-xs tracking-wider text-umber">
                    02
                </span>
                <h2
                    ref={sectionHeadingRef}
                    tabIndex={-1}
                    id="members-heading"
                    className="mt-3 text-xl font-semibold"
                >
                    People &amp; access
                </h2>
                <p className="mt-2 text-sm text-secondary-text">
                    Review who can work in this organization and what they can
                    do.
                </p>
                {count !== undefined && (
                    <p className="mt-5 flex items-center gap-2 text-xs font-semibold text-status-success">
                        <span
                            aria-hidden="true"
                            className="size-2 rounded-full bg-status-success"
                        />
                        {count} active {count === 1 ? 'member' : 'members'}
                    </p>
                )}
            </div>
            <div className="min-w-0 lg:col-span-3">
                {administrator ? (
                    <InvitationIssuer organizationId={organizationId} />
                ) : (
                    <h3 className="mb-5 text-base font-semibold">
                        Team members
                    </h3>
                )}
                {page.isPending && (
                    <p role="status" className="text-sm text-secondary-text">
                        Loading members…
                    </p>
                )}
                {page.isError && (
                    <div>
                        <InlineError>Could not load members.</InlineError>
                        <Button
                            variant="quiet"
                            onClick={() => void page.refetch()}
                            className="mt-2"
                        >
                            Try again
                        </Button>
                    </div>
                )}
                {page.data?.items.length === 0 && (
                    <p className="rounded-lg bg-inset px-4 py-6 text-sm text-secondary-text">
                        No active members are available.
                    </p>
                )}
                {page.data && page.data.items.length > 0 && (
                    <>
                        <ul className="flex flex-col gap-2">
                            {page.data.items.map((member, index) => (
                                <MemberRow
                                    key={member.id}
                                    member={member}
                                    organizationId={organizationId}
                                    administrator={administrator}
                                    currentUserId={currentUserId}
                                    colorIndex={
                                        pageIndex * memberPageSize + index
                                    }
                                    onRemoved={() => {
                                        if (
                                            page.data.items.length === 1 &&
                                            pageIndex > 0
                                        ) {
                                            setCursors((previous) =>
                                                previous.slice(0, -1),
                                            );
                                        }
                                        sectionHeadingRef.current?.focus();
                                    }}
                                />
                            ))}
                        </ul>
                        {(pageIndex > 0 || page.data.next_cursor) && (
                            <div className="mt-5 flex items-center justify-between gap-2 text-xs text-secondary-text">
                                <span>
                                    Showing {pageStart}–{pageEnd} of {count}{' '}
                                    members
                                </span>
                                <div className="flex items-center gap-1">
                                    <Button
                                        variant="quiet"
                                        size="small"
                                        disabled={pageIndex === 0}
                                        onClick={() =>
                                            setCursors((previous) =>
                                                previous.slice(0, -1),
                                            )
                                        }
                                    >
                                        <FiArrowLeft
                                            aria-hidden="true"
                                            className="mr-1"
                                        />
                                        Previous
                                    </Button>
                                    <Button
                                        variant="quiet"
                                        size="small"
                                        disabled={!page.data.next_cursor}
                                        onClick={() => {
                                            if (page.data.next_cursor) {
                                                setCursors((previous) => [
                                                    ...previous,
                                                    page.data.next_cursor,
                                                ]);
                                            }
                                        }}
                                    >
                                        Next
                                        <FiArrowRight
                                            aria-hidden="true"
                                            className="ml-1"
                                        />
                                    </Button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </section>
    );
}
