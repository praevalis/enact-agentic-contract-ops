import { useId } from 'react';

import { Input, type InputProps } from './Input';
import { InlineError } from './InlineError';

export interface FormFieldProps extends Omit<InputProps, 'invalid'> {
    label: string;
    hint?: string;
    error?: string;
}

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
        <div className="flex flex-col gap-1.5">
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
            {error && <InlineError id={errorId}>{error}</InlineError>}
        </div>
    );
}
