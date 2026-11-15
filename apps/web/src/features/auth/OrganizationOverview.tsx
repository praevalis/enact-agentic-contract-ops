import { Navigate, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { InlineError } from '../../components/ui/InlineError';
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
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-umber">
                Your workspace
            </p>
            <h1 className="mb-3 text-3xl font-semibold">Organization</h1>
            <p className="mb-8 text-base text-secondary-text">
                Choose the organization you want to work in.
            </p>
            <OrganizationPicker
                current={{
                    organization: session.data.organization,
                    membership: session.data.membership,
                }}
            />
            <div className="rounded-lg bg-inset p-6">
                <p className="text-sm text-secondary-text">Signed in as</p>
                <p className="mt-1 font-semibold">
                    {session.data.user.display_name}
                </p>
                <p className="text-sm text-secondary-text">
                    {session.data.user.email}
                </p>
                <p className="mt-4 text-sm">
                    {session.data.membership?.role.replaceAll('_', ' ')}
                </p>
            </div>
            <div className="mt-6 flex flex-wrap gap-4">
                <Button
                    variant="secondary"
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
            {signOut.isError && (
                <InlineError className="mt-4">
                    Sign-out could not be completed. Try again.
                </InlineError>
            )}
        </main>
    );
}
