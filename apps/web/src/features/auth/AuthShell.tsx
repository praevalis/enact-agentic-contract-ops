import type { ReactNode } from 'react';

interface AuthShellProps {
    eyebrow: string;
    title: string;
    lead: string;
    asideTitle: string;
    asideText: string;
    children: ReactNode;
}

/**
 * Frames the account and organization setup forms.
 *
 * @param props - Form copy, supporting copy, and form content.
 * @returns The responsive auth layout.
 */
export function AuthShell({
    eyebrow,
    title,
    lead,
    asideTitle,
    asideText,
    children,
}: AuthShellProps) {
    return (
        <main className="grid min-h-screen min-[851px]:grid-cols-[minmax(340px,47%)_1fr]">
            <div className="flex items-center px-6 py-12 sm:px-12 min-[851px]:px-[clamp(24px,5vw,72px)]">
                <div className="mx-auto w-full max-w-[400px]">
                    <p className="mb-3 text-xs font-semibold uppercase tracking-[0.13em] text-umber">
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
            <aside className="flex min-h-56 flex-col justify-center bg-night px-8 py-12 text-white min-[851px]:px-[clamp(32px,6vw,88px)]">
                <div
                    aria-hidden="true"
                    className="mb-8 flex items-center gap-3"
                >
                    <span className="h-[9px] w-20 rounded-sm bg-amber" />
                    <span className="h-[9px] w-11 rounded-sm bg-off-white" />
                    <span className="h-[9px] w-28 rounded-sm bg-amber" />
                </div>
                <h2 className="mb-4 max-w-xl text-[26px] font-semibold leading-tight tracking-tight min-[851px]:text-[clamp(28px,3.4vw,48px)]">
                    {asideTitle}
                </h2>
                <p className="max-w-lg text-base leading-6 text-steel">
                    {asideText}
                </p>
            </aside>
        </main>
    );
}

interface FormErrorProps {
    children: ReactNode;
}

/**
 * Announces an auth flow failure beside its form.
 *
 * @param props - Recoverable error guidance.
 * @returns A visible, announced error notice.
 */
export function FormError({ children }: FormErrorProps) {
    return (
        <div role="alert" className="rounded-lg bg-inset px-4 py-3 text-sm">
            <p className="mb-1 font-semibold text-status-danger">Error</p>
            <p>{children}</p>
        </div>
    );
}
