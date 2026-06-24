# TraceDesk Recorded Replays

Recorded replays are anonymous, deterministic walkthroughs of completed investigations. They are meant for public portfolio review when live Claude access is unavailable or intentionally protected.

Replays do not call Claude, open SSE connections, or execute approval-gated MCP write tools. They reuse the same investigation workspace as live runs, but the UI labels the session as a replay and disables approval buttons.

The current canonical replay is:

- `eu-webhook-latency`: a regional webhook latency investigation that demonstrates specialist reports, evidence citations, customer-safe diagnosis text, and a pending approval action.

Live investigations remain available from case detail pages when `ANTHROPIC_API_KEY` is configured. In production, live mode also requires `LIVE_INVESTIGATION_ACCESS_CODE`; otherwise the API refuses live investigations even if a key exists. This lets the hosted project expose public replays without allowing visitors to spend the maintainer's Anthropic credits.

Live mode streams events from the FastAPI SSE endpoint and can execute support MCP write tools only after explicit human approval.
