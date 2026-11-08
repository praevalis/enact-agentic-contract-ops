import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { App } from './App';

test('renders the activation workspace placeholder', async () => {
    render(<App />);

    expect(
        await screen.findByRole('heading', { name: 'Enact' }),
    ).toBeInTheDocument();
});
