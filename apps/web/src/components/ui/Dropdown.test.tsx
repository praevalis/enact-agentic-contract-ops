import {
    act,
    cleanup,
    fireEvent,
    render,
    screen,
} from '@testing-library/react';
import { useState } from 'react';
import { afterEach, expect, test, vi } from 'vitest';

import { Dropdown } from './Dropdown';

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
});

test('repositions the panel when its content grows after opening', () => {
    const resizeCallbacks: (() => void)[] = [];

    class TestResizeObserver implements ResizeObserver {
        constructor(callback: ResizeObserverCallback) {
            resizeCallbacks.push(() => callback([], this));
        }

        observe(): void {}
        unobserve(): void {}
        disconnect(): void {}
    }

    vi.stubGlobal('ResizeObserver', TestResizeObserver);
    vi.stubGlobal('innerHeight', 600);
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
        top: 400,
        bottom: 444,
        left: 100,
        right: 200,
        width: 100,
        height: 44,
        x: 100,
        y: 400,
        toJSON: () => ({}),
    });

    function Example() {
        const [expanded, setExpanded] = useState(false);

        return (
            <>
                <button type="button" onClick={() => setExpanded(true)}>
                    Load options
                </button>
                <Dropdown triggerLabel="Choose" trigger="Choose">
                    {() => <p>{expanded ? 'Many options' : 'Loading'}</p>}
                </Dropdown>
            </>
        );
    }

    render(<Example />);
    const trigger = screen.getByRole('button', { name: 'Choose' });
    fireEvent.click(trigger);

    const panel = document.getElementById(
        trigger.getAttribute('aria-controls') ?? '',
    );
    expect(panel).not.toBeNull();
    if (!panel) {
        throw new Error('The dropdown panel did not open.');
    }

    expect(panel).not.toHaveClass('bottom-full');
    fireEvent.click(screen.getByRole('button', { name: 'Load options' }));
    Object.defineProperty(panel, 'scrollHeight', { value: 400 });
    act(() => resizeCallbacks[0]?.());

    expect(panel).toHaveClass('bottom-full');
    expect(panel).toHaveStyle({ maxHeight: '384px' });
});
