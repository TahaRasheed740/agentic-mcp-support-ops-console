FROM ghcr.io/astral-sh/uv:0.11.23 AS uv

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY services/api/pyproject.toml ./
COPY services/api/uv.lock ./
COPY services/api/alembic.ini ./
COPY services/api/migrations ./migrations
COPY services/api/src ./src
COPY knowledge ./knowledge
COPY output/pdf ./output/pdf

RUN uv sync --locked --no-dev --no-editable

EXPOSE 8000

CMD ["uvicorn", "tracedesk_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
