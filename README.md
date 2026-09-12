# Enact

Enact is an agentic contract-to-operations compiler for B2B SaaS activations.

## Repository

- `apps/server` - FastAPI application, domain modules, and LangGraph workflows
- `apps/web` - React/Vite browser application
- `scripts` - repository automation entry points
- `fixtures` - reference and benchmark inputs and expected results
- `infra` - container and PostgreSQL bootstrap configuration
- `docs/context` - product, architecture, and execution context
- `docs/reference` - source reference material

## Prerequisites

- Python 3.13
- uv
- Node.js and pnpm
- Docker with Docker Compose

Copy `.env.example` to `.env` before starting the local stack.

```text
docker compose up --build
```
