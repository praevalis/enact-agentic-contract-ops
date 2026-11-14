import { Outlet } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { useSession } from './queries';

/**
 * Waits for cookie restoration before auth routes decide where to navigate.
 *
 * @returns Auth routes, a loading state, or a retryable session error.
 */
export function SessionBoundary() {
    const session = useSession();

    if (session.isPending) {
        return (
            <main role="status" className="p-6">
                Checking your session…
            </main>
        );
    }

    if (session.isError) {
        return (
            <main className="mx-auto max-w-lg px-6 py-20">
                <h1 className="mb-3 text-xl font-semibold">
                    Unable to check your session
                </h1>
                <p className="mb-6 text-secondary-text">
                    Check your connection and try again.
                </p>
                <Button
                    variant="primary"
                    onClick={() => void session.refetch()}
                >
                    Try again
                </Button>
            </main>
        );
    }

    return <Outlet />;
}
