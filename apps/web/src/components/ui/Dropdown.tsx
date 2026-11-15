import { cva, type VariantProps } from 'class-variance-authority';
import {
    useCallback,
    useEffect,
    useId,
    useLayoutEffect,
    useRef,
    useState,
    type ReactNode,
} from 'react';

import { cn } from '../../utils/cn';
import { Button } from './Button';

const panelStyles = cva(
    'absolute left-0 top-full z-20 mt-2 max-h-96 overflow-y-auto rounded-lg bg-surface p-2 shadow-md',
    {
        variants: {
            panelWidth: {
                trigger: 'w-full',
                wide: 'w-full sm:w-96',
                menu: 'w-48',
            },
        },
        defaultVariants: { panelWidth: 'trigger' },
    },
);

export interface DropdownProps extends VariantProps<typeof panelStyles> {
    triggerLabel: string;
    trigger: ReactNode;
    children: (close: () => void) => ReactNode;
    disabled?: boolean;
    className?: string;
    alignment?: 'auto' | 'start' | 'end';
    triggerAppearance?: 'field' | 'icon';
}

export function Dropdown({
    triggerLabel,
    trigger,
    children,
    disabled = false,
    className,
    panelWidth,
    alignment = 'auto',
    triggerAppearance = 'field',
}: DropdownProps) {
    const [open, setOpen] = useState(false);
    const [restoreFocus, setRestoreFocus] = useState(false);
    const [openAbove, setOpenAbove] = useState(false);
    const [alignEnd, setAlignEnd] = useState(false);
    const [availableHeight, setAvailableHeight] = useState<number>();
    const [horizontalOffset, setHorizontalOffset] = useState(0);
    const panelId = useId();
    const containerRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLButtonElement>(null);
    const panelRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open && restoreFocus) {
            triggerRef.current?.focus();
        }
    }, [open, restoreFocus]);

    useLayoutEffect(() => {
        if (!open) {
            return;
        }

        function positionPanel(): void {
            const trigger = triggerRef.current;
            const panel = panelRef.current;

            if (!trigger || !panel) {
                return;
            }

            const bounds = trigger.getBoundingClientRect();
            const below = window.innerHeight - bounds.bottom - 16;
            const above = bounds.top - 16;
            const placeAbove = panel.scrollHeight > below && above > below;
            const panelWidth = panel.offsetWidth;
            const endAligned =
                alignment === 'end' ||
                (alignment === 'auto' &&
                    bounds.left + panelWidth > window.innerWidth - 8 &&
                    bounds.right - panelWidth >= 8);
            const alignedLeft = endAligned
                ? bounds.right - panelWidth
                : bounds.left;
            const fittedLeft = Math.min(
                Math.max(alignedLeft, 8),
                window.innerWidth - panelWidth - 8,
            );

            setOpenAbove(placeAbove);
            setAlignEnd(endAligned);
            setAvailableHeight(Math.max(0, placeAbove ? above : below));
            setHorizontalOffset(fittedLeft - alignedLeft);
        }

        positionPanel();
        window.addEventListener('resize', positionPanel);
        window.addEventListener('scroll', positionPanel, true);
        const observer =
            typeof ResizeObserver === 'undefined'
                ? undefined
                : new ResizeObserver(positionPanel);
        if (contentRef.current) {
            observer?.observe(contentRef.current);
        }

        return () => {
            window.removeEventListener('resize', positionPanel);
            window.removeEventListener('scroll', positionPanel, true);
            observer?.disconnect();
        };
    }, [alignment, open]);

    useEffect(() => {
        if (!open) {
            return;
        }

        function handlePointerDown(event: PointerEvent): void {
            if (
                event.target instanceof Node &&
                !containerRef.current?.contains(event.target)
            ) {
                setRestoreFocus(false);
                setOpen(false);
            }
        }

        function handleKeyDown(event: KeyboardEvent): void {
            if (event.key === 'Escape') {
                setRestoreFocus(false);
                setOpen(false);
                triggerRef.current?.focus();
            }
        }

        document.addEventListener('pointerdown', handlePointerDown);
        document.addEventListener('keydown', handleKeyDown);

        return () => {
            document.removeEventListener('pointerdown', handlePointerDown);
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [open]);

    const close = useCallback((): void => {
        setOpen(false);
        setRestoreFocus(true);
    }, []);

    return (
        <div
            ref={containerRef}
            onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget)) {
                    setOpen(false);
                }
            }}
            className={cn('relative w-full', className)}
        >
            <Button
                ref={triggerRef}
                variant="secondary"
                size={triggerAppearance === 'icon' ? 'small' : 'medium'}
                type="button"
                disabled={disabled}
                aria-label={triggerLabel}
                aria-expanded={open}
                aria-controls={open ? panelId : undefined}
                onClick={() => {
                    setRestoreFocus(false);
                    setHorizontalOffset(0);
                    setOpen((wasOpen) => !wasOpen);
                }}
                className={cn(
                    'w-full',
                    triggerAppearance === 'field'
                        ? 'justify-between gap-5 bg-surface shadow-sm ring-[0.5px] ring-control-hover/50 hover:bg-control-hover'
                        : cn(
                              'min-h-10 p-0 hover:bg-control-hover',
                              open ? 'bg-control-hover' : 'bg-transparent',
                          ),
                )}
            >
                {trigger}
            </Button>
            {open && (
                <div
                    id={panelId}
                    ref={panelRef}
                    style={{
                        maxHeight: availableHeight,
                        transform: `translateX(${horizontalOffset}px)`,
                    }}
                    className={cn(
                        panelStyles({ panelWidth }),
                        openAbove && 'bottom-full top-auto mb-2 mt-0',
                        alignEnd && 'left-auto right-0',
                    )}
                >
                    <div ref={contentRef}>{children(close)}</div>
                </div>
            )}
        </div>
    );
}
