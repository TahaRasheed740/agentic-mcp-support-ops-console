# Replay-Only Public Deployment

TraceDesk should be deployed publicly as a replay-only portfolio demo. Public
visitors can inspect the product, data model, retrieval, MCP tools, recorded
investigations, and evaluation reports without being able to spend Anthropic API
credits.

## Deployment Stance

Use this mode for public hosting:

- Recorded replays are public after they have been exported from real live runs.
- Knowledge search, support cases, MCP tool explorer, and evaluations are public.
- Live Claude investigations are disabled.
- `ANTHROPIC_API_KEY` is not configured in the hosted environment.
- `LIVE_INVESTIGATIONS_ENABLED` is set to `false`.

Live Claude investigations remain a local development capability only. They are
useful for recording new canonical replays and refreshing evaluation reports, but
they should not be exposed in the public deployment.

## Required Services

The hosted stack needs the same logical services as local Docker Compose:

| Service | Purpose |
| --- | --- |
| `web` | Next.js public UI. |
| `api` | FastAPI REST, health, sessions, cases, runtime capabilities, replays, evaluations. |
| `postgres` | Managed PostgreSQL with pgvector. |
| `knowledge-mcp` | Documentation and hybrid retrieval MCP tools. |
| `operations-mcp` | Synthetic integration, run, log, and incident MCP tools. |
| `support-mcp` | Synthetic support case, persona, and approval-tool MCP surface. |

## Production Environment

Use values like these for a public replay-only deployment:

```env
APP_ENV=production
LIVE_INVESTIGATIONS_ENABLED=false
ANTHROPIC_API_KEY=
SESSION_SECRET=<long-random-secret>
DATABASE_URL=<managed-postgres-url>
WEB_ORIGIN=https://<web-domain>
NEXT_PUBLIC_API_URL=https://<api-domain>
API_INTERNAL_URL=https://<api-domain>
```

Do not set `ANTHROPIC_API_KEY` in the public environment. The runtime endpoint
will report live investigations as unavailable, and the case detail page will
show a replay-only message instead of a Claude launch path.

## Health Checks

Use these endpoints for deployment health checks:

- API liveness: `/health/live`
- API readiness: `/health/ready`
- Web: `/`

The API container should run migrations, seed deterministic data when empty,
ingest knowledge documents when empty, and then start Uvicorn.

## Public Verification Checklist

After deployment, verify:

- `/` loads the support queue.
- `/replays` loads without live Claude access.
- Captured replay scenarios are listed only after real local investigations have been exported.
- A replay clearly states that playback does not call Claude.
- Replay controls can step through recorded investigation events when captured fixtures exist.
- `/knowledge` returns evidence results.
- `/tools` opens the MCP tool explorer.
- `/evaluations` shows the latest deterministic and model-judge report.
- A case detail page shows **Live Claude disabled** and links to recorded replays.
- `/api/v1/runtime` returns `live_investigations_enabled: false`.
- No `ANTHROPIC_API_KEY` is configured in the hosting provider.

## What This Means In Plain English

The public site is an interactive product demo, not a public AI service. Visitors
can see what the agent did through recorded investigations and reports, but they
cannot start new Claude runs using the maintainer's credentials.
