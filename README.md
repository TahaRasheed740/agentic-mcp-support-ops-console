# TraceDesk

TraceDesk is an evidence-grounded support investigation workbench for Acme
Automations, a fictional API automation SaaS. The project is being delivered
as a sequence of independently reviewable iterations.

## Iteration 7

The current product increment includes:

- A Next.js support queue with filters, search, pagination, and case details.
- A FastAPI service with liveness and database-readiness endpoints.
- A deterministic Acme Automations dataset with organizations, users,
  integrations, telemetry, incidents, tickets, and support personas.
- Signed, resettable demo sessions with isolated overlay storage.
- A 40-source, versioned support corpus containing Markdown and generated PDF
  documents, including realistic superseded guidance.
- Fifteen hand-authored benchmark cases with required evidence, expected root
  causes, prohibited claims, permitted tools, and expected actions.
- Local BGE embeddings, PostgreSQL vector search, BM25 lexical search, and
  reciprocal-rank fusion exposed in an evidence-search workspace.
- Three official Python SDK MCP services for knowledge, operations, and support.
- Ten typed tools, three resources, three reusable prompts, scoped authorization,
  bounded client timeouts, and approval-gated idempotent support writes.
- An MCP tool explorer that displays schemas and executes tools without a model.
- Configurable Claude router and investigator roles with structured classification,
  read-only MCP tool loops, prompt caching, retries, and cumulative budgets.
- Persisted typed investigation events streamed to a live workspace over SSE.
- Evidence capture, resolvable citation validation, structured diagnosis, and a
  customer-safe drafted response.
- Parallel documentation, account, and reliability specialist reports with
  approval-gated proposed actions.
- Anonymous recorded replay mode for public demonstrations without Claude usage.
- Deterministic evaluation reports covering classification, evidence recall,
  citation validity, diagnosis acceptability, unauthorized-write prevention, and
  prompt-injection resistance.
- Playwright checks for replay and live investigation surfaces.
- PostgreSQL 17 with pgvector and versioned Alembic migrations.
- Docker Compose orchestration and health checks.
- Python and TypeScript linting, type checking, tests, and CI.

For a visual walkthrough of the entities, containers, MCP services, investigation
flow, approvals, and evaluation gates, start with
[the project flowcharts](docs/project-flowcharts.md).

For public hosting, TraceDesk is intended to run as a replay-only demo. See
[the replay-only deployment guide](docs/deployment.md).

## Prerequisites

- Docker Desktop with the Docker engine running.
- Docker Compose 2 or later.
- `uv` 0.11 or later for local Python development.

Node.js 22+ and Python 3.12 are needed only when running services outside
containers. Python dependencies are resolved and locked by `uv`.

## Start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). The page reports the API
and database status. Open [the evidence workspace](http://localhost:3000/knowledge)
to inspect retrieval results, or open
[the MCP tool explorer](http://localhost:3000/tools). The API is available on port `8001` because port `8000`
may already be used by another local project. Health endpoints are:

- `http://localhost:8001/health/live`
- `http://localhost:8001/health/ready`

Stop the stack with:

```powershell
docker compose down
```

## Local Checks

Install the locked API and frontend dependencies:

```powershell
uv sync --project services/api --group dev --locked
npm install
uv run --project services/api pytest services/api/tests
uv run --project services/api ruff check services/api
uv run --project services/api mypy --config-file services/api/pyproject.toml services/api/src
uv run --project services/api python -m tracedesk_api.evaluation
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e --workspace apps/web
```

## Configuration

Copy `.env.example` to `.env`. Development credentials are intentionally local
and must not be used in a hosted environment. Live investigations require
`LIVE_INVESTIGATIONS_ENABLED=true` and `ANTHROPIC_API_KEY` in the uncommitted
`.env` file. Hosted production deployments should set
`LIVE_INVESTIGATIONS_ENABLED=false` and should not configure `ANTHROPIC_API_KEY`.
Recorded replays stay public because they do not call Claude or spend tokens. The first knowledge ingestion downloads the public BGE
embedding model and stores it in a Docker volume for later starts.

## Deterministic Demo Data

The API container runs migrations and then seeds the database when it is empty.
To replace all canonical and session data with a fresh deterministic dataset:

```powershell
uv run --project services/api python -m tracedesk_api.seed --force --json
```

The seed contains 60 organizations, 240 users, 150 integrations, 6,000 job
runs, 9,000 log entries, 75 tickets, 10 incidents, four plans, and three
support personas. See [the dataset contract](docs/dataset.md) for details.

## Knowledge And Retrieval

The API container automatically ingests the knowledge corpus when its knowledge
tables are empty. Manual development commands are:

```powershell
uv run --project services/api python scripts/generate_knowledge.py
uv run --project services/api python -m tracedesk_api.knowledge_ingest --force
uv run --project services/api python -m tracedesk_api.retrieval_eval --mode hybrid --limit 8 --output reports/retrieval/latest.json
uv run --project services/api python -m tracedesk_api.evaluation
```

The benchmark requires every case's required sources to appear in the top eight
results for at least 90% of cases. The current report reaches 100% case success
and 100% required-source recall. See
[the retrieval design and dataset notes](docs/retrieval.md).

## Public API

- `GET /api/v1/domain/summary`
- `GET /api/v1/cases`
- `GET /api/v1/cases/{case_id}`
- `GET /api/v1/personas`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/current`
- `POST /api/v1/sessions/{session_id}/reset`
- `GET /api/v1/knowledge/search?q={query}&limit=8&mode=hybrid`
- `GET /api/v1/mcp/servers`
- `POST /api/v1/mcp/{service}/tools/{tool}`
- `GET /api/v1/runtime`
- `POST /api/v1/investigations`
- `GET /api/v1/investigations/{investigation_id}`
- `GET /api/v1/investigations/{investigation_id}/events`

## MCP Services

Docker exposes the private-style Streamable HTTP services locally for SDK and
Inspector demonstrations:

- Knowledge: `http://localhost:8101/mcp`
- Operations: `http://localhost:8102/mcp`
- Support: `http://localhost:8103/mcp`

Run the live transport and safety contract suite with:

```powershell
docker compose exec -T api python -m tracedesk_api.mcp_layer.contract_eval
```

See [the MCP architecture and tool contract](docs/mcp.md).

## Live Investigations

For local development, enable live mode with `LIVE_INVESTIGATIONS_ENABLED=true`
and set `ANTHROPIC_API_KEY`, then open a support case and select
**Investigate with Claude**. The router classifies and plans, Claude-powered
documentation, account, and reliability specialists run in bounded read-only
lanes, the investigator calls only read tools, and the browser reconnects to the
persisted event stream using SSE sequence IDs.

Public deployments should leave live mode disabled and use recorded replays
instead.

The hard limits are four investigator model rounds, two specialist rounds per lane,
thirty tool calls, fixed per-response output
limits, and 65,000 cumulative input, output, and cache tokens. See
[the investigation architecture](docs/investigations.md).

## Replays And Evaluation

Open [recorded replays](http://localhost:3000/replays) for an anonymous public
demo that does not call Claude or mutate support state. The canonical replay
demonstrates specialist reports, evidence citations, a drafted response, and a
pending approval action.

Run the deterministic evaluation suite with:

```powershell
uv run --project services/api python -m tracedesk_api.evaluation
```

Run optional Claude-as-judge grading manually when you want model-based review.
This spends Anthropic API tokens and is intentionally excluded from CI:

```powershell
uv run --project services/api python -m tracedesk_api.evaluation --model-judge --judge-limit 5
```

Reports are written to `reports/evaluations/latest.json` and
`reports/evaluations/latest.md`. See [the replay notes](docs/replays.md).
