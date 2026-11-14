import { Link, Navigate, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { useSession, useSignOut } from './queries';

/**
 * Shows the active organization after account onboarding.
 *
 * @returns The current workspace summary or an auth redirect.
 */
export function OrganizationOverview() {
    const session = useSession();
    const signOut = useSignOut();
    const navigate = useNavigate();

    if (!session.data) {
        return <Navigate to="/sign-in" replace />;
    }

    if (!session.data.organization) {
        return <Navigate to="/setup" replace />;
    }

    return (
        <main className="mx-auto max-w-5xl px-4 py-10 sm:px-8 lg:px-12 lg:py-12">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-umber">
                Your workspace
            </p>
            <h1 className="mb-3 text-3xl font-semibold">Organization</h1>
            <p className="mb-8 text-base text-secondary-text">
                Working in {session.data.organization.name}
            </p>
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
                <Link
                    to="/setup"
                    className="inline-flex min-h-11 items-center text-sm font-semibold underline underline-offset-4"
                >
                    Join or create another organization
                </Link>
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
                <p role="alert" className="mt-4 text-sm text-status-danger">
                    Sign-out could not be completed. Try again.
                </p>
            )}
        </main>
    );
}
