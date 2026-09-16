# Enact Repository Instructions

## Source of truth

Read the relevant canonical documents before planning or implementing work:

1. `docs/reference/enact-project-brief.md` defines the product thesis and scope.
2. `docs/context/prd.md` defines product requirements and acceptance criteria.
3. `docs/context/implementation-plan.md` defines the accepted technical direction.
4. `docs/context/execution-plan.md` is the authoritative work tracker.
5. `docs/context/reference-scenario.md` defines the Acme Cloud reference behavior.

Do not create parallel planning documents when a canonical document can be updated. Keep product decisions in the canonical documents rather than restating them here.

## Working agreement

- Work on one execution-plan task at a time unless the user explicitly groups tasks.
- Keep each task independently useful and suitable for a meaningful commit.
- Do not mark a task complete until its implementation and proportionate verification are complete.
- Update `docs/context/execution-plan.md` when completed work changes its recorded state or scope.
- Preserve unrelated user changes and avoid broad cleanup outside the active task.
- Do not create speculative modules, abstractions, directories, or infrastructure. Add them when a concrete slice requires them.
- Ask before making a choice that materially changes the accepted product or architecture. Record accepted changes in the appropriate canonical document.
- Do not commit changes unless the user asks for a commit.

## Repository boundaries

- `apps/server` contains the FastAPI application and is a member of the root uv workspace.
- `apps/web` contains the React/Vite static client and owns its pnpm configuration and lockfile.
- `infra` contains deployment, container, PostgreSQL bootstrap, and migration infrastructure.
- `scripts` contains repository automation, including artifact and OpenAPI client generation.
- `fixtures` contains deterministic development and evaluation inputs. Do not package fixtures into production images unless runtime behavior explicitly requires them.

The application is a modular monolith. A worker, additional deployable service, or multi-agent decomposition requires a concrete measured need and an accepted plan change.

## Tooling

- Use Python 3.13 and the root uv workspace for Python dependencies and commands.
- Run Python tools through `uv run`; do not create an independent dependency manager inside `apps/server`.
- Run pnpm commands against `apps/web`; do not turn the repository root into a pnpm workspace.
- Use root pre-commit hooks for repository-wide commit checks. Do not add Husky.
- Use `docker-compose.yml` for the local deployment topology.
- CI is manually dispatched unless the accepted plan changes that policy.
- Add current stable dependency versions deliberately and update lockfiles through their owning package manager.

## Architecture guardrails

- FastAPI is the sole owner of application data and operational mutations.
- Preserve domain-oriented boundaries and keep infrastructure concerns behind explicit interfaces.
- Prefer object-oriented, SOLID designs and dependency injection where they provide a real boundary; avoid abstractions without a current consumer.
- Keep model reasoning bounded by deterministic validation and governed execution.
- Do not allow an LLM to authorize or directly perform target-system mutations.
- Treat billing, entitlements, support, and onboarding as equally important contract domains. 
- Use asynchronous database and integration paths. PostgreSQL access uses SQLAlchemy with `asyncpg`.
- Preserve the scoped PostgreSQL roles `enact_owner`, `enact_migrate`, and `enact_app`.
- Tenant-owned data must use fail-closed row-level security. Application filtering is not a substitute for RLS.
- Uploaded documents must remain behind an S3-compatible object-storage boundary; MinIO is the local implementation.
- Keep API endpoints versioned under `/api/v1`. The web client's configured base URL stops at `/api` so callers choose the API version.

## Validation

Run checks proportionate to the files changed. The repository-wide baseline is:

```text
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
pnpm --dir apps/web lint
pnpm --dir apps/web format:check
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
pre-commit run --all-files
```

Use targeted checks during iteration, then run the relevant full application checks before declaring a task complete. Tests must cover tenant isolation and RLS whenever persistence behavior is introduced or changed.

Nested `AGENTS.md` files may add language- or application-specific instructions. They extend this file and must not contradict it.
