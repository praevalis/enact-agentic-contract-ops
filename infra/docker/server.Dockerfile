FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY apps/server/pyproject.toml apps/server/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package enact-server --no-install-workspace

COPY apps/server/src apps/server/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package enact-server

FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv
COPY apps/server/src apps/server/src
COPY apps/server/alembic.ini apps/server/alembic.ini
COPY apps/server/migrations apps/server/migrations

RUN useradd --create-home --uid 10001 enact
USER enact

EXPOSE 8000

CMD ["uvicorn", "--app-dir", "apps/server/src", "enact.main:app", "--host", "0.0.0.0", "--port", "8000"]
