import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';

interface AppProvidersProps {
    children: ReactNode;
}

/**
 * Provides a query cache for one application tree.
 *
 * @param props - Application content using server state.
 * @returns The query client provider.
 */
export function AppProviders({ children }: AppProvidersProps) {
    const [queryClient] = useState(() => new QueryClient());

    return (
        <QueryClientProvider client={queryClient}>
            {children}
        </QueryClientProvider>
    );
}
