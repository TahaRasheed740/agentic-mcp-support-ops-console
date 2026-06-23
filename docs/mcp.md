# MCP service layer

## Purpose

Iteration 3 places Acme Automations systems behind Model Context Protocol
boundaries before any language model is allowed to investigate them. The
support queue, case detail page, knowledge search, and tool explorer all use the
same MCP transports that the Iteration 4 agent will use.

The implementation uses the official Python SDK (`mcp` 1.28) with stateless
Streamable HTTP and structured Pydantic outputs.

## Services

| Service | Tools | Resource | Prompt |
| --- | --- | --- | --- |
| Knowledge | `search_knowledge`, `get_document` | `acme://knowledge/catalog` | `evidence_search_plan` |
| Operations | `get_integration`, `list_recent_runs`, `get_run_logs`, `list_incidents` | `acme://operations/status` | `reliability_investigation` |
| Support | `list_cases`, `get_case`, `update_ticket_status`, `add_internal_note` | `acme://support/queue-summary` | `case_triage` |

The API opens a fresh asynchronous SDK session per request, initializes the MCP
connection, injects trusted authorization context, and enforces an eight-second
deadline. Calls return a consistent envelope containing service, request ID,
timestamp, and idempotent-replay state.

## Authorization and writes

Every tool declares an `AuthorizationContext` in its input schema. Browser
clients cannot supply or replace it: the API removes any submitted
`authorization` field and derives the persona and session from the signed demo
cookie.

Read tools require a service-specific scope. The two write tools additionally
require a session, an action ID present in the trusted approval context, and an
idempotency key. Reusing the key with the same request returns the stored result;
reusing it with different arguments fails. Writes affect only `ticket_overlays`,
never the canonical synthetic ticket.

The explorer deliberately has no approved action IDs. It can demonstrate any
read tool, but every write attempt remains blocked. Iteration 5 will create and
resume real approval records from proposed agent actions.

## Contract gate

`tracedesk_api.mcp_layer.contract_eval` starts with a temporary demo session and
verifies all three transports, tool schemas, resources, prompts, representative
reads, scope denial, approval denial, replay behavior, idempotency conflicts,
typed failures, and the timeout boundary. Its temporary overlays and invocation
records are removed through the session's cascading delete.

## Current boundaries

- MCP services trust authorization injected by the private API network. They do
  not yet accept public clients or implement external OAuth. Public identity and
  deployment hardening belong to Iteration 8; exposing these ports publicly now
  would create security work for an interface intended only for the demo stack.
- Approval enforcement exists, but the explorer cannot mint approvals. That is
  intentional: Iteration 5 must bind approvals to proposed actions and human UI
  decisions before a user-facing approval token can safely exist.
- Each API call creates a short-lived MCP session. This keeps failure isolation
  simple for the current workload. Connection pooling is deferred until traces
  from Iteration 4 show that session setup is a meaningful latency cost.
