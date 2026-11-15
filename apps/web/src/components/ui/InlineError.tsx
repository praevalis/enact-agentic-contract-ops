import type { ReactNode } from 'react';

import { cn } from '../../utils/cn';

interface InlineErrorProps {
    children: ReactNode;
    className?: string;
    id?: string;
}

export function InlineError({ children, className, id }: InlineErrorProps) {
    return (
        <p
            id={id}
            role="alert"
            className={cn('text-sm text-status-danger', className)}
        >
            {children}
        </p>
    );
}
