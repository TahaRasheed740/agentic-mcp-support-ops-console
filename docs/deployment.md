# Replay-Only Public Deployment

TraceDesk should be deployed publicly as a replay-only portfolio demo. Public
visitors can inspect captured investigations without being able to spend
Anthropic API credits.

## Deployment Stance

Use this mode for public hosting:

- Recorded replays are public after they have been exported from real live runs.
- The hosted app is frontend-only and does not require the backend, database, or MCP services.
- Support cases, knowledge search, MCP tools, investigations, and evaluations show public-demo placeholders.
- Live Claude investigations are disabled.
- `ANTHROPIC_API_KEY` is not configured in the hosted environment.
- `NEXT_PUBLIC_PUBLIC_DEMO` is set to `true`.

Live Claude investigations remain a local development capability only. They are
useful for recording new canonical replays and refreshing evaluation reports, but
they should not be exposed in the public deployment.

## Public Vercel Deployment

The recommended public deployment is Vercel Hobby with only the Next.js web app
running. The GitHub repository still contains the complete full-stack system, but
the public link runs the safe presentation layer.

Use these Vercel settings:

- Import repository: `TahaRasheed740/agentic-mcp-support-ops-console`
- Root directory: `apps/web`
- Framework preset: Next.js
- Install command: `npm install`
- Build command: `npm run build`
- Environment variable: `NEXT_PUBLIC_PUBLIC_DEMO=true`
- Do not add `ANTHROPIC_API_KEY`
- Do not add database or MCP service variables

The checked-in `apps/web/vercel.json` mirrors these settings.

## Local Full-Stack Mode

Local Docker Compose remains the complete application:

- `web`: Next.js UI.
- `api`: FastAPI REST, health, sessions, cases, runtime capabilities, evaluations.
- `postgres`: PostgreSQL with pgvector.
- `knowledge-mcp`: Documentation and hybrid retrieval MCP tools.
- `operations-mcp`: Synthetic integration, run, log, and incident MCP tools.
- `support-mcp`: Synthetic support case, persona, and approval-tool MCP surface.

Leave `NEXT_PUBLIC_PUBLIC_DEMO` unset or set it to `false` locally. Configure
`ANTHROPIC_API_KEY` and `LIVE_INVESTIGATIONS_ENABLED=true` only when privately
running live Claude investigations.

## Public Verification Checklist

After deployment, verify:

- `/` loads the public replay demo landing page.
- `/replays` loads without live Claude access.
- Four captured replay scenarios are listed.
- A replay states that playback is read-only and does not spend API credits.
- Replay controls can step through recorded investigation events.
- `/knowledge`, `/tools`, `/investigations`, and `/evaluations` explain that those features belong to the full local stack.
- No `ANTHROPIC_API_KEY` is configured in the hosting provider.

## What This Means In Plain English

The public site is an interactive replay demo, not a public AI service. Visitors
can see what the agent did through recorded investigations, but they cannot start
new Claude runs using the maintainer's credentials. The complete backend and
agent system remain available in the repository and in local/private demos.
