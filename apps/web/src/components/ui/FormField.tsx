import { useId } from 'react';

import { Input, type InputProps } from './Input';

export interface FormFieldProps extends Omit<InputProps, 'invalid'> {
    label: string;
    hint?: string;
    error?: string;
}

/**
 * Associates a visible label, hint, and validation error with an input.
 *
 * @param props - Input attributes and field guidance.
 * @returns A labeled input with accessible descriptions.
 */
export function FormField({
    label,
    hint,
    error,
    id,
    ...props
}: FormFieldProps) {
    const generatedId = useId();
    const fieldId = id ?? generatedId;
    const hintId = hint ? `${fieldId}-hint` : undefined;
    const errorId = error ? `${fieldId}-error` : undefined;
    const describedBy = [props['aria-describedby'], hintId, errorId]
        .filter(Boolean)
        .join(' ');

    return (
        <div className="grid gap-1.5">
            <label htmlFor={fieldId} className="text-sm font-medium">
                {label}
            </label>
            <Input
                {...props}
                id={fieldId}
                invalid={Boolean(error)}
                aria-describedby={describedBy || undefined}
            />
            {hint && (
                <p id={hintId} className="text-xs text-secondary-text">
                    {hint}
                </p>
            )}
            {error && (
                <p
                    id={errorId}
                    role="alert"
                    className="text-sm text-status-danger"
                >
                    Error: {error}
                </p>
            )}
        </div>
    );
}
