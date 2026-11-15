import type { ReactNode } from 'react';

interface FormErrorProps {
    children: ReactNode;
}

export function FormError({ children }: FormErrorProps) {
    return (
        <div role="alert" className="rounded-lg bg-inset px-4 py-3 text-sm">
            <p className="mb-1 font-semibold text-status-danger">Error</p>
            <p>{children}</p>
        </div>
    );
}
