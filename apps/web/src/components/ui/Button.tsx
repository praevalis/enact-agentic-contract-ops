import { cva, type VariantProps } from 'class-variance-authority';
import type { ButtonHTMLAttributes } from 'react';

import { cn } from '../../utils/cn';

const buttonStyles = cva(
    'inline-flex min-h-11 items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus disabled:cursor-not-allowed disabled:opacity-50',
    {
        variants: {
            variant: {
                primary: 'bg-amber text-night hover:bg-amber/90',
                secondary: 'bg-inset text-primary-text hover:bg-control-hover',
                quiet: 'bg-transparent text-primary-text underline underline-offset-4 hover:bg-inset',
            },
        },
        defaultVariants: { variant: 'secondary' },
    },
);

export interface ButtonProps
    extends
        ButtonHTMLAttributes<HTMLButtonElement>,
        VariantProps<typeof buttonStyles> {}

/**
 * Renders a native button with the design system's action variants.
 *
 * @param props - Native button attributes and visual variant.
 * @returns A keyboard-accessible button.
 */
export function Button({
    variant,
    className,
    type = 'button',
    ...props
}: ButtonProps) {
    return (
        <button
            {...props}
            type={type}
            className={cn(buttonStyles({ variant }), className)}
        />
    );
}
