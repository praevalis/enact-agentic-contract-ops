import { Navigate, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { InlineError } from '../../components/ui/InlineError';
import { InvitationIssuer } from './InvitationIssuer';
import { OrganizationPicker } from './OrganizationPicker';
import { useSession, useSignOut } from './queries';

export function OrganizationOverview() {
    const session = useSession();
    const signOut = useSignOut();
    const navigate = useNavigate();

    if (!session.data) {
        return <Navigate to="/sign-in" replace />;
    }

    if (!session.data.organization || !session.data.membership) {
        return <Navigate to="/setup" replace />;
    }

    return (
        <main className="mx-auto max-w-6xl px-4 py-10 sm:px-8 lg:py-12">
            <div className="mb-3 flex items-center justify-between gap-4">
                <p className="text-xs font-semibold uppercase tracking-widest text-umber">
                    Your workspace
                </p>
                <Button
                    variant="quiet"
                    size="small"
                    disabled={signOut.isPending}
                    onClick={() =>
                        signOut.mutate(undefined, {
                            onSuccess: () =>
                                navigate('/sign-in', { replace: true }),
                        })
                    }
                >
                    {signOut.isPending ? 'Signing out…' : 'Sign out'}
                </Button>
            </div>
            <h1 className="mb-3 text-3xl font-semibold">Organization</h1>
            <p className="mb-8 text-base text-secondary-text">
                Choose the organization you want to work in.
            </p>
            {signOut.isError && (
                <InlineError className="mb-4">
                    Sign-out could not be completed. Try again.
                </InlineError>
            )}
            <OrganizationPicker
                current={{
                    organization: session.data.organization,
                    membership: session.data.membership,
                }}
            />
            {session.data.membership.role === 'administrator' && (
                <section aria-labelledby="people-heading" className="mb-12">
                    <h2 id="people-heading" className="text-xl font-semibold">
                        People &amp; access
                    </h2>
                    <p className="mb-5 text-sm text-secondary-text">
                        Invite teammates to work in this organization.
                    </p>
                    <InvitationIssuer
                        key={session.data.organization.id}
                        organizationId={session.data.organization.id}
                    />
                </section>
            )}
        </main>
    );
}
