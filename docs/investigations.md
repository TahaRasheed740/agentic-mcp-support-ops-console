# Claude-backed investigations

## Workflow

Live investigations use one router, bounded specialist lanes, and one final
general investigator/synthesizer. The specialists are now Claude-powered, but
they remain constrained by lane-specific read-only tool catalogs.

1. The Support MCP service supplies the case and effective session-overlay state.
2. The configurable router model returns a Pydantic classification and plan through
   the Anthropic SDK's structured-output interface.
3. TraceDesk routes relevant cases to documentation, account, and reliability
   specialists. Each specialist receives only its own read-only MCP tools, runs in
   parallel, and emits a structured specialist report.
4. The general investigator receives only read tools permitted by the router plan. TraceDesk
   removes authorization from model-visible schemas and injects trusted context at
   the MCP gateway.
5. Tool requests, results, model summaries, budgets, and evidence are committed to
   PostgreSQL as ordered events.
6. Knowledge results receive stable `E1`, `E2`, and subsequent citation IDs.
7. A final structured-output call receives captured evidence, specialist reports,
   and the investigation log, then produces findings, citations, proposed actions,
   and a drafted customer response.
8. TraceDesk rejects any finding or citation that references evidence not captured
   during that investigation.

The browser consumes persisted events with SSE. `Last-Event-ID` and the `after`
query parameter allow reconnection without making memory the source of truth.

## Safety and budgets

- Specialists can only call tools in their own lanes: documentation can search/read
  knowledge, account can inspect integration context, and reliability can inspect
  integrations, incidents, recent runs, and bounded logs. Support write tools are
  always removed from model-visible schemas.
- Model calls retry rate limits, connection failures, timeouts, and internal errors
  twice. Rate-limit retries use provider reset/retry headers when available, then
  fall back to `CLAUDE_RATE_LIMIT_RETRY_SECONDS`.
- Raw MCP results are captured for evidence, but model-visible tool results are
  compacted so live investigations fit lower development-tier rate limits.
- Each investigation is capped at four general investigator rounds, two specialist
  rounds per lane, thirty MCP calls, fixed output sizes, and 65,000 cumulative
  input, output, cache-read, and cache-creation tokens.
- Full evidence remains in PostgreSQL; synthesis receives bounded excerpts.
- Streamed text contains ordinary activity summaries. TraceDesk does not request or
  expose hidden chain-of-thought.

## Configuration

`CLAUDE_ROUTER_MODEL` and `CLAUDE_INVESTIGATOR_MODEL` configure roles instead of
embedding model IDs in workflow code. Local defaults use `claude-haiku-4-5` and
`claude-sonnet-4-5`. `ANTHROPIC_API_KEY` belongs only in `.env` or a secret store.

Hosted deployments should also set `LIVE_INVESTIGATION_ACCESS_CODE`. In
production, TraceDesk blocks live investigations when this code is absent or when
the launch request does not include the matching `X-TraceDesk-Live-Code` header.
Recorded replays do not need the code because they do not call Claude or spend
tokens.

## Current boundaries

- A process restart cancels an active in-process task, although persisted events
  remain durable.
- The default evaluation command does not call Claude. It grades benchmark
  behavior with fixed rules so CI remains inexpensive and reproducible. Optional
  model-based grading is available through `--model-judge` and should be run
  manually because it spends Anthropic tokens.
- Drafted responses and actions are recommendations until a human approves the
  queued write action.
