import { Navigate } from 'react-router-dom';

import { OrganizationIdentity } from './OrganizationIdentity';
import { OrganizationMembers } from './OrganizationMembers';
import { OrganizationPicker } from './OrganizationPicker';
import { useSession } from './queries';

export function OrganizationOverview() {
    const session = useSession();

    if (!session.data) {
        return <Navigate to="/sign-in" replace />;
    }

    if (!session.data.organization || !session.data.membership) {
        return <Navigate to="/setup" replace />;
    }

    return (
        <main className="mx-auto max-w-6xl px-4 py-10 sm:px-8 lg:py-12">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-umber">
                Your workspace
            </p>
            <h1 className="mb-3 text-3xl font-semibold">Organization</h1>
            <p className="mb-8 text-base text-secondary-text">
                Choose a team, then manage its details and people in one place.
            </p>
            <OrganizationPicker
                current={{
                    organization: session.data.organization,
                    membership: session.data.membership,
                }}
            />
            <OrganizationIdentity
                key={`${session.data.organization.id}-identity`}
                organizationId={session.data.organization.id}
                name={session.data.organization.name}
                administrator={session.data.membership.role === 'administrator'}
            />
            <OrganizationMembers
                key={`${session.data.organization.id}-members`}
                organizationId={session.data.organization.id}
                currentUserId={session.data.user.id}
                administrator={session.data.membership.role === 'administrator'}
            />
        </main>
    );
}
