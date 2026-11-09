import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';

import { App } from './App';

afterEach(() => {
    cleanup();
});

test('renders the home placeholder', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Enact' })).toBeInTheDocument();
});
