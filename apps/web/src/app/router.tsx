import { createBrowserRouter, Navigate } from 'react-router-dom';

import { OrganizationOverview } from '../features/auth/OrganizationOverview';
import { OrganizationSetup } from '../features/auth/OrganizationSetup';
import { Register } from '../features/auth/Register';
import { SessionBoundary } from '../features/auth/SessionBoundary';
import { SignIn } from '../features/auth/SignIn';

export const router = createBrowserRouter([
    {
        Component: SessionBoundary,
        children: [
            { path: '/organization', Component: OrganizationOverview },
            { path: '/sign-in', Component: SignIn },
            { path: '/register', Component: Register },
            { path: '/setup', Component: OrganizationSetup },
            { path: '*', element: <Navigate to="/sign-in" replace /> },
        ],
    },
]);
