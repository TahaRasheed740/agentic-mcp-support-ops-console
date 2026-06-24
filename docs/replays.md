# TraceDesk Recorded Replays

Recorded replays are anonymous, deterministic walkthroughs of completed investigations. They are meant for public portfolio review when live Claude access is unavailable or intentionally disabled.

Replays do not call Claude, open SSE connections, or execute approval-gated MCP write tools. They reuse the same investigation workspace as live runs, but the UI labels the session as a replay and disables approval buttons.

The replay page includes playback controls for play, pause, restart, step forward,
step back, and speed. The UI reveals the investigation progressively as recorded
events appear: classification, plan, tool calls, evidence, specialist reports,
diagnosis, and the approval queue.

The current canonical replays are:

- `eu-webhook-latency`: regional queue latency investigation with incident correlation and no-customer-action guidance.
- `webhook-secret-rotation`: webhook 401 failures after secret rotation, using auth documentation and run logs.
- `stripe-schema-mapping`: nested Stripe payload schema change causing empty mapped email fields.
- `salesforce-oauth-expiration`: Salesforce OAuth token lifecycle failure after reauthorization attempts.

Live investigations remain available locally when `LIVE_INVESTIGATIONS_ENABLED=true` and `ANTHROPIC_API_KEY` is configured. Public deployments should set `LIVE_INVESTIGATIONS_ENABLED=false` and should not configure `ANTHROPIC_API_KEY`. This lets the hosted project expose public replays without allowing visitors to spend the maintainer's Anthropic credits.

Live mode streams events from the FastAPI SSE endpoint and can execute support MCP write tools only after explicit human approval.
