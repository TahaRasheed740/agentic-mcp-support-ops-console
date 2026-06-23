# ADR 0001: System foundation

## Status

Accepted for Iteration 0.

## Decision

TraceDesk uses an npm-workspace monorepo with a Next.js frontend, a Python
FastAPI backend, and PostgreSQL with pgvector. Docker Compose is the portable
runtime definition and will remain aligned with the eventual Railway services.

Readiness differs from liveness: `/health/live` proves the API process is
running, while `/health/ready` verifies its database dependency with `SELECT 1`.

## Consequences

The first increment has production-shaped service boundaries without adding
agent, retrieval, or MCP behavior before those features have testable data.

