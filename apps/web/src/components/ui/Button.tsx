import { cva, type VariantProps } from 'class-variance-authority';
import type { ButtonHTMLAttributes, Ref } from 'react';

import { cn } from '../../utils/cn';

const buttonStyles = cva(
    'inline-flex items-center justify-center rounded-lg font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus disabled:cursor-not-allowed disabled:opacity-50',
    {
        variants: {
            variant: {
                primary: 'bg-amber text-night hover:bg-amber/90',
                secondary: 'bg-inset text-primary-text hover:bg-control-hover',
                raised: 'bg-surface text-primary-text shadow-sm ring-1 ring-control-hover hover:bg-control-hover',
                quiet: 'bg-transparent text-primary-text underline underline-offset-4 hover:bg-inset',
            },
            size: {
                small: 'min-h-9 px-3 py-1.5 text-xs',
                medium: 'min-h-11 px-4 py-2 text-sm',
                large: 'min-h-12 px-5 py-2.5 text-base',
            },
        },
        defaultVariants: { variant: 'secondary', size: 'medium' },
    },
);

export interface ButtonProps
    extends
        ButtonHTMLAttributes<HTMLButtonElement>,
        VariantProps<typeof buttonStyles> {
    ref?: Ref<HTMLButtonElement>;
}

export function Button({
    variant,
    size,
    className,
    type = 'button',
    ref,
    ...props
}: ButtonProps) {
    return (
        <button
            {...props}
            ref={ref}
            type={type}
            className={cn(buttonStyles({ variant, size }), className)}
        />
    );
}
