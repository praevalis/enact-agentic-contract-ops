# Enact Server Instructions

This file extends the repository-level `AGENTS.md` for work under `apps/server`.

## Python

- Target Python 3.13 exclusively. Use current Python syntax and standard-library capabilities rather than compatibility patterns for older versions.
- Use PEP 695 type parameter syntax for generic classes, functions, and type aliases instead of declaring `TypeVar` objects solely for those generics.
- Do not add `from __future__ import annotations`. Write annotations that work on the Python 3.13 runtime, using quoted forward references only when required.
- Add precise type hints to function and method parameters, return values, attributes, and meaningful local variables.
- Avoid `Any`, unparameterized containers, and overly generic types. Use them only when a precise alternative would add disproportionate complexity, and keep their scope narrow.
- Code must satisfy Pyright in strict mode.
- Do not use `# type:` directives merely to silence type-checker warnings. Fix the underlying typing or design issue whenever practical.
- When a root-cause fix is impossible or disproportionately complex, narrowly scope the directive and add a concise one- or two-line explanation of why the suppression is necessary.

## Style and documentation

- Ruff is authoritative for linting, import sorting, and formatting.
- Use single quotes and a maximum line length of 100 characters.
- Use Google-style docstrings.
- Every public method must have a complete docstring with `Args`, `Returns`, and `Raises` sections whenever those sections apply.
- Private methods may use a one-line descriptive docstring. Use a complete Google-style docstring when their behavior, invariants, side effects, or failure modes need explanation.
- Document meaningful exceptions in `Raises`; do not list exceptions that cannot escape the method.

## Imports

- Import in this order: standard library, third-party packages, then local application packages. Ruff `I` rules enforce grouping and sorting.
- Use relative imports within the same package.
- Use absolute imports when importing across packages.
- Do not use wildcard imports.

## Design

- Use object-oriented design and SOLID principles where they create clear, testable boundaries.
- Favor composition over inheritance.
- Keep classes focused on one responsibility.
- Apply dependency inversion through typed `Protocol` interfaces.
- Use `Protocol` for interfaces; do not use `ABC` or abstract base classes for interface definitions.
- Avoid marker interfaces, pass-through service classes, and abstractions with only one speculative consumer.

## Schemas and errors

- Name API and application schemas by entity and operation: `XxxCreate`, `XxxRead`, and `XxxUpdate`.
- Use the entity name in place of `Xxx`; do not introduce competing suffixes such as `Response`, `Input`, or `Patch` when one of the standard names expresses the role.
- Application exceptions must carry both a human-readable `message` and a stable machine-readable `code`.
- Exception codes are part of the programmatic contract. Keep them deterministic and do not derive them from message text.

## Queries and pagination

- Use cursor-based pagination for client-facing collection queries.
- Use offset-based pagination for internal or administrative collection queries.
- A feature-specific requirement may override these defaults when the reason is documented.
- Keep pagination ordering deterministic and define a stable tie-breaker.

## Database migrations

- Name Alembic migration revisions with a monotonically increasing four-digit prefix and a concise description, for example `0001_initial` or `0002_add_embeddings`.
- Keep each migration focused on one coherent schema change.
- Alembic migration files must pass the same Ruff lint and format rules as application code.
- Follow the repository rules for ownership, scoped roles, grants, default privileges, and row-level security.
- Include a valid downgrade unless the accepted task explicitly documents why reversal is unsafe or impossible.

## Tests

- Mark every test with `@pytest.mark.unit` or `@pytest.mark.integration`.
- Prefer applying the marker to the test class so all tests in the class inherit it.
- Organize related tests in classes so class-level markers and fixtures can be shared.
- Use one test class to cover one production class. Do not create a separate test class for each method.
- Group function-level or integration behavior by cohesive feature or scenario rather than creating artificial one-test classes.
- Keep tests fully typed and subject to the same lint and format rules as production code.

## Server validation

Run the relevant targeted tests while iterating. Before declaring server work complete, run:

```text
uv run ruff check apps/server
uv run ruff format --check apps/server
uv run pyright
uv run pytest apps/server/tests
```

Run broader root checks when shared configuration, infrastructure, generated contracts, or cross-application behavior changes.
