import { cva } from 'class-variance-authority';
import { useState } from 'react';
import type { InputHTMLAttributes, Ref } from 'react';
import { FiEye, FiEyeOff } from 'react-icons/fi';

import { cn } from '../../utils/cn';

const inputStyles = cva(
    'min-h-11 w-full rounded-lg bg-inset px-3 py-2.5 text-sm text-primary-text outline-none placeholder:text-secondary-text focus-visible:ring-2 focus-visible:ring-focus disabled:cursor-not-allowed disabled:opacity-60',
    {
        variants: {
            invalid: {
                true: 'ring-1 ring-status-danger',
                false: '',
            },
        },
        defaultVariants: { invalid: false },
    },
);

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    invalid?: boolean;
    ref?: Ref<HTMLInputElement>;
}

export function Input({
    invalid = false,
    className,
    type,
    disabled,
    ref,
    ...props
}: InputProps) {
    const [passwordVisible, setPasswordVisible] = useState(false);
    const isPassword = type === 'password';
    const VisibilityIcon = passwordVisible ? FiEyeOff : FiEye;

    const input = (
        <input
            {...props}
            ref={ref}
            type={isPassword && passwordVisible ? 'text' : type}
            disabled={disabled}
            aria-invalid={invalid || undefined}
            className={cn(
                inputStyles({ invalid }),
                isPassword && 'pr-16',
                className,
            )}
        />
    );

    if (!isPassword) {
        return input;
    }

    return (
        <div className="relative">
            {input}
            <button
                type="button"
                disabled={disabled}
                aria-label={passwordVisible ? 'Hide password' : 'Show password'}
                onClick={() => setPasswordVisible((visible) => !visible)}
                className="absolute inset-y-0 right-1 flex min-w-11 items-center justify-center rounded-md text-secondary-text hover:text-primary-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-not-allowed disabled:opacity-60"
            >
                <VisibilityIcon
                    className="size-5"
                    aria-hidden="true"
                    focusable="false"
                />
            </button>
        </div>
    );
}
