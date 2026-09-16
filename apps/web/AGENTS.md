# Enact Web Instructions

This file extends the repository-level `AGENTS.md` for work under `apps/web`.

## TypeScript

- Use strict TypeScript and current ES2022 language features.
- Add precise types at component, hook, function, state, and external-data boundaries.
- Do not use `any`. Use `unknown` for untrusted values and narrow it before use.
- Avoid broad assertions, non-null assertions, and unchecked casts. Prefer runtime validation or explicit control-flow narrowing.
- Keep `noUncheckedIndexedAccess` and `noImplicitOverride` violations resolved rather than suppressed.
- Allow inference for obvious local values. Add explicit types when they document a public contract or prevent widening.
- Use discriminated unions for finite UI states instead of combinations of loosely related booleans.
- Use `type` for unions, mapped types, and compositions. Use `interface` for object contracts intended to be implemented or extended.

## Formatting and linting

- ESLint is authoritative for linting and Prettier is authoritative for formatting.
- Use single quotes for JavaScript and TypeScript strings.
- Use four spaces for indentation. Do not use literal tab characters.
- Include trailing commas wherever the syntax permits them.
- Do not disable lint rules without a narrow, documented reason.
- Group imports in this order: third-party packages, application modules, relative modules, then side-effect imports such as styles.
- Use named exports for application components, hooks, utilities, and types.
- Do not introduce barrel files unless they provide a deliberate package boundary rather than merely shortening imports.

## React

- Use function components and hooks.
- Use PascalCase for component names and component filenames.
- Prefix custom hooks with `use`.
- Keep components focused on one responsibility.
- Favor composition over large configurable components and deeply nested conditionals.
- Keep render functions declarative. Move substantial state transitions, data orchestration, or reusable behavior into focused hooks or services.
- Do not use effects for derived state. Compute derived values during rendering unless synchronization with an external system is required.
- Do not add memoization pre-emptively. Use `useMemo`, `useCallback`, and `memo` only when referential stability is required or a measured performance problem exists.
- Keep state as close as practical to its consumers. Lift it only when multiple components genuinely share ownership.
- Do not copy server state into local component state without a concrete editing or synchronization requirement.
- Use error boundaries where a feature failure should be isolated from the rest of the application.

## Application organization

- Organize product code by feature rather than by technical category.
- Keep application composition, providers, routing, and global error handling under `src/app`.
- A feature may contain its own components, hooks, query definitions, view models, and tests.
- Reuse components from the shared component library instead of creating feature-local versions of the same component.
- Create a feature-specific component when the feature requires materially different behavior or design, not merely minor styling differences.
- Promote a feature component into the shared library only after a real reuse requirement establishes a stable shared interface.
- Keep domain behavior out of shared UI components.
- Do not create other shared abstractions until at least two concrete consumers establish the common behavior.
- Do not add speculative state-management libraries, component libraries, or styling frameworks.
- Preserve the static-client architecture. Do not add server-side routes, server actions, or a backend-for-frontend.

## API and server state

- Treat FastAPI as the authoritative owner of application data, validation, and operational mutations.
- Use the generated OpenAPI client for server communication.
- Never edit files under `src/api/generated` manually.
- Regenerate the client after an accepted API contract change and commit the updated generated output with that change.
- Do not duplicate generated request or response schemas with handwritten TypeScript types.
- Add feature-specific view models only when the UI representation materially differs from the API contract.
- Use TanStack Query for remote server state, caching, invalidation, and mutation lifecycle.
- Keep query keys centralized within the feature that owns them and make them deterministic.
- Invalidate or update cached data deliberately after mutations. Do not rely on incidental refetches.
- Handle loading, empty, error, stale, and success states explicitly.
- Use stable server error codes for programmatic behavior. Do not parse human-readable error messages.
- The configured API base URL ends at `/api`; requests must select the intended API version, such as `/v1`.
- Client-facing collection views should consume cursor-based pagination. Internal or administrative views may use offset-based pagination when provided by the API.

## Components and accessibility

- Use semantic HTML before adding ARIA attributes.
- Every interactive control must be keyboard accessible and have an accessible name.
- Associate form fields with visible labels and expose validation errors accessibly.
- Preserve focus intentionally across dialogs, navigation, validation failures, and asynchronous mutations.
- Do not communicate status using color alone.
- Ensure loading indicators and asynchronous status changes are available to assistive technology.
- Prefer accessible role, label, and text queries in tests because the same semantics benefit users.

## Forms and validation

- Keep authoritative business validation on the server.
- Client-side validation may provide immediate feedback but must not redefine server rules.
- Display field-level errors near their controls and case-level failures in an appropriate summary.
- Preserve user input after recoverable submission failures.
- Prevent duplicate submissions while a mutation is pending.
- Map structured server errors by stable error code and field location.

## Error handling

- Represent expected failures explicitly rather than swallowing rejected promises.
- User-facing errors should explain what happened and what the user can do next.
- Do not expose stack traces, internal identifiers, credentials, or raw upstream responses.
- Unexpected errors should reach the application's observability and error-boundary mechanisms.
- Empty catch blocks and unhandled floating promises are not allowed.

## Tests

- Use Vitest and Testing Library for component, hook, and feature tests.
- Test behavior from the user's perspective rather than component internals.
- Prefer accessible queries such as `getByRole`, `getByLabelText`, and `findByRole`.
- Keep tests colocated with the component or feature they cover.
- Name tests after observable behavior.
- Avoid snapshots for behavior that can be asserted semantically.
- Mock at external boundaries. Do not mock internal implementation details merely to simplify a test.
- Use Playwright for critical cross-feature and browser workflows.
- Cover loading, empty, failure, retry, authorization, and successful mutation states where applicable.
- Tests must be deterministic and must not depend on execution order or live external services.

## Generated and external files

- Do not modify generated API files manually.
- Do not commit build output, coverage output, or local environment files.
- Browser code must not contain server credentials, privileged database values, or secrets.
- Only expose environment variables intentionally prefixed for Vite client use.
- Treat uploaded contract content and rendered document data as untrusted.

## Web validation

Run targeted tests while iterating. Before declaring web work complete, run:

```text
pnpm --dir apps/web lint
pnpm --dir apps/web format:check
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
```

Run Playwright when routes, uploads, navigation, or complete user workflows change:

```text
pnpm --dir apps/web test:e2e
```

Run broader root checks when generated contracts, shared infrastructure, or cross-application behavior changes.
