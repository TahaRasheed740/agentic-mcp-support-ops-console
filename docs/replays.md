# TraceDesk Recorded Replays

Recorded replays are anonymous walkthroughs exported from completed live investigations. They are meant for public portfolio review when live Claude access is unavailable or intentionally disabled.

Replays do not call Claude, open SSE connections, or execute approval-gated MCP write tools. They reuse the same investigation workspace as live runs, but the UI labels the session as a replay and disables approval buttons.

The replay page includes playback controls for play, pause, restart, step forward,
step back, skip to end, and speed. The UI reveals the investigation progressively
as recorded events appear: classification, plan, tool calls, evidence, specialist
reports, diagnosis, and the approval queue.

Current status:

- No captured replay fixtures are currently shipped.
- Scripted or simulated replay scenarios should not be presented as recordings.
- Replays should be added only after a real local live investigation is run and exported.

Live investigations remain available locally when `LIVE_INVESTIGATIONS_ENABLED=true` and `ANTHROPIC_API_KEY` is configured. Public deployments should set `LIVE_INVESTIGATIONS_ENABLED=false` and should not configure `ANTHROPIC_API_KEY`. This lets the hosted project expose public replays without allowing visitors to spend the maintainer's Anthropic credits.

Live mode streams events from the FastAPI SSE endpoint and can execute support MCP write tools only after explicit human approval.
