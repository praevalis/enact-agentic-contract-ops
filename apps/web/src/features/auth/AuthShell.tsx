import type { ReactNode } from 'react';

interface AuthShellProps {
    eyebrow: string;
    title: string;
    lead: string;
    asideTitle: string;
    asideText: string;
    children: ReactNode;
}

export function AuthShell({
    eyebrow,
    title,
    lead,
    asideTitle,
    asideText,
    children,
}: AuthShellProps) {
    return (
        <main className="flex min-h-screen flex-col lg:flex-row">
            <div className="flex min-w-0 items-center px-4 py-10 sm:px-8 lg:flex-1 lg:px-12 lg:py-12">
                <div className="mx-auto w-full max-w-sm">
                    <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-umber">
                        {eyebrow}
                    </p>
                    <h1 className="mb-3 text-3xl font-semibold leading-9 tracking-tight">
                        {title}
                    </h1>
                    <p className="mb-8 text-base leading-6 text-secondary-text">
                        {lead}
                    </p>
                    {children}
                </div>
            </div>
            <aside className="flex min-h-56 min-w-0 flex-col justify-center bg-night px-4 py-10 text-white sm:px-8 lg:flex-1 lg:px-12 lg:py-12">
                <div
                    aria-hidden="true"
                    className="mb-8 flex items-center gap-3"
                >
                    <span className="h-2 w-20 rounded-sm bg-amber" />
                    <span className="h-2 w-11 rounded-sm bg-off-white" />
                    <span className="h-2 w-28 rounded-sm bg-amber" />
                </div>
                <h2 className="mb-4 max-w-xl text-2xl font-semibold leading-tight tracking-tight lg:text-5xl">
                    {asideTitle}
                </h2>
                <p className="max-w-lg text-base leading-6 text-steel">
                    {asideText}
                </p>
            </aside>
        </main>
    );
}
