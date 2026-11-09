import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines conditional class names and resolves conflicting Tailwind utilities.
 *
 * @param inputs - Class names, conditional values, or class collections to combine.
 * @returns A class string with conflicting Tailwind utilities resolved.
 */
export function cn(...inputs: ClassValue[]): string {
    return twMerge(clsx(inputs));
}
